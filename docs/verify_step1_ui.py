"""Step 1 UI acceptance checks with Playwright.

Verifies: page loads, both cards present, empty states, buttons wired,
demo toggle fills mock data, copy button state, responsive widths with no
horizontal scroll, and captures screenshots.
"""

import asyncio
import json
import sys

from playwright.async_api import async_playwright

BASE = "http://localhost:5173"
OUT = r"C:\Users\dhruv\projects\medical-transcribe\docs"


async def main() -> int:
    results = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch()

        # ---------- Desktop 1440 ----------
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            permissions=["clipboard-read", "clipboard-write"],
        )
        page = await context.new_page()
        await page.goto(BASE, wait_until="networkidle")

        results["title"] = await page.title()
        results["health_pill"] = await page.locator(".status-pill").inner_text()
        results["left_title"] = await page.locator("h2#transcription-title").inner_text()
        results["right_title"] = await page.locator("h2#summary-title").inner_text()

        # Empty states present
        empties = await page.locator(".empty:visible").count()
        results["empty_state_count_initial"] = empties
        results["cta_disabled_initial"] = await page.locator(
            "button:has-text('Process Transcript with AI')"
        ).is_disabled()
        results["copy_disabled_initial"] = await page.locator(
            "button:has-text('Copy to Prescription')"
        ).is_disabled()
        results["words_chip"] = (
            await page.locator(".chip").first.inner_text()
        ).replace("\n", " ")

        # Buttons state machine
        await page.locator("button:has-text('Start Mic')").click()
        results["start_recording_state"] = await page.locator(
            "button:has-text('Recording…')"
        ).count() == 1
        results["live_strip_visible"] = await page.locator(".live-strip").is_visible()
        results["stop_enabled_recording"] = await page.locator(
            "button:has-text('Stop')"
        ).is_enabled()
        await page.locator("button:has-text('Stop')").click()
        results["back_to_stopped"] = await page.locator(
            "button:has-text('Start Mic')"
        ).count() == 1

        # CTA against not-yet-implemented /api/analyze -> toast with demo option
        await page.locator("button:has-text('Process Transcript with AI')").is_disabled()
        await page.locator(".demo-toggle").click()  # turn mock on
        await page.wait_for_timeout(250)
        results["mock_words"] = await page.locator(".chip").first.inner_text()
        results["mock_patient"] = await page.locator(".patient-name").inner_text()
        results["mock_summary_value_len"] = len(
            await page.locator(".summary-textarea").input_value()
        )
        results["cta_enabled_with_mock"] = await page.locator(
            "button:has-text('Process Transcript with AI')"
        ).is_enabled()
        results["copy_enabled_with_mock"] = await page.locator(
            "button:has-text('Copy to Prescription')"
        ).is_enabled()
        results["med_rows"] = await page.locator(".med-row").count()
        results["negatives_label"] = await page.locator(
            "text=Denied by patient"
        ).count() == 1
        await page.screenshot(path=f"{OUT}\\step1-desktop-mock.png", full_page=False)

        # Copy to Prescription writes to clipboard
        await page.locator("button:has-text('Copy to Prescription')").click()
        await page.wait_for_timeout(400)
        clip = await page.evaluate("navigator.clipboard.readText()")
        results["prescription_text_ok"] = clip.startswith("PATIENT: Ramesh Gupta")
        results["prescription_len"] = len(clip)

        # Horizontal scroll check at 1440
        results["no_hscroll_1440"] = await page.evaluate(
            "document.documentElement.scrollWidth <= window.innerWidth"
        )
        await page.locator(".demo-toggle").click()  # mock off -> clean reset
        await page.wait_for_timeout(250)
        results["cleared_after_mock_off"] = (
            await page.locator(".chip").first.inner_text()
        ).replace("\n", " ")
        await page.close()
        await context.close()

        # ---------- Mobile 360 ----------
        page2 = await browser.new_page(viewport={"width": 360, "height": 740})
        await page2.goto(BASE, wait_until="networkidle")
        results["stacked_order"] = await page2.evaluate(
            """() => {
                const first = document.querySelectorAll('.card')[0]
                  .getBoundingClientRect();
                const second = document.querySelectorAll('.card')[1]
                  .getBoundingClientRect();
                return first.top < second.top && first.width <= 360;
            }"""
        )
        results["no_hscroll_360"] = await page2.evaluate(
            "document.documentElement.scrollWidth <= window.innerWidth"
        )
        await page2.screenshot(path=f"{OUT}\\step1-mobile.png", full_page=True)
        await page2.close()

        # ---------- Tablet 800 ----------
        page3 = await browser.new_page(viewport={"width": 800, "height": 900})
        await page3.goto(BASE, wait_until="networkidle")
        results["no_hscroll_800"] = await page3.evaluate(
            "document.documentElement.scrollWidth <= window.innerWidth"
        )
        await page3.close()

        await browser.close()

    print(json.dumps(results, indent=2))
    ok = all(v is not False for v in results.values() if isinstance(v, bool))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
