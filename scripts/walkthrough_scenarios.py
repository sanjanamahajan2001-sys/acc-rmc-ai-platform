import asyncio
import os
import time
import uuid
from playwright.async_api import async_playwright

SCREENSHOT_DIR = "/mnt/c/Users/acer/.gemini/antigravity/brain/4fe36a86-34a3-44c5-8725-e56313d016b4/.user_uploaded"

async def run_scenario(name, fill_qa_func, fill_mix_func=None):
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1400, "height": 900})

        await page.goto("http://localhost:5173")
        await page.wait_for_timeout(2000)

        # Open Manual Entry Wizard
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

        # Step 3
        if fill_mix_func:
            await fill_mix_func(page)
        await page.locator("button:has-text('Proceed')").click()
        await page.wait_for_timeout(1000)

        # Step 4
        await page.locator("input[type='text']").first.fill(f"QC-{name.upper()}-{uuid.uuid4().hex[:4].upper()}")
        await fill_qa_func(page)

        save_btn = page.locator("button:has-text('Save Step 4')")
        if await save_btn.is_enabled():
            await save_btn.click()
            await page.wait_for_timeout(2500)

        # Capture Step 5 Screenshot
        ts = int(time.time()*1000)
        path = os.path.join(SCREENSHOT_DIR, f"media_{ts}_{name}.png")
        await page.screenshot(path=path)
        print(f"Captured {name}: {path}")

        await browser.close()

async def main():
    # Scenario E: Warning Case (Elevated W/B ratio ~ 0.51)
    async def fill_mix_warn(page):
        # We can leave mix design as standard or adjust
        pass
    async def fill_qa_warn(page):
        await page.locator("input[type='date']").nth(0).fill("2026-08-09")
        await page.locator("input[type='date']").nth(1).fill("2026-09-06")
        await page.locator("input[type='number']").nth(0).fill("30.8")
        await page.locator("input[type='number']").nth(1).fill("51.3")

    # Scenario B: Blocking Curing Age Mismatch (6-day curing)
    async def fill_qa_bad_curing(page):
        await page.locator("input[type='date']").nth(0).fill("2026-08-09")
        await page.locator("input[type='date']").nth(1).fill("2026-08-15") # 6 days!
        await page.locator("input[type='number']").nth(0).fill("30.8")
        await page.locator("input[type='number']").nth(1).fill("51.3")

    print("Running Scenario B (6-day curing error)...")
    await run_scenario("scenario_b_6day_curing", fill_qa_bad_curing)

if __name__ == "__main__":
    asyncio.run(main())
