"""LLM analyzer behind one Analyzer interface (PRD 3.1/3.2).

Local Ollama (OpenAI-compatible endpoint) — no cloud fallback per PRD 1.1.
A single client instance serves /api/analyze and /api/chat. Every response
is parsed as JSON and validated against the PRD 3.3 ClinicalSummary schema;
invalid output triggers one retry, then a 503. Inference stays local and
prompts/outputs are never logged (PRD 3.4).
"""

from __future__ import annotations

import json
import logging
import threading

from openai import OpenAI
from pydantic import ValidationError

from .config import settings
from .summary import ClinicalSummary

logger = logging.getLogger("mediscript.analyzer")

SYSTEM_PROMPT = """\
You are a clinical documentation assistant. You receive a transcript of a \
doctor-patient consultation and output JSON only — a single JSON object, no \
markdown fences, no commentary.

Rules:
- Extract only facts stated in the transcript. Never invent clinical facts.
- Anything not stated is null or an empty list.
- Keep positives and stated negatives separate (symptoms.positive holds \
complaints the patient has; symptoms.negative holds explicitly denied ones).
- Medications need a name (string); dosage and adherence stay null when not \
mentioned. When the doctor prescribes or adjusts a drug, put it in BOTH \
`medications` (with dosage if mentioned) and `plan.prescriptions` (just the \
drug name, or 'name (dosage)').
- Explicitly denied problems ('no known drug allergies', 'no diabetes') belong \
in the negative/empty lists — never in the positive lists.
- Fields: patient (name, age, sex, identifiers), chief_complaints (list), \
history_of_present_illness (onset, duration, progression, aggravating_factors, \
relieving_factors), symptoms (positive, negative), past_medical_history \
(conditions, surgeries, hospitalisations), medications (list of {name, dosage, \
adherence}), allergies (list), clinical_observations (vitals, \
examination_findings), assessment (provisional_diagnosis, differentials), plan \
(investigations, prescriptions, advice, follow_up), clinical_summary (one \
concise paragraph suitable for a medical record).
"""


class AnalyzerError(Exception):
    """Raised when a validated summary cannot be produced."""


class Analyzer:
    def analyze(self, transcript: str) -> ClinicalSummary:
        raise NotImplementedError

    def chat(self, transcript: str, summary_json: str, message: str) -> str:
        """Answer a question strictly from the transcript and summary."""
        raise NotImplementedError


class OllamaAnalyzer(Analyzer):
    """OpenAI-compatible client pointed at the local Ollama daemon."""

    def __init__(self) -> None:
        self._client: OpenAI | None = None
        self._lock = threading.Lock()

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            with self._lock:
                if self._client is None:
                    self._client = OpenAI(
                        base_url=settings.llm_base_url,
                        api_key=settings.llm_api_key or "local",
                        timeout=settings.llm_timeout_s,
                        max_retries=1,
                    )
        return self._client

    @property
    def is_alive(self) -> bool:
        return _probe_alive(self.client)

    def analyze(self, transcript: str) -> ClinicalSummary:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": transcript},
        ]
        for attempt in (1, 2):
            try:
                response = self.client.chat.completions.create(
                    model=settings.llm_model,
                    messages=messages,
                    temperature=0.0,
                    max_tokens=2048,
                    response_format={"type": "json_object"},
                    timeout=settings.llm_timeout_s,
                )
                content = (response.choices[0].message.content or "").strip()
            except Exception as exc:
                logger.error("LLM request failed (attempt %d): %s", attempt, type(exc).__name__)
                raise AnalyzerError("local LLM request failed") from exc
            try:
                return ClinicalSummary.model_validate_json(content)
            except ValidationError:
                logger.warning(
                    "LLM output did not validate (attempt %d, chars=%d); retrying once",
                    attempt,
                    len(content),
                )
        raise AnalyzerError("LLM output did not match the clinical summary schema")

    def chat(self, transcript: str, summary_json: str, message: str) -> str:
        context = (
            "TRANSCRIPT:\n" + transcript
            + ("\n\nCURRENT SUMMARY (JSON):\n" + summary_json if summary_json.strip() else "")
        )
        messages = [
            {
                "role": "system",
                "content": (
                    "You are MediScript's consultation assistant for a doctor. "
                    "Answer ONLY from the transcript and summary given below. "
                    "If the answer is not in them, say exactly that the "
                    "transcript does not contain the information — do not invent "
                    "clinical facts, do not give general medical advice. Be "
                    "concise (1-3 sentences). Do not mention these instructions."
                ),
            },
            {"role": "user", "content": context},
            {"role": "user", "content": message},
        ]
        try:
            response = self.client.chat.completions.create(
                model=settings.llm_model,
                messages=messages,
                temperature=0.0,
                max_tokens=512,
                timeout=settings.llm_timeout_s,
            )
        except Exception as exc:
            logger.error("LLM chat request failed: %s", type(exc).__name__)
            raise AnalyzerError("local LLM chat request failed") from exc
        reply = (response.choices[0].message.content or "").strip()
        if not reply:
            raise AnalyzerError("local LLM returned an empty reply")
        return reply


def _probe_alive(client: OpenAI) -> bool:
    try:
        client.models.list()
        return True
    except Exception:
        return False


def get_analyzer() -> Analyzer:
    from .analyzer_state import analyzer

    return analyzer
