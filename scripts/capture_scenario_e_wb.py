import asyncio
import os
import time
import uuid
from playwright.async_api import async_playwright

SCREENSHOT_DIR = "/mnt/c/Users/acer/.gemini/antigravity/brain/4fe36a86-34a3-44c5-8725-e56313d016b4/.user_uploaded"

async def capture_scenario_e_wb():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1400, "height": 900})

        await page.goto("http://localhost:5173")
        await page.wait_for_timeout(1500)

        await page.locator("button:has-text('Manual Production Entry')").click()
        await page.wait_for_timeout(1000)

        # Step 1
        await page.locator("select").first.select_option(index=1)
        await page.locator("select").nth(1).select_option(index=1)
        await page.locator("button:has-text('Proceed')").click()
        await page.wait_for_timeout(1000)

        # Step 2
        await page.locator("input[type='text']").nth(0).fill("TM-MUM-402")
        await page.locator("input[type='text']").nth(1).fill(f"DC-{uuid.uuid4().hex[:6].upper()}")
        await page.locator("button:has-text('Proceed')").click()
        await page.wait_for_timeout(1000)

        # Step 3: Water input fill index 3 or by name
        water_input = page.locator("input[type='number']").nth(3) # water field index
        await water_input.fill("235.0") # High water -> W/B = 0.522 > 0.50
        await page.locator("button:has-text('Proceed')").click()
        await page.wait_for_timeout(1000)

        # Step 4
        await page.locator("input[type='text']").first.fill(f"QC-WARN-{uuid.uuid4().hex[:4].upper()}")
        await page.locator("input[type='date']").nth(0).fill("2026-08-09")
        await page.locator("input[type='date']").nth(1).fill("2026-09-06")
        await page.locator("input[type='number']").nth(0).fill("30.8")
        await page.locator("input[type='number']").nth(1).fill("51.3")
        await page.locator("button:has-text('Save Step 4')").click()
        await page.wait_for_timeout(2500)

        ts = int(time.time()*1000)
        path = os.path.join(SCREENSHOT_DIR, f"media_{ts}_scenario_e.png")
        await page.screenshot(path=path)
        print(f"Captured Scenario E: {path}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_scenario_e_wb())
