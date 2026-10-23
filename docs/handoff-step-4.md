# Step 4 — Handoff: LLM analyzer (/api/analyze) with local Ollama

Status: ✅ done, committed. Next: Step 5 (floating chat drawer with /api/chat).

## What was built

- **Ollama installed & serving** on this machine (`winget install Ollama.Ollama`,
  v0.40.9, port 11434, `qwen2.5:3b` pulled). The `run.bat` block that installs it
  existed already — it now matches reality end-to-end.
- `backend/app/summary.py` — PRD 3.3 `ClinicalSummary` as Pydantic v2 models with
  hostile-LLM guards: every list field coerces str/None/dict-before-list into a
  proper `list[str]` (`coerce_string_list`), medication dicts merge into
  `medications`, hallucinated empty med names are dropped.
- `backend/app/analyzer.py` — `Analyzer` interface + `OllamaAnalyzer`: one OpenAI
  client (`openai` pkg) at `LLM_BASE_URL` serving both this endpoint and Step 5's
  chat. Request: `response_format=json_object`, `temperature=0`, timeout
  `LLM_TIMEOUT_S` (180 s). A strict system prompt enforces "never invent clinical
  facts", positives/negatives split, medications in both `medications` and
  `plan.prescriptions`. Parse-failure → one retry → `AnalyzerError`.
- `POST /api/analyze` — body `{"transcript": "..."}`; 400 invalid JSON/empty
  transcript, 422 missing field, 503 LLM failure (all in the PRD error contract).
  Response: validated summary JSON directly.
- Frontend: the existing Step-1 CTA handler now hits the real endpoint and
  `setState({ summary })`; SummaryCard renders sections. **Added the missing PRD
  2.4 processing state**: CTA switches to spinner + "Analysing…" + disabled while
  the request runs (`.btn--busy .spinner` CSS).
- `.env.example` grew `WHISPER_CPU_THREADS`, `WHISPER_BEAM_SIZE`, `LLM_TIMEOUT_S`.

## How to run it right now

```
run.bat   # starts Ollama (install if missing) + backend + frontend
```
Record a consultation (or use the demo toggle to see a pre-made summary), stop,
click **Process Transcript with AI** → the summary card fills section by section.

## How it was verified (all green)

- 17 backend tests (incl. analyze contract, 400/422/503 shapes, unreachable-LLM
  503 against a dead port, "the response contains only PRD keys").
- `docs/smoke_analyze.py` — REAL `qwen2.5:3b` inference on the transcribed
  fixture consult → 200 in ~9 s, schema re-validated client side; meds
  populated, HPI aggravators correct, anaphylaxis-free hallucinated fields
  skipped.
- `docs/verify_step4_analyze.py` — full pipeline Playwright E2E: fake mic →
  chunks transcribed → uploader drains → Stop → CTA shows "Analysing…" with
  spinner + disabled → clinical summary textarea filled + 7 summary sections
  with bullets; screenshot `docs/step4-summary.png`.
- Regression: `verify_step2_recorder.py` + `verify_step3_transcribe.py` + step-3
  suite all pass; `tsc -b`, `vite build` clean.

## Known gaps (planned, not bugs)

- Chat drawer is Step 5; the same Analyzer client instance is reusable there.
- The clinical summary textarea is editable; edits stay local
  (`summaryEditedText`) — Copy to Prescription consumes it.

## Gotchas for the next session

- First analyze after a cold boot can take ~15 s while Ollama loads the model
  into RAM (subsequent requests ~5–12 s on this CPU).
- `qwen2.5:3b` still occasionally drifts on schema — the Pydantic coercion layer
  absorbs str↔list↔dict wobble; if a 503 repeats, check the log lines
  `LLM output did not validate (attempt N)`.
- The summary JSON replaces the whole `summary` in the store; per-section
  incremental streaming is NOT part of the PRD.
