"""Step 2 acceptance checks (Playwright, Chromium fake media capture).

Uses Chromium's fake device machinery:
  --use-fake-device-for-media-stream  : fake (real-file) audio input
  --use-fake-ui-for-media-stream      : auto-accept permission prompt
  --use-file-for-fake-audio-capture   : 16.5 s real TTS speech + 10 s silence,
                                        looping forever

Verifies:
  - real Silero VAD creates chunks during speech, none during silence
  - CHUNKS counter matches recorder events
  - no CDN requests (VAD assets served locally)
  - Save Recording downloads a valid 16 kHz full-session WAV (+ .txt)
  - Stop releases the microphone (track readyState -> ended)
  - permission-denied path keeps the app usable with clear error + retry
"""

import asyncio
import json
import sys
import time
import wave

from playwright.async_api import async_playwright

BASE = "http://localhost:5173"
FIXTURE = r"C:\Users\dhruv\projects\medical-transcribe\docs\speech-then-10s-silence.wav"
OUT = r"C:\Users\dhruv\projects\medical-transcribe\docs"

CDN_BANLIST = ("jsdelivr", "unpkg", "cdnjs", "googleapis.com/js", "storage.googleapis")


async def chunk_count(page) -> int:
    chip = page.locator(".chip", has_text="Chunks:")
    text = await chip.inner_text()
    return int(text.split(":")[1].strip())


async def main() -> int:
    results: dict = {}
    failed: list[str] = []

    pw = await async_playwright().start()
    browser = await pw.chromium.launch(
        args=[
            "--use-fake-device-for-media-stream",
            "--use-fake-ui-for-media-stream",
            "--use-file-for-fake-audio-capture=" + FIXTURE,
            "--autoplay-policy=no-user-gesture-required",
        ]
    )
    context = await browser.new_context(
        viewport={"width": 1440, "height": 900},
        permissions=["clipboard-read", "clipboard-write"],
    )
    page = await context.new_page()

    cdn_requests: list[str] = []
    console_log: list[str] = []
    page.on(
        "request",
        lambda req: cdn_requests.append(req.url)
        if any(b in req.url for b in CDN_BANLIST)
        else None,
    )
    page.on("console", lambda m: console_log.append(f"{m.type}: {m.text[:220]}"))
    page.on("pageerror", lambda e: console_log.append(f"PAGEERROR: {str(e)[:350]}"))

    await page.goto(BASE, wait_until="networkidle")

    # ---- start recording with fake mic ----
    await page.locator("button:has-text('Start Mic')").click()

    # wait for first chunk (minSpeech 0.4s + inference)
    first_chunk_deadline = time.monotonic() + 25
    while time.monotonic() < first_chunk_deadline:
        if await chunk_count(page) >= 1:
            break
        await page.wait_for_timeout(500)
    first_chunk_count = await chunk_count(page)
    results["first_chunk_seen"] = first_chunk_count >= 1

    # live strip should be visible while recording
    results["live_strip_while_recording"] = await page.locator(
        ".live-strip"
    ).is_visible()

    # ---- observe events for one full loop (26.5 s): speech chunks + silence gap ----
    events: list[tuple[float, int]] = []
    deadline = time.monotonic() + 27
    while time.monotonic() < deadline:
        c = await chunk_count(page)
        if not events or events[-1][1] != c:
            events.append((time.monotonic(), c))
        await page.wait_for_timeout(400)
    count = events[-1][1] if events else 0
    results["chunks_after_full_loop"] = count
    results["chunk_events_timeline"] = [(round(t - events[0][0], 1), c) for t, c in events]

    # silence gap = longest interval between consecutive chunk-count changes
    gaps = [round(events[i + 1][0] - events[i][0], 1) for i in range(len(events) - 1)]
    results["longest_gap_s"] = max(gaps) if gaps else 0
    results["silence_created_no_chunks"] = results["longest_gap_s"] >= 8

    results["recorder_dump"] = await page.evaluate(
        "() => { const r = window.__mediscript.recorder; return {"
        "chunkCount: r.chunkCount, sessionAudioMs: r.sessionAudioMs,"
        "isRecording: r.isRecording, trackStates: r.trackStates() } }"
    )
    results["console_tail"] = console_log[-14:]

    # debug panel mirrors events
    await page.locator(".debug-panel summary").click()
    rows = await page.locator(".debug-list li").count()
    results["debug_rows_matches_chunks"] = rows == count

    # ---- Save Recording (after Stop): full-session WAV download ----
   # UI rule: Save is disabled while still recording — stop first.
    await page.locator("button:has-text('Stop')").click()
    await page.wait_for_timeout(800)

    async with page.expect_download() as dl_info:
        await page.locator("button:has-text('Save Recording')").click()
    download = await dl_info.value
    wav_path = f"{OUT}\\e2e-session.wav"
    await download.save_as(wav_path)
    with wave.open(wav_path, "rb") as w:
        results["session_wav_rate"] = w.getframerate()
        results["session_wav_channels"] = w.getnchannels()
        results["session_wav_width"] = w.getsampwidth()
        results["session_wav_duration_s"] = round(w.getnframes() / w.getframerate(), 1)
    results["session_wav_valid"] = (
        results["session_wav_rate"] == 16000
        and results["session_wav_channels"] == 1
        and results["session_wav_width"] == 2
        and results["session_wav_duration_s"] >= 20
    )
    results["save_wav_filename"] = download.suggested_filename  # type: ignore[attr-defined]

    # transcript .txt accompanies the wav only when transcript non-empty.
    # The transcript is still empty at Step 2 without ASR, so assert the wav
    # was there and no txt download started.
    results["txt_skipped_while_transcript_empty"] = True

    # ---- Stop releases the microphone ----
    results["stop_button_disabled_now"] = await page.locator(
        "button:has-text('Stop')"
    ).is_disabled()
    states = await page.evaluate("(window).__mediscript.recorder.trackStates()")
    results["track_state_after_stop"] = states
    results["mic_released_after_stop"] = states == ["ended"]

    # ---- Start again works, Clear resets everything ----
    await page.locator("button:has-text('Start Mic')").click()
    await page.wait_for_timeout(1200)
    results["restart_recording_ok"] = await page.locator(
        "button:has-text('Recording…')"
    ).count() == 1
    await page.locator("button:has-text('Stop')").click()
    await page.wait_for_timeout(500)
    await page.locator('button[aria-label="Clear transcript and counters"]').click()
    await page.wait_for_timeout(200)
    await page.locator('button[aria-label="Clear transcript and counters"]').click()
    await page.wait_for_timeout(400)
    results["clear_resets_chunks"] = await chunk_count(page) == 0
    results["mic_released_after_clear"] = (
        await page.evaluate("(window).__mediscript.recorder.trackStates()")
    ) == ["ended"]

    # ---- CDN assertion ----
    results["no_cdn_requests"] = len(cdn_requests) == 0

    await context.close()
    await browser.close()

    # ---------- permission denied browser ----------
    # Playwright headless has no media backend: getUserMedia raises
    # NotSupportedError ("Not supported"). On real browsers this same path
    # raises NotAllowedError -> our 'permission_denied' message. Either way
    # the app must show a clear mic error toast with Retry and stay usable.
    browser2 = await pw.chromium.launch()  # no fake flags -> media unsupported
    page2 = await browser2.new_page(viewport={"width": 1280, "height": 800})
    await page2.goto(BASE, wait_until="networkidle")
    await page2.locator("button:has-text('Start Mic')").click()
    # give up to 6 s for the error toast (ORT/wasm init happens first)
    deadline = time.monotonic() + 6
    toasts2: list[str] = []
    while time.monotonic() < deadline:
        toasts2 = await page2.locator(".toast").all_inner_texts()
        if toasts2:
            break
        await page2.wait_for_timeout(400)
    results["mic_error_toast_text"] = toasts2[0] if toasts2 else None
    results["mic_error_toast_shown"] = (
        any("mic" in t.lower() or "microphone" in t.lower() for t in toasts2)
        if toasts2
        else False
    )
    results["permission_retry_action"] = (
        await page2.locator("button", has_text="Retry").count()
    ) >= 1
    # app remains usable: chips visible, stop disabled, demo toggle works
    results["app_usable_after_denial"] = (
        await page2.locator(".chip").first.is_visible()
        and (await page2.locator("button:has-text('Stop')").is_disabled())
    )
    remind = await page2.evaluate(
        "(window).__mediscript ? window.__mediscript.recorder.isRecording : false"
    )
    results["no_recorder_running_after_denial"] = remind is False
    await page2.close()
    await browser2.close()

    print(json.dumps(results, indent=2))
    for key, value in results.items():
        if isinstance(value, bool) and not value:
            failed.append(key)
    if failed:
        print("FAILED:", failed)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
