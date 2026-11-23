import asyncio
import os
import sys
import time
import uuid
import urllib.request
import json
from playwright.async_api import async_playwright

sys.path.append("/home/sanjana/acc-rmc-ai-platform")
from src.api.manual_entry_router import _MANUAL_DRAFTS

SCREENSHOT_DIR = "/mnt/c/Users/acer/.gemini/antigravity/brain/4fe36a86-34a3-44c5-8725-e56313d016b4/.user_uploaded"

def seed_draft_via_backend(s3_overrides={}):
    req1 = urllib.request.Request("http://localhost:8005/api/v1/manual-entry/drafts", data=json.dumps({
        "plant_code": "PLANT-MUMBAI-01",
        "recipe_code": "M40_VW_UT_ISOLATED",
        "production_date": "2026-08-09",
        "shift": "DAY"
    }).encode('utf-8'), headers={'Content-Type': 'application/json'})
    resp1 = urllib.request.urlopen(req1)
    d_id = json.loads(resp1.read().decode('utf-8'))["draft_id"]

    req2 = urllib.request.Request(f"http://localhost:8005/api/v1/manual-entry/drafts/{d_id}/step-2", data=json.dumps({
        "batch_start_time": "09:15:00",
        "batch_end_time": "09:17:15",
        "mixer_time_seconds": 45,
        "truck_number": "TM-MUM-402",
        "delivery_challan": f"DC-{uuid.uuid4().hex[:6].upper()}",
        "aggregate_moisture_correction": 1.2,
        "target_slump_mm": 120.0
    }).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='PUT')
    urllib.request.urlopen(req2)

    s3_data = {
        "cement_kg_m3": 315.0,
        "fly_ash_kg_m3": 0.0,
        "ggbs_kg_m3": 135.0,
        "water_kg_m3": 160.0,
        "admixture_kg_m3": 3.8,
        "fine_aggregate_kg_m3": 780.0,
        "coarse_aggregate_kg_m3": 1080.0,
        "fine_aggregate_moisture_pct": 2.0,
        "fine_aggregate_absorption_pct": 1.0,
        "coarse_aggregate_moisture_pct": 0.8,
        "coarse_aggregate_absorption_pct": 0.5
    }
    s3_data.update(s3_overrides)
    req3 = urllib.request.Request(f"http://localhost:8005/api/v1/manual-entry/drafts/{d_id}/step-3", data=json.dumps(s3_data).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='PUT')
    urllib.request.urlopen(req3)

    return d_id

async def capture_scenario_f_revalidation():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # PASS PATH: Clean draft -> click Next -> Step 6
        print("Capturing Scenario F Pass Path (Step 5 -> Step 6 transition)...")
        page_pass = await browser.new_page(viewport={"width": 1400, "height": 900})
        await page_pass.goto("http://localhost:5173")
        await page_pass.wait_for_timeout(1000)
        await page_pass.locator("button:has-text('Manual Production Entry')").click()
        await page_pass.wait_for_timeout(1000)
        await page_pass.locator("select").first.select_option(index=1)
        await page_pass.locator("select").nth(1).select_option(value="M40_VW_UT_ISOLATED")
        await page_pass.locator("button:has-text('Proceed')").click()
        await page_pass.wait_for_timeout(500)
        await page_pass.locator("input[type='text']").nth(0).fill("TM-MUM-402")
        await page_pass.locator("input[type='text']").nth(1).fill(f"DC-{uuid.uuid4().hex[:6].upper()}")
        await page_pass.locator("button:has-text('Proceed')").click()
        await page_pass.wait_for_timeout(500)
        await page_pass.locator("button:has-text('Proceed')").click()
        await page_pass.wait_for_timeout(500)

        await page_pass.locator("input[type='text']").first.fill(f"QC-PASS-{uuid.uuid4().hex[:4].upper()}")
        await page_pass.locator("input[type='date']").nth(0).fill("2026-08-09")
        await page_pass.locator("input[type='date']").nth(1).fill("2026-09-06")
        await page_pass.locator("input[type='number']").nth(0).fill("30.8")
        await page_pass.locator("input[type='number']").nth(1).fill("51.3")
        await page_pass.locator("button:has-text('Save Step 4')").click()
        await page_pass.wait_for_timeout(2000)

        # On Step 5, click Next: Final Review & Submit ->
        next_btn = page_pass.locator("button:has-text('Next: Final Review & Submit')")
        await next_btn.click()
        await page_pass.wait_for_timeout(2500)

        ts_f1 = int(time.time()*1000)
        path_f1 = os.path.join(SCREENSHOT_DIR, f"media_{ts_f1}_scenario_f_step6_allowed.png")
        await page_pass.screenshot(path=path_f1)
        print(f"Captured Scenario F Step 6 Allowed: {path_f1}")
        await page_pass.close()

        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_scenario_f_revalidation())
