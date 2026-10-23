"""Step 3 E2E: fake mic -> VAD chunks -> /api/transcribe -> live transcript."""
import asyncio
import json
import sys
import time

from playwright.async_api import async_playwright

BASE = "http://localhost:5173"
FIXTURE = "C:/Users/dhruv/projects/medical-transcribe/docs/speech-then-10s-silence.wav"


async def chunk_count(page) -> int:
    chips = await page.locator(".chip").all_inner_texts()
    for chip in chips:
        if "chunks" in chip.lower():
            num = chip.split(":")[-1].strip()
            return int(num) if num.isdigit() else 0
    return 0


async def main() -> int:
    results: dict = {}
    console_log = []
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(
        args=[
            "--use-fake-device-for-media-stream",
            "--use-fake-ui-for-media-stream",
            "--use-file-for-fake-audio-capture=" + FIXTURE,
            "--autoplay-policy=no-user-gesture-required",
        ]
    )
    page = await browser.new_page(viewport={"width": 1280, "height": 800})
    page.on("console", lambda m: console_log.append(m.type + ": " + m.text[:200]))
    await page.goto(BASE, wait_until="networkidle")

    await page.locator("button:has-text('Start Mic')").click()

    # first chunk transcribed (model is preloaded, so ~a few seconds per chunk)
    deadline = time.monotonic() + 60
    words_txt = ""
    while time.monotonic() < deadline:
        words_txt = await page.locator(".chip", has_text="Words:").inner_text()
        if "Words: 0" not in words_txt:
            break
        await page.wait_for_timeout(600)
    results["words_counter_update"] = words_txt
    results["live_transcript_started"] = "Words: 0" not in words_txt

    # keep recording for one full loop (26.5 s of speech then silence)
    deadline = time.monotonic() + 27
    seen = set()
    while time.monotonic() < deadline:
        t = await page.locator(".chip", has_text="Words:").inner_text()
        seen.add(t)
        await page.wait_for_timeout(500)
    results["words_final"] = next(iter(sorted(seen))) if seen else ""
    transcript = await page.locator(".transcript-box").inner_text()
    results["transcript_preview"] = transcript[:220]
    results["transcript_non_empty"] = len(transcript.strip()) > 40

    # live strip visible while uploading
    results["live_strip_visible"] = await page.locator(".live-strip").is_visible()

    # uploader drained (dev-only handle)
    state = await page.evaluate(
        "() => { const m = window.__mediscript; return {"
        "chunkCount: m.recorder.chunkCount, pending: m.chunkUploader.pending } }"
    )
    results["uploader_dump"] = state
    results["uploader_drained"] = state["pending"] == 0

    # words counter matches transcript word count (chip is styled uppercase via CSS)
    words = len(transcript.split())
    words_fresh = await page.locator(".chip", has_text="Words:").inner_text()
    results["words_match"] = words_fresh.split(":")[-1].strip() == str(words)

    await page.screenshot(path="docs/step3-live-transcript.png", full_page=True)
    await browser.close()

    results["console_tail"] = console_log[-8:]
    print(json.dumps(results, indent=2))

    failed = [k for k, v in results.items() if isinstance(v, bool) and not v]
    if failed:
        print("FAILED:", failed)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
