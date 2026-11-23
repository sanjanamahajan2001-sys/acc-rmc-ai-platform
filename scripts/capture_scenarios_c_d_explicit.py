import asyncio
import os
import time
import uuid
from playwright.async_api import async_playwright

SCREENSHOT_DIR = "/mnt/c/Users/acer/.gemini/antigravity/brain/4fe36a86-34a3-44c5-8725-e56313d016b4/.user_uploaded"

async def capture_scenarios_c_d_explicit():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # --- SCENARIO D: Failure Reason Code Exception (CURING_ISSUE) ---
        print("Capturing Scenario D (Failure Reason CURING_ISSUE)...")
        page2 = await browser.new_page(viewport={"width": 1400, "height": 900})
        await page2.goto("http://localhost:5173")
        await page2.wait_for_timeout(1000)

        await page2.locator("button:has-text('Manual Production Entry')").click()
        await page2.wait_for_timeout(1000)
        await page2.locator("select").first.select_option(index=1)
        await page2.locator("select").nth(1).select_option(value="M40_VW_UT_ISOLATED")
        await page2.locator("button:has-text('Proceed')").click()
        await page2.wait_for_timeout(500)

        await page2.locator("input[type='text']").nth(0).fill("TM-MUM-402")
        await page2.locator("input[type='text']").nth(1).fill(f"DC-{uuid.uuid4().hex[:6].upper()}")
        await page2.locator("button:has-text('Proceed')").click()
        await page2.wait_for_timeout(500)
        await page2.locator("button:has-text('Proceed')").click()
        await page2.wait_for_timeout(500)

        # Step 4: CURING_ISSUE failure reason + explanatory text input fill
        await page2.locator("input[type='text']").first.fill(f"QC-REASON-{uuid.uuid4().hex[:4].upper()}")
        await page2.locator("input[type='date']").nth(0).fill("2026-08-09")
        await page2.locator("input[type='date']").nth(1).fill("2026-09-06")
        await page2.locator("input[type='number']").nth(0).fill("30.8")
        await page2.locator("input[type='number']").nth(1).fill("51.3")
        await page2.locator("select").first.select_option(value="CURING_ISSUE")

        # Fill mandatory failure_reason_text input
        reason_text_input = page2.locator("input[placeholder*='Detail root cause'], input[name*='reason_text'], input[placeholder*='root cause']")
        if await reason_text_input.count() > 0:
            await reason_text_input.fill("Water bath temperature excursion during curing phase.")
        else:
            # Fallback input search
            await page2.locator("input[type='text']").nth(3).fill("Water bath temperature excursion during curing phase.")

        await page2.locator("button:has-text('Save Step 4')").click()
        await page2.wait_for_timeout(2000)
        await page2.locator("text=5. Quality Checks").click()
        await page2.wait_for_timeout(2500)

        ts_d = int(time.time()*1000)
        path_d = os.path.join(SCREENSHOT_DIR, f"media_{ts_d}_scenario_d.png")
        await page2.screenshot(path=path_d)
        print(f"Captured Scenario D: {path_d}")
        await page2.close()

        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_scenarios_c_d_explicit())
