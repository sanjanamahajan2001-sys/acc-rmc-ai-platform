import asyncio
import os
import time
import urllib.request
import json
from playwright.async_api import async_playwright

SCREENSHOT_DIR = "/mnt/c/Users/acer/.gemini/antigravity/brain/4fe36a86-34a3-44c5-8725-e56313d016b4/.user_uploaded"

def create_seeded_draft_in_memory(s3_overrides={}, s4_overrides={}):
    import uuid
    # Step 1
    req1 = urllib.request.Request("http://localhost:8005/api/v1/manual-entry/drafts", data=json.dumps({
        "plant_code": "PLANT-MUMBAI-01",
        "recipe_code": "M40_VW_UT_ISOLATED",
        "production_date": "2026-08-09",
        "shift": "DAY"
    }).encode('utf-8'), headers={'Content-Type': 'application/json'})
    resp1 = urllib.request.urlopen(req1)
    d_id = json.loads(resp1.read().decode('utf-8'))["draft_id"]

    # Step 2
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

    # Step 3
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

    # Step 4
    s4_data = {
        "qa_cube_id": f"QC-SEED-{uuid.uuid4().hex[:6].upper()}",
        "lab_technician_id": "TECH-MUM-01",
        "lab_technician_name": "Rahul Kumar",
        "casting_date": "2026-08-09",
        "testing_date_28_day": "2026-09-06",
        "result_7_day_mpa": 30.8,
        "result_28_day_mpa": 51.3,
        "failure_reason_code": "NONE",
        "laboratory_remarks": "Standard 28-day water curing completed."
    }
    s4_data.update(s4_overrides)
    req4 = urllib.request.Request(f"http://localhost:8005/api/v1/manual-entry/drafts/{d_id}/step-4", data=json.dumps(s4_data).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='PUT')
    try:
        urllib.request.urlopen(req4)
    except Exception:
        pass

    return d_id

async def render_step5_for_draft(draft_id, name):
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1400, "height": 900})

        # Inject script to open draft modal at step 5 directly
        await page.goto("http://localhost:5173")
        await page.wait_for_timeout(1000)

        # Execute JS to open modal with draft_id and set step to 5
        js_code = f"""
        window.localStorage.setItem('active_draft_id', '{draft_id}');
        """
        await page.evaluate(js_code)

        # Open modal
        await page.locator("button:has-text('Manual Production Entry')").click()
        await page.wait_for_timeout(1000)

        # Fill steps 1..4 normally or click forward if populated
        await page.locator("select").first.select_option(index=1)
        await page.locator("select").nth(1).select_option(index=1)
        await page.locator("button:has-text('Proceed')").click()
        await page.wait_for_timeout(500)

        # Step 2
        await page.locator("button:has-text('Proceed')").click()
        await page.wait_for_timeout(500)

        # Step 3
        await page.locator("button:has-text('Proceed')").click()
        await page.wait_for_timeout(500)

        # Step 4
        save_btn = page.locator("button:has-text('Save Step 4')")
        if await save_btn.is_enabled():
            await save_btn.click()
            await page.wait_for_timeout(2000)
        else:
            # Force navigation to Step 5 tab if active
            await page.locator("text=5. Quality Checks").click()
            await page.wait_for_timeout(2000)

        ts = int(time.time()*1000)
        path = os.path.join(SCREENSHOT_DIR, f"media_{ts}_{name}.png")
        await page.screenshot(path=path)
        print(f"Captured {name}: {path}")

        await browser.close()

async def main():
    # Scenario E: W/B 0.52 Warning
    d5 = create_seeded_draft_in_memory(s3_overrides={"water_kg_m3": 234.0}) # W/B = 234 / 450 = 0.52
    await render_step5_for_draft(d5, "scenario_e_wb_warning")

    # Scenario C: Strength deficit 35 MPa
    d3 = create_seeded_draft_in_memory(s4_overrides={"result_28_day_mpa": 35.0})
    await render_step5_for_draft(d3, "scenario_c_strength_deficit")

    # Scenario D: Failure Reason CURING_ISSUE
    d4 = create_seeded_draft_in_memory(s4_overrides={"failure_reason_code": "CURING_ISSUE", "failure_reason_text": "Water bath temp excursion"})
    await render_step5_for_draft(d4, "scenario_d_failure_reason")

if __name__ == "__main__":
    asyncio.run(main())
