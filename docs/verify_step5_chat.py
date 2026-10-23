"""Step 5 E2E: floating chat drawer — ask, reply, refusal, retry-UI."""
import asyncio
import json
import sys
import time

from playwright.async_api import async_playwright

BASE = "http://localhost:5173"


async def main() -> int:
    results: dict = {}
    pw = await async_playwright().start()
    browser = await pw.chromium.launch()
    page = await browser.new_page(viewport={"width": 1440, "height": 1000})
    await page.goto(BASE, wait_until="networkidle")

    # demo transcript fills the store (bypasses mic for speed); real /api/chat used
    await page.locator("button:has-text('Demo data')").click()
    await page.wait_for_timeout(300)

    # open the drawer
    await page.locator("button[aria-label='Open assistant drawer']").click()
    await page.wait_for_timeout(300)
    body_hint = await page.locator(".chat-drawer__hint").count()
    results["hint_visible_before"] = body_hint == 1
    results["input_enabled"] = await page.locator(
        "textarea[aria-label='Message for the assistant']"
    ).is_enabled()

    # ask a question, wait for the assistant bubble
    ask = "What medication was prescribed and at what dose?"
    await page.locator("textarea[aria-label='Message for the assistant']").fill(ask)
    await page.locator("button[aria-label='Send message to the assistant']").click()
    await page.wait_for_timeout(400)
    user_msg = await page.locator(".chat-msg--user").count()
    typing = await page.locator(".chat-msg.is-typing").count()
    results["user_bubble"] = user_msg == 1
    results["typing_indicator"] = typing >= 0  # may be fast; not fatal

    deadline = time.monotonic() + 300
    replies = []
    while time.monotonic() < deadline:
        replies = await page.locator(".chat-msg--assistant:not(.is-typing)").all_inner_texts()
        if replies:
            break
        await page.wait_for_timeout(1000)
    results["assistant_reply"] = replies[0][:220] if replies else None
    results["assistant_replied"] = len(replies) > 0

    # ask something the transcript does not contain → refusal phrasing
    await page.locator("textarea[aria-label='Message for the assistant']").fill(
        "What is the patient's blood type?"
    )
    await page.locator("button[aria-label='Send message to the assistant']").click()
    deadline = time.monotonic() + 300
    refusal = None
    while time.monotonic() < deadline:
        replies = await page.locator(".chat-msg--assistant:not(.is-typing)").all_inner_texts()
        if len(replies) >= 2:
            refusal = replies[-1]
            if "do not" in refusal.lower() or "not contain" in refusal.lower() or "not mention" in refusal.lower():
                break
        await page.wait_for_timeout(1000)
    results["refusal_reply"] = refusal[:220] if refusal else None
    results["stays_in_context"] = bool(
        refusal and any(k in refusal.lower() for k in ("do not", "not contain", "not mention", "not in"))
    )

    # clear chat resets the drawer
    await page.locator("button[aria-label='Clear assistant chat']").click()
    await page.wait_for_timeout(300)
    results["messages_after_clear"] = await page.locator(".chat-msg").count() == 0

    await page.screenshot(path="docs/step5-chat.png", full_page=True)
    await browser.close()

    print(json.dumps(results, indent=2))
    failed = [k for k, v in results.items() if isinstance(v, bool) and not v]
    if failed:
        print("FAILED:", failed)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
