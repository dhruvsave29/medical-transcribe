# AGENTS.md — Shared Context for Every Agent Session

This file republishes PRD sections 1–3 (product, UI, shared contracts). Read it fully
before touching code. Current build progress lives in `/docs/handoff-step-*.md`.

The complete PRD: `PRD_Live_Medical_Transcription_Local_Ollama_Updated.docx`
(copy lives in repo Downloads source; sections 1–3 are authoritative below).

---

# PRD (validated): Live Medical Transcription & AI Clinical Summary
Prepared October 23, 2026 · Build plan in 6 agent-ready steps

## 1. Product Overview

What it is: A web application that listens to a doctor–patient consultation through the
microphone, filters out silence and noise with Voice Activity Detection (VAD), converts
speech to text with an ASR model (OpenAI Whisper), shows the transcript live, and, when the
session ends, sends the full transcript to an LLM that extracts structured medical
information and produces a concise clinical summary suitable for a medical record.

Core flow (7 requirements from the assignment):
- Capture live audio from the microphone.
- Detect speech segments with VAD so silence and background noise never reach the recogniser.
- Convert speech to text with an ASR model such as OpenAI Whisper.
- Display the transcript on screen as it is produced.
- On session completion, send the full transcript to an LLM.
- Extract structured medical information from the transcript.
- Generate a concise, structured clinical summary.

Required tech stack:
- Python for the backend and AI integration.
- JavaScript/TypeScript for the frontend.
- HTML5 and CSS3 for markup and styling.
- Frontend skills to demonstrate: responsive UI design, API integration, state management.

Who uses it: A doctor or clinic assistant during a consultation. The doctor speaks
naturally, watches the transcript appear, clicks one button to generate the summary, and
copies the result into a prescription or record.

### 1.1 Autonomous Build Mode (opencode CLI)

Goal: after the 6 steps, one command starts a fully working app. Nothing is left to code,
configure or fix by hand.

Zero required manual configuration: run.sh (Linux/macOS) or run.bat (Windows) creates .env
from .env.example when missing, installs project dependencies, ensures Ollama is installed
and running where supported, pulls the configured local model, downloads the Whisper/VAD
assets, and starts both servers. No cloud LLM account or API key is required. If the
operating system blocks an installer or requires administrator approval, the script must
stop with a precise, copy-pasteable recovery command and document this as an environment
limitation — not silently continue with a broken app.

Locked decisions (the agent never chooses between options):
- Frontend: React + TypeScript + Vite + Zustand, plain CSS with variables. Runs on port
  5173. The Vite dev server proxies /api to the backend, so no CORS setup is needed in
  development.
- Backend: Python 3.11+, FastAPI, Uvicorn, Pydantic v2, inside a .venv that the run script
  creates. Runs on port 8000.
- ASR: faster-whisper with the small.en model on CPU (int8). The model downloads
  automatically on first backend start and needs no API key. Set WHISPER_MODEL=small for
  non-English speech.
- VAD: @ricky0123/vad-web (Silero) in the browser, with its model and WASM files copied
  locally by Vite so it works without a CDN.
- LLM: local Ollama by default, using the OpenAI-compatible endpoint at
  http://127.0.0.1:11434/v1, model qwen2.5:3b (configurable with LLM_BASE_URL and
  LLM_MODEL). LLM_API_KEY is optional and defaults to a harmless local placeholder only if
  the client library requires a value. One client serves both /api/analyze and /api/chat.
  All analysis and chat inference stays on the user's machine; no cloud LLM fallback is
  allowed.
- Not used: Docker, a database, login, cloud LLM services, or external analytics. The LLM
  and Whisper run locally. Internet access may be needed once to install dependencies and
  download model assets; normal inference is local.

Definition of done for every step (the agent does all of this itself):
- Install the dependencies, start the servers and exercise the feature for real: curl for
  APIs, Playwright or a browser for the UI.
- Fix every error and warning found. Finish only when every acceptance criterion passes.
- Leave no TODOs, stubs, placeholder text or fake data in shipped code. Mock data lives
  only behind the dev toggle from Step 1.
- No dead buttons: every control in Section 2 must work by the end of Step 5.
- Commit to git at the end of each step so a bad step can be rolled back.
- Write the hand-off note with the exact command that runs the app as it stands.

## 2. UI Description

### 2.1 Overall layout and visual style
- A single-page app with a thin top bar (the hospital or demo name appears at the top right
  in the accent colour) and a large white rounded container below it.
- Two equal-width cards side by side: the left card is Live Medical Transcription (input
  side), the right card is AI Medical Summary (output side). On narrow screens they stack
  vertically, transcription first.
- Very light grey-blue page background, white cards with large corner radius (about 24px)
  and a soft shadow. Generous padding and spacing.
- One accent colour: indigo/periwinkle (about #6366F1) for card titles, the primary buttons
  and icons. Semantic colours for secondary actions: red for Stop, green for Save, neutral
  grey for Clear.
- Typography: a clean geometric sans-serif (Inter or Plus Jakarta Sans). Card titles are
  bold and accent-coloured with a leading icon. Section labels in the summary are small,
  uppercase, letter-spaced, grey-blue, each with a tiny icon on the left and a thin divider
  line running to the right edge.
- Rounded pill shapes for all buttons and stat chips. Empty states use light grey, centred
  text.

### 2.2 Left card: Live Medical Transcription
- Title row: microphone icon + "Live Medical Transcription" in the accent colour.
- Control row (four pill buttons):
  - Start Mic: filled indigo, white text, microphone icon. Primary action.
  - Stop: white with red outline and red text, red square icon.
  - Clear: white with grey outline, trash icon.
  - Save Recording: white with green outline and green text, download icon.
- Stat chips: two small outlined pills, "WORDS: 0" and "CHUNKS: 0" (chunks = number of
  speech segments VAD has sent to the recogniser). They update live.
- Live caption strip: a short, slightly elevated rounded box under the chips. It shows the
  in-progress/interim state (for example "Listening…" or the segment currently being
  transcribed) so the user knows the system is alive between chunks.
- Transcript area: a large rounded box with soft grey fill. Before recording it shows the
  placeholder "Ready — click Start Mic and speak naturally. VAD will auto-chunk your
  speech." with a small magic-wand icon. Once recording starts, each recognised chunk is
  appended here and the box auto-scrolls.
- Primary CTA at the bottom: a full-width indigo button with a lightning icon, "Process
  Transcript with AI". It sends the transcript to the LLM.

### 2.3 Right card: AI Medical Summary
- Title row: hourglass icon + "AI Medical Summary" in the accent colour, with an outlined
  "✕ Clear" button aligned to the top right of the card.
- Patient header: "Patient Name: …" in bold, then "Age: … Gender: …" in a lighter grey
  beneath, followed by a thin divider. (Values come from the extracted patient details;
  neutral placeholder until then.)
- Scrollable body with a thin custom scrollbar. It contains these sections in order, each
  with an icon, an uppercase label and a divider:
  - Clinical Summary: a resizable textarea (visible resize handle) with the placeholder
    "AI-generated clinical summary will appear here…". It is editable so the doctor can
    correct the text.
  - Chief Complaints: empty state "No complaints extracted yet".
  - Symptoms: empty state "No symptoms extracted yet".
  - Clinical Impression: empty state "No diagnosis inferred".
  - Medications: empty state "No medications extracted yet".
  - Examinations & Tests: empty state "No examinations extracted yet".
  - Allergies: empty state "No allergies extracted yet".
  - Past Medical History: empty state "No past medical history extracted".
  - History & Follow-up: history of present illness and the follow-up plan.
- Sticky footer button: a full-width indigo "Copy to Prescription" button that stays
  visible at the bottom of the card while the body scrolls.
- Floating action button: a round indigo chat-bubble button fixed at the bottom-right of
  the screen (opens a working chat drawer, built in Step 5).

### 2.4 UX behaviour and states
- Idle: all counters at 0, placeholder text in the transcript, empty states in every
  summary section, "Process Transcript with AI" disabled.
- Recording: Start Mic becomes disabled (or shows a pulsing recording state), Stop becomes
  active, the live strip shows "Listening…" and switches to "Transcribing…" when VAD closes
  a segment. WORDS and CHUNKS increment as text arrives.
- Stopped: the mic is released, the transcript remains editable, and "Process Transcript
  with AI" is enabled.
- Processing: the CTA shows a spinner and "Analysing…", the summary card shows skeleton
  shimmer in each section.
- Done: every section fills in. Sections the transcript did not cover keep their
  empty-state text rather than showing invented content.
- Errors: inline toast messages for microphone permission denied, backend unreachable, or
  LLM failure, each with a retry option.
- Clear: left Clear wipes transcript and counters (after a quick confirm if text exists).
  Right Clear wipes the summary only.
- Save Recording: downloads the captured audio (WAV) and, optionally, the transcript text.
- Copy to Prescription: copies a clean, formatted plain-text version of the summary to the
  clipboard and confirms with a toast ("Copied").

## 3. Shared Contracts (every agent must follow these)

### 3.1 Recommended architecture
- Frontend: React + TypeScript + Vite, with Zustand for state, plain CSS with CSS variables
  for the design tokens. HTML5 semantic markup.
- Browser audio + VAD: getUserMedia + AudioWorklet, with client-side Silero VAD
  (@ricky0123/vad-web). Each detected speech segment is encoded as 16 kHz mono WAV and sent
  to the backend. This is what makes the "CHUNKS" counter meaningful and keeps silence off
  the network.
- Backend: Python 3.11+, FastAPI, Pydantic v2, Uvicorn.
- ASR: OpenAI Whisper through faster-whisper running locally, behind one Transcriber
  interface so it can be swapped.
- LLM: local Ollama through its OpenAI-compatible API by default, behind one Analyzer
  interface. Use structured/JSON output when supported and validate every response with
  Pydantic before it reaches the UI. Do not send transcripts to external services.
- Config: model names and local endpoint settings come from environment variables (.env),
  never hard-coded. No API key is required. If .env is missing, the run scripts create it
  from .env.example automatically.

### 3.2 API contract
- POST /api/transcribe accepts multipart/form-data with audio (WAV, one speech segment),
  chunk_index and optional language. Returns { "chunk_index": 3, "text": "...",
  "duration_ms": 4200 }.
- POST /api/analyze accepts { "transcript": "..." }. Returns the ClinicalSummary object
  below.
- GET /api/health returns { "status": "ok", "asr": "...", "llm": "..." } and also reports
  "model_ready": true once the Whisper model has loaded.
- POST /api/chat accepts { "transcript": "...", "summary": { }, "message": "..." } and
  returns { "reply": "..." }. It powers the floating chat drawer, answers only from the
  transcript and summary, and says so when the answer is not in them.
- All errors return { "error": { "code": "...", "message": "..." } } with a proper HTTP
  status.

### 3.3 ClinicalSummary schema

```json
{
  "patient": { "name": null, "age": null, "sex": null, "identifiers": [] },
  "chief_complaints": ["..."],
  "history_of_present_illness": {
    "onset": null, "duration": null, "progression": null,
    "aggravating_factors": [], "relieving_factors": []
  },
  "symptoms": { "positive": [], "negative": [] },
  "past_medical_history": { "conditions": [], "surgeries": [], "hospitalisations": [] },
  "medications": [{ "name": "", "dosage": null, "adherence": null }],
  "allergies": [],
  "clinical_observations": { "vitals": [], "examination_findings": [] },
  "assessment": { "provisional_diagnosis": null, "differentials": [] },
  "plan": { "investigations": [], "prescriptions": [], "advice": [], "follow_up": null },
  "clinical_summary": "Concise paragraph suitable for a medical record."
}
```

UI mapping: Patient header = patient. Clinical Summary = clinical_summary. Chief Complaints
= chief_complaints. Symptoms = symptoms (positives and stated negatives shown separately).
Clinical Impression = assessment. Medications = medications. Examinations & Tests =
clinical_observations plus plan.investigations. Allergies = allergies. Past Medical History
= past_medical_history. History & Follow-up = history_of_present_illness plus
plan.follow_up.

### 3.4 Global rules for every agent
- Never invent clinical facts. Anything not said in the transcript is null or an empty
  list. Assessment and plan are recorded only as stated by the clinician.
- Keep positives and stated negatives ("no fever") separate in symptoms.
- Keep the repo structure fixed: /frontend, /backend, /docs. Do not rename shared files or
  change the contracts above without recording it in /docs/CHANGELOG.md.
- Each step ends with its acceptance checks passing and a short hand-off note in
  /docs/handoff-step-N.md listing what was built, how to run it, and known gaps.
- Treat all transcript data as sensitive: no logging of transcript text, no third-party
  analytics.

---

# Where we are now

- Step 1 ✅ — foundation, design tokens, static two-card UI, run scripts, /api/health,
  mock data behind the dev-only "Demo data" toggle. See docs/handoff-step-1.md.
- Step 2 ✅ — real mic capture + Silero VAD chunking (16 k mono WAV chunks, no CDN
  assets, error toasts with Retry). See docs/handoff-step-2.md.
- Next: Step 3 (ASR backend). One step per session; use the hand-off prompt
  template in the PRD (Section 6).
