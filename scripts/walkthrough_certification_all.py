import asyncio
import os
import time
import uuid
import urllib.request
import json
from playwright.async_api import async_playwright

SCREENSHOT_DIR = "/mnt/c/Users/acer/.gemini/antigravity/brain/4fe36a86-34a3-44c5-8725-e56313d016b4/.user_uploaded"

async def run_walkthrough_scenarios():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1400, "height": 900})

        # --- SCENARIO E: Non-Blocking Warning (W/B ratio 0.52) ---
        print("Executing Scenario E (Warning W/B 0.52)...")
        await page.goto("http://localhost:5173")
        await page.wait_for_timeout(1500)
        await page.locator("button:has-text('Manual Production Entry')").click()
        await page.wait_for_timeout(1000)
        await page.locator("select").first.select_option(index=1)
        await page.locator("select").nth(1).select_option(index=1)
        await page.locator("button:has-text('Proceed')").click()
        await page.wait_for_timeout(1000)
        await page.locator("input[type='text']").nth(0).fill("TM-MUM-402")
        await page.locator("input[type='text']").nth(1).fill(f"DC-{uuid.uuid4().hex[:6].upper()}")
        await page.locator("button:has-text('Proceed')").click()
        await page.wait_for_timeout(1000)

        # Step 3: Set Water to 230 kg/m3 (W/B ~ 0.511)
        water_in = page.locator("input[name*='water']")
        if await water_in.count() > 0:
            await water_in.fill("230")
        await page.locator("button:has-text('Proceed')").click()
        await page.wait_for_timeout(1000)

        # Step 4: Save valid QA
        await page.locator("input[type='text']").first.fill(f"QC-WARN-{uuid.uuid4().hex[:4].upper()}")
        await page.locator("input[type='date']").nth(0).fill("2026-08-09")
        await page.locator("input[type='date']").nth(1).fill("2026-09-06")
        await page.locator("input[type='number']").nth(0).fill("30.8")
        await page.locator("input[type='number']").nth(1).fill("51.3")
        await page.locator("button:has-text('Save Step 4')").click()
        await page.wait_for_timeout(2500)

        path_e = os.path.join(SCREENSHOT_DIR, f"media_{int(time.time()*1000)}_scenario_e.png")
        await page.screenshot(path=path_e)
        print(f"Captured Scenario E: {path_e}")

        # --- SCENARIO C: Strength Deficit (35.0 MPa vs 40.0 MPa target) ---
        print("Executing Scenario C (Strength Deficit)...")
        await page.locator("button:has-text('Back to Step 4')").click()
        await page.wait_for_timeout(1000)
        await page.locator("input[type='number']").nth(1).fill("35.0")
        await page.locator("button:has-text('Save Step 4')").click()
        await page.wait_for_timeout(2500)

        path_c = os.path.join(SCREENSHOT_DIR, f"media_{int(time.time()*1000)}_scenario_c.png")
        await page.screenshot(path=path_c)
        print(f"Captured Scenario C: {path_c}")

        # --- SCENARIO D: Failure Reason Code Exception ---
        print("Executing Scenario D (Failure Reason CURING_ISSUE)...")
        await page.locator("button:has-text('Back to Step 4')").click()
        await page.wait_for_timeout(1000)
        await page.locator("input[type='number']").nth(1).fill("51.3")
        await page.locator("select").first.select_option(value="CURING_ISSUE")
        await page.locator("textarea").first.fill("Water bath temperature excursion during curing phase.")
        await page.locator("button:has-text('Save Step 4')").click()
        await page.wait_for_timeout(2500)

        path_d = os.path.join(SCREENSHOT_DIR, f"media_{int(time.time()*1000)}_scenario_d.png")
        await page.screenshot(path=path_d)
        print(f"Captured Scenario D: {path_d}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_walkthrough_scenarios())
