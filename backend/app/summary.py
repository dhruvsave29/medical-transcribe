"""ClinicalSummary Pydantic models — exact mirror of PRD 3.3.

Never invent clinical facts: everything the transcript did not state stays
null / empty list (PRD 3.4). Every LLM response is validated before it
reaches the UI.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


def coerce_string_list(value: Any) -> list[str]:
    """LLMs wobble between str / list / None / nested-dicts for list fields."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if item is None:
                continue
            if isinstance(item, dict):
                # {'name': 'Aspirin', 'dosage': '75 mg'} -> 'Aspirin (75 mg)'
                name = str(item.get("name") or "").strip()
                extra = str(item.get("dosage") or "").strip()
                out.append(f"{name} ({extra})" if name and extra else name)
            else:
                out.append(str(item).strip())
        return [x for x in out if x]
    return []


class Patient(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = None
    age: str | None = None
    sex: str | None = None
    identifiers: list[str] = []

    @field_validator("identifiers", mode="before")
    @classmethod
    def _identifiers(cls, v: Any) -> Any:
        return coerce_string_list(v)


class HistoryOfPresentIllness(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    onset: str | None = None
    duration: str | None = None
    progression: str | None = None
    aggravating_factors: list[str] = []
    relieving_factors: list[str] = []

    @field_validator("aggravating_factors", "relieving_factors", mode="before")
    @classmethod
    def _factors(cls, v: Any) -> Any:
        return coerce_string_list(v)


class Symptoms(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    positive: list[str] = []
    negative: list[str] = []

    @field_validator("positive", "negative", mode="before")
    @classmethod
    def _posneg(cls, v: Any) -> Any:
        return coerce_string_list(v)


class PastMedicalHistory(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    conditions: list[str] = []
    surgeries: list[str] = []
    hospitalisations: list[str] = []

    @field_validator("conditions", "surgeries", "hospitalisations", mode="before")
    @classmethod
    def _history(cls, v: Any) -> Any:
        return coerce_string_list(v)


class Medication(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str
    dosage: str | None = None
    adherence: str | None = None


class ClinicalObservations(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    vitals: list[str] = []
    examination_findings: list[str] = []

    @field_validator("vitals", "examination_findings", mode="before")
    @classmethod
    def _observations(cls, v: Any) -> Any:
        return coerce_string_list(v)


class Assessment(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    provisional_diagnosis: str | None = None
    differentials: list[str] = []

    @field_validator("differentials", mode="before")
    @classmethod
    def _differentiials(cls, v: Any) -> Any:
        return coerce_string_list(v)


class Plan(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    investigations: list[str] = []
    prescriptions: list[str] = []
    advice: list[str] = []
    follow_up: str | None = None

    @field_validator("investigations", "prescriptions", "advice", mode="before")
    @classmethod
    def _plan_lists(cls, v: Any) -> Any:
        return coerce_string_list(v)


class ClinicalSummary(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    patient: Patient = Patient()
    chief_complaints: list[str] = []
    history_of_present_illness: HistoryOfPresentIllness = HistoryOfPresentIllness()
    symptoms: Symptoms = Symptoms()
    past_medical_history: PastMedicalHistory = PastMedicalHistory()
    medications: list[Medication] = []
    allergies: list[str] = []
    clinical_observations: ClinicalObservations = ClinicalObservations()
    assessment: Assessment = Assessment()
    plan: Plan = Plan()
    clinical_summary: str

    @field_validator(
        "chief_complaints", "allergies", mode="before"
    )
    @classmethod
    def _top_lists(cls, v: Any) -> Any:
        return coerce_string_list(v)

    @field_validator("medications", mode="before")
    @classmethod
    def _medications(cls, v: Any) -> Any:
        # Accept both [{'name': ..}] and flat strings.
        if isinstance(v, list):
            meds = []
            for item in v:
                if isinstance(item, dict):
                    meds.append(item)
                else:
                    try:
                        meds.append(json.loads(str(item)))
                    except Exception:
                        meds.append({"name": str(item)})
            return meds
        return coerce_string_list(v)

    @model_validator(mode="after")
    def _no_hallucinated_meds(self) -> "ClinicalSummary":
        # PRD guard: medication names must never be empty strings.
        self.medications = [m for m in self.medications if m.name.strip()]
        return self

    @field_validator("clinical_summary", mode="before")
    @classmethod
    def _paragraph(cls, v: Any) -> Any:
        # clinical_summary may come back as a list -> join sentences.
        if isinstance(v, list):
            return " ".join(str(x) for x in coerce_string_list(v))
        return v
