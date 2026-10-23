"""Final UI screenshots (desktop + mobile) with demo data loaded."""
import asyncio

from playwright.async_api import async_playwright


async def main() -> None:
    pw = await async_playwright().start()
    browser = await pw.chromium.launch()
    page = await browser.new_page(viewport={"width": 1440, "height": 1000})
    await page.goto("http://localhost:5173", wait_until="networkidle")
    await page.locator("button:has-text('Demo data')").click()
    await page.wait_for_timeout(1200)
    await page.screenshot(path="docs/final-desktop.png", full_page=True)
    await page.set_viewport_size({"width": 390, "height": 844})
    await page.wait_for_timeout(600)
    await page.screenshot(path="docs/final-mobile.png", full_page=True)
    await browser.close()
    await pw.stop()


asyncio.run(main())
