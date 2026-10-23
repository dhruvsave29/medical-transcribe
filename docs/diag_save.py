"""Diagnose Save Recording download flow."""
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
    page.on("console", lambda m: logs.append(m.type + ": " + m.text[:200]))
    downloads = []
    page.on("download", lambda d: downloads.append(d.suggested_filename))
    await page.goto("http://localhost:5173", wait_until="networkidle")

    # sanity: does a plain blob anchor download get intercepted?
    probe = asyncio.ensure_future(page.wait_for_event("download", timeout=5000))
    await page.evaluate(
        "() => { const a = document.createElement('a');"
        "a.href = URL.createObjectURL(new Blob(['x'], {type:'text/plain'}));"
        "a.download = 'probe.txt'; document.body.appendChild(a); a.click(); a.remove(); }"
    )
    try:
        d = await probe
        print("probe download OK:", d.suggested_filename)
    except Exception as e:
        print("probe download FAILED:", e)

    await page.locator("button:has-text('Start Mic')").click()
    await page.wait_for_timeout(9000)
    await page.locator("button:has-text('Stop')").click()
    await page.wait_for_timeout(1000)
    toasts1 = await page.locator(".toast").all_inner_texts()
    save_enabled = await page.locator("button:has-text('Save Recording')").is_enabled()
    state = await page.evaluate(
        "() => { const r = window.__mediscript.recorder; return {"
        "chunkCount: r.chunkCount, sessionAudioMs: r.sessionAudioMs,"
        "trackStates: r.trackStates() } }"
    )
    print(json.dumps({"toasts1": toasts1, "save_enabled": save_enabled, "state": state}))
    probe2 = asyncio.ensure_future(page.wait_for_event("download", timeout=8000))
    await page.locator("button:has-text('Save Recording')").click()
    try:
        d2 = await probe2
        print("save download OK:", d2.suggested_filename)
    except Exception as e:
        print("save download FAILED:", e)
    toasts2 = await page.locator(".toast").all_inner_texts()
    print("toasts2:", toasts2)
    print("downloads:", downloads)
    for line in logs[-10:]:
        print(line)
    await browser.close()
    await pw.stop()


asyncio.run(main())
