import asyncio
import os
import time
import uuid
from playwright.async_api import async_playwright

SCREENSHOT_DIR = "/mnt/c/Users/acer/.gemini/antigravity/brain/4fe36a86-34a3-44c5-8725-e56313d016b4/.user_uploaded"

async def run_walkthrough():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1400, "height": 900})

        print("Navigating to ACC RMC Platform...")
        await page.goto("http://localhost:5173")
        await page.wait_for_timeout(2000)

        # Open Manual Entry Modal Wizard
        print("Opening Manual Entry Wizard...")
        await page.locator("button:has-text('Manual Production Entry')").click()
        await page.wait_for_timeout(1000)

        # Step 1: Select Plant & Recipe
        print("Step 1: Filling Batch Info...")
        await page.locator("select").first.select_option(index=1)
        await page.locator("select").nth(1).select_option(index=1)
        await page.locator("button:has-text('Proceed')").click()
        await page.wait_for_timeout(1000)

        # Step 2: Fill Machine & Batch Details
        print("Step 2: Filling Machine Details...")
        truck_input = page.locator("input[placeholder*='Truck'], input[name*='truck'], input#truck_number").first
        if await truck_input.count() > 0:
            await truck_input.fill("TM-MUM-402")
        else:
            await page.locator("input[type='text']").nth(0).fill("TM-MUM-402")

        challan_input = page.locator("input[placeholder*='Challan'], input[name*='challan'], input#delivery_challan").first
        if await challan_input.count() > 0:
            await challan_input.fill(f"DC-{uuid.uuid4().hex[:6].upper()}")
        else:
            await page.locator("input[type='text']").nth(1).fill(f"DC-{uuid.uuid4().hex[:6].upper()}")

        await page.locator("button:has-text('Proceed')").click()
        await page.wait_for_timeout(1000)

        # Step 3: Material Consumption
        print("Step 3: Materials...")
        await page.locator("button:has-text('Proceed')").click()
        await page.wait_for_timeout(1000)

        # Step 4: Laboratory QA (Scenario A: Valid 28-Day)
        print("Step 4: Filling Valid Laboratory QA (Scenario A)...")
        cube_input = page.locator("input[placeholder*='Cube'], input#qa_cube_id").first
        if await cube_input.count() > 0:
            await cube_input.fill(f"QC-PASS-{uuid.uuid4().hex[:6].upper()}")
        else:
            await page.locator("input[type='text']").first.fill(f"QC-PASS-{uuid.uuid4().hex[:6].upper()}")

        dates = page.locator("input[type='date']")
        if await dates.count() >= 2:
            await dates.nth(0).fill("2026-08-09")
            await dates.nth(1).fill("2026-09-06") # 28 days

        numbers = page.locator("input[type='number']")
        if await numbers.count() >= 2:
            await numbers.nth(0).fill("30.8")
            await numbers.nth(1).fill("51.3")

        save_btn = page.locator("button:has-text('Save Step 4')")
        if await save_btn.is_enabled():
            await save_btn.click()
            await page.wait_for_timeout(2500)

        # Scenario A: Clean Pass Quality Gate
        print("Scenario A: Capturing Step 5 Clean Pass Quality Gate...")
        ts_a = int(time.time()*1000)
        path_a = os.path.join(SCREENSHOT_DIR, f"media_{ts_a}.png")
        await page.screenshot(path=path_a)
        print(f"Captured Scenario A: {path_a}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_walkthrough())
