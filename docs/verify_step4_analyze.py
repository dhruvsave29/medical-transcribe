"""Step 4 E2E: full pipeline — mic -> VAD -> ASR -> /api/analyze -> summary card."""
import asyncio
import json
import sys
import time

from playwright.async_api import async_playwright

BASE = "http://localhost:5173"
FIXTURE = "C:/Users/dhruv/projects/medical-transcribe/docs/speech-then-10s-silence.wav"


async def main() -> int:
    results: dict = {}
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(
        args=[
            "--use-fake-device-for-media-stream",
            "--use-fake-ui-for-media-stream",
            "--use-file-for-fake-audio-capture=" + FIXTURE,
            "--autoplay-policy=no-user-gesture-required",
        ]
    )
    page = await browser.new_page(viewport={"width": 1440, "height": 1000})
    await page.goto(BASE, wait_until="networkidle")

    # ---- capture + transcribe (Steps 2/3) ----
    await page.locator("button:has-text('Start Mic')").click()
    deadline = time.monotonic() + 40
    while time.monotonic() < deadline:
        words = await page.locator(".chip", has_text="Words:").inner_text()
        if "Words: 0" not in words:
            break
        await page.wait_for_timeout(500)
    results["transcript_started"] = "Words: 0" not in words

    # wait for all chunks uploaded (drained) before stopping/analyzing
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        state = await page.evaluate(
            "() => { const m = window.__mediscript;"
            " return { chunkCount: m.recorder.chunkCount, pending: m.chunkUploader.pending } }"
        )
        if state["chunkCount"] >= 2 and state["pending"] == 0:
            break
        await page.wait_for_timeout(800)
    results["uploader_dump"] = state
    results["uploader_drained"] = state["pending"] == 0 and state["chunkCount"] >= 2

    await page.locator("button:has-text('Stop')").click()
    await page.wait_for_timeout(1200)

    transcript = await page.locator(".transcript-box").inner_text()
    results["transcript_chars"] = len(transcript)
    results["transcript_ok"] = len(transcript) > 100

    # Stop button disabled, CTA enabled
    results["stop_disabled_now"] = await page.locator(
        "button:has-text('Stop')"
    ).is_disabled()
    results["cta_enabled"] = await page.locator(
        "button[aria-label='Process transcript with AI']"
    ).is_enabled()

    # ---- analyse (Step 4): spinner + 'Analysing…' while processing ----
    cta = page.locator("button[aria-label='Process transcript with AI']")
    results["cta_ready"] = await cta.is_enabled()
    await cta.click()
    await page.wait_for_timeout(600)
    processing_text = await cta.inner_text()
    results["processing_label"] = processing_text
    results["cta_spinning"] = (
        "Analys" in processing_text
        and await cta.is_disabled()
        and await page.locator(".btn--busy .spinner").count() == 1
    )

    # wait for completion: toast or textarea filled (qwen2.5:3b CPU can take a while)
    textarea = page.locator(".summary-textarea")
    deadline = time.monotonic() + 300
    summary_len = 0
    while time.monotonic() < deadline:
        summary_len = len((await textarea.input_value()).strip())
        if summary_len > 30:
            break
        await page.wait_for_timeout(1000)
    results["clinical_summary_chars"] = summary_len
    results["summary_filled"] = summary_len > 30

    # sections no longer all empty: find at least one non-empty bullet section
    bullets = 0
    try:
        bullets = await page.locator(".summary-card li, .list-unstyled li").count()
    except Exception:
        bullets = 0
    results["summary_bullets"] = bullets
    results["summary_sections_filled"] = bullets >= 2

    # patient header appears with a value
    header_txt = await page.locator(".patient-header").inner_text() if await page.locator(
        ".patient-header"
    ).count() else "(none)"
    results["patient_header"] = header_txt[:160]

    await page.screenshot(path="docs/step4-summary.png", full_page=True)
    await browser.close()

    print(json.dumps(results, indent=2))
    failed = [k for k, v in results.items() if isinstance(v, bool) and not v]
    if failed:
        print("FAILED:", failed)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
