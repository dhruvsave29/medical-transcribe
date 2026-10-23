"""Diagnose the permission-denied path (no fake-ui flags)."""
import asyncio
import json

from playwright.async_api import async_playwright


async def main() -> None:
    logs = []
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(args=["--deny-permission-prompts"])
    page = await browser.new_page(viewport={"width": 1280, "height": 800})
    page.on("console", lambda m: logs.append(m.type + ": " + m.text[:220]))
    await page.goto("http://localhost:5173", wait_until="networkidle")
    await page.locator("button:has-text('Start Mic')").click()
    await page.wait_for_timeout(3000)
    g = await page.evaluate(
        "async () => { try { const s = await navigator.mediaDevices.getUserMedia({audio:true}); return 'GRANTED ' + s.getTracks()[0].label } catch (e) { return 'DENIED: ' + e.name + ' - ' + e.message.slice(0,120) } }"
    )
    toasts = await page.locator(".toast").all_inner_texts()
    state = await page.evaluate(
        "() => { const r = window.__mediscript.recorder; return { chunkCount: r.chunkCount, isRecording: r.isRecording, trackStates: r.trackStates() } }"
    )
    print(json.dumps({"gum_probe": g, "toasts": toasts, "state": state}, indent=1))
    for entry in logs[-12:]:
        print(entry)
    await browser.close()
    await pw.stop()


asyncio.run(main())
