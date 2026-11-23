import asyncio
import os
import time
import uuid
from playwright.async_api import async_playwright

SCREENSHOT_DIR = "/mnt/c/Users/acer/.gemini/antigravity/brain/4fe36a86-34a3-44c5-8725-e56313d016b4/.user_uploaded"

async def capture_scenarios_c_and_d():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # --- SCENARIO C: Strength Deficit (35.0 MPa vs 40.0 target) ---
        print("Capturing Scenario C (35.0 MPa result)...")
        page = await browser.new_page(viewport={"width": 1400, "height": 900})
        await page.goto("http://localhost:5173")
        await page.wait_for_timeout(1000)

        await page.locator("button:has-text('Manual Production Entry')").click()
        await page.wait_for_timeout(1000)
        await page.locator("select").first.select_option(index=1)
        await page.locator("select").nth(1).select_option(index=1)
        await page.locator("button:has-text('Proceed')").click()
        await page.wait_for_timeout(500)
        await page.locator("input[type='text']").nth(0).fill("TM-MUM-402")
        await page.locator("input[type='text']").nth(1).fill(f"DC-{uuid.uuid4().hex[:6].upper()}")
        await page.locator("button:has-text('Proceed')").click()
        await page.wait_for_timeout(500)
        await page.locator("button:has-text('Proceed')").click()
        await page.wait_for_timeout(500)

        # Step 4: Strength 35.0 MPa
        await page.locator("input[type='text']").first.fill(f"QC-LOW-{uuid.uuid4().hex[:4].upper()}")
        await page.locator("input[type='date']").nth(0).fill("2026-08-09")
        await page.locator("input[type='date']").nth(1).fill("2026-09-06")
        await page.locator("input[type='number']").nth(0).fill("30.8")
        await page.locator("input[type='number']").nth(1).fill("35.0")
        await page.locator("button:has-text('Save Step 4')").click()
        await page.wait_for_timeout(2000)
        await page.locator("text=5. Quality Checks").click()
        await page.wait_for_timeout(2000)

        path_c = os.path.join(SCREENSHOT_DIR, f"media_{int(time.time()*1000)}_scenario_c.png")
        await page.screenshot(path=path_c)
        print(f"Captured Scenario C: {path_c}")
        await page.close()

        # --- SCENARIO D: Failure Reason Code Exception ---
        print("Capturing Scenario D (Failure Reason CURING_ISSUE)...")
        page2 = await browser.new_page(viewport={"width": 1400, "height": 900})
        await page2.goto("http://localhost:5173")
        await page2.wait_for_timeout(1000)

        await page2.locator("button:has-text('Manual Production Entry')").click()
        await page2.wait_for_timeout(1000)
        await page2.locator("select").first.select_option(index=1)
        await page2.locator("select").nth(1).select_option(index=1)
        await page2.locator("button:has-text('Proceed')").click()
        await page2.wait_for_timeout(500)
        await page2.locator("input[type='text']").nth(0).fill("TM-MUM-402")
        await page2.locator("input[type='text']").nth(1).fill(f"DC-{uuid.uuid4().hex[:6].upper()}")
        await page2.locator("button:has-text('Proceed')").click()
        await page2.wait_for_timeout(500)
        await page2.locator("button:has-text('Proceed')").click()
        await page2.wait_for_timeout(500)

        # Step 4: CURING_ISSUE reason code
        await page2.locator("input[type='text']").first.fill(f"QC-REASON-{uuid.uuid4().hex[:4].upper()}")
        await page2.locator("input[type='date']").nth(0).fill("2026-08-09")
        await page2.locator("input[type='date']").nth(1).fill("2026-09-06")
        await page2.locator("input[type='number']").nth(0).fill("30.8")
        await page2.locator("input[type='number']").nth(1).fill("51.3")
        await page2.locator("select").first.select_option(value="CURING_ISSUE")
        await page2.locator("textarea").first.fill("Water bath temperature excursion during curing phase.")
        await page2.locator("button:has-text('Save Step 4')").click()
        await page2.wait_for_timeout(2000)
        await page2.locator("text=5. Quality Checks").click()
        await page2.wait_for_timeout(2000)

        path_d = os.path.join(SCREENSHOT_DIR, f"media_{int(time.time()*1000)}_scenario_d.png")
        await page2.screenshot(path=path_d)
        print(f"Captured Scenario D: {path_d}")
        await page2.close()

        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_scenarios_c_and_d())
