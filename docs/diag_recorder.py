"""Diagnose why the fake-media recorder produced no chunks."""
import asyncio
import json

from playwright.async_api import async_playwright


async def main() -> None:
    logs = []
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(
        args=[
            "--use-fake-device-for-media-stream",
            "--use-fake-ui-for-media-stream",
            "--use-file-for-fake-audio-capture=C:/Users/dhruv/projects/medical-transcribe/docs/speech-then-10s-silence.wav",
            "--autoplay-policy=no-user-gesture-required",
        ]
    )
    page = await browser.new_page(viewport={"width": 1280, "height": 800})
    page.on("console", lambda m: logs.append(m.type + ": " + m.text[:250]))
    page.on("pageerror", lambda e: logs.append("PAGEERROR: " + str(e)[:350]))
    await page.goto("http://localhost:5173", wait_until="networkidle")
    await page.locator("button:has-text('Start Mic')").click()
    await page.wait_for_timeout(10000)
    state = await page.evaluate(
        "() => { const r = window.__mediscript.recorder; return {"
        "chunkCount: r.chunkCount,"
        "sessionAudioMs: r.sessionAudioMs,"
        "isRecording: r.isRecording,"
        "trackStates: r.trackStates() } }"
    )
    chips = await page.locator(".chip").all_inner_texts()
    toasts = await page.locator(".toast").all_inner_texts()
    print(json.dumps({"state": state, "chips": chips, "toasts": toasts}, indent=1))
    print("CONSOLE ---")
    for entry in logs:
        print(entry)
    await browser.close()
    await pw.stop()


asyncio.run(main())
