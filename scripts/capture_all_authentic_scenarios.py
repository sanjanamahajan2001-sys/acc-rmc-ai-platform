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

def seed_draft_via_backend(s3_overrides={}, s4_overrides={}):
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

async def render_step5_directly(page, draft_id):
    await page.goto("http://localhost:5173")
    await page.wait_for_timeout(1000)
    await page.locator("button:has-text('Manual Production Entry')").click()
    await page.wait_for_timeout(1000)

    # Step 1 -> Step 2
    await page.locator("select").first.select_option(index=1)
    await page.locator("select").nth(1).select_option(value="M40_VW_UT_ISOLATED")
    await page.locator("button:has-text('Proceed')").click()
    await page.wait_for_timeout(500)

    # Step 2 -> Step 3
    await page.locator("input[type='text']").nth(0).fill("TM-MUM-402")
    await page.locator("input[type='text']").nth(1).fill(f"DC-{uuid.uuid4().hex[:6].upper()}")
    await page.locator("button:has-text('Proceed')").click()
    await page.wait_for_timeout(500)

    # Step 3 -> Step 4
    await page.locator("button:has-text('Proceed')").click()
    await page.wait_for_timeout(500)

    # Execute JS to update active draft object in modal state to draft_id and set currentStep to 5
    js = f"""
    fetch('http://localhost:8005/api/v1/manual-entry/drafts/{draft_id}')
      .then(res => res.json())
      .then(data => {{
        window.localStorage.setItem('active_draft_id', '{draft_id}');
      }});
    """
    await page.evaluate(js)

    # Click Step 5 tab if completed or force navigate via Save Step 4 if valid
    save_btn = page.locator("button:has-text('Save Step 4')")
    if await save_btn.is_enabled():
        await save_btn.click()
        await page.wait_for_timeout(2000)
    else:
        # Save button disabled because of invalid 6-day curing; force navigation to Step 5 tab
        await page.locator("text=5. Quality Checks").click()
        await page.wait_for_timeout(2500)

async def capture_all_authentic_scenarios():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # --- SCENARIO B: Invalid 6-Day Curing (6 Days actual age) ---
        print("Capturing Scenario B (6-Day Curing Schedule Mismatch)...")
        d_b_id = seed_draft_via_backend()
        d_b = _MANUAL_DRAFTS.get(d_b_id)
        if d_b:
            d_b['qa_cube_id'] = f"QC-6DAY-{uuid.uuid4().hex[:4].upper()}"
            d_b['lab_technician_id'] = "TECH-MUM-01"
            d_b['lab_technician_name'] = "Rahul Kumar"
            d_b['casting_date'] = "2026-08-09"
            d_b['testing_date_28_day'] = "2026-08-15" # 6 days!
            d_b['result_7_day_mpa'] = 30.8
            d_b['result_28_day_mpa'] = 51.3
            d_b['failure_reason_code'] = "NONE"
            d_b['laboratory_remarks'] = "Standard water curing verified."

        page_b = await browser.new_page(viewport={"width": 1400, "height": 900})
        await page_b.goto("http://localhost:5173")
        await page_b.wait_for_timeout(1000)
        await page_b.locator("button:has-text('Manual Production Entry')").click()
        await page_b.wait_for_timeout(1000)
        # Step 1
        await page_b.locator("select").first.select_option(index=1)
        await page_b.locator("select").nth(1).select_option(value="M40_VW_UT_ISOLATED")
        await page_b.locator("button:has-text('Proceed')").click()
        await page_b.wait_for_timeout(500)
        # Step 2
        await page_b.locator("input[type='text']").nth(0).fill("TM-MUM-402")
        await page_b.locator("input[type='text']").nth(1).fill(f"DC-{uuid.uuid4().hex[:6].upper()}")
        await page_b.locator("button:has-text('Proceed')").click()
        await page_b.wait_for_timeout(500)
        # Step 3
        await page_b.locator("button:has-text('Proceed')").click()
        await page_b.wait_for_timeout(500)

        # Step 4: Fill 6-day date in UI to trigger Step 4 error banner
        await page_b.locator("input[type='text']").first.fill(f"QC-6DAY-{uuid.uuid4().hex[:4].upper()}")
        await page_b.locator("input[type='date']").nth(0).fill("2026-08-09")
        await page_b.locator("input[type='date']").nth(1).fill("2026-08-15") # 6 days
        await page_b.locator("input[type='number']").nth(0).fill("30.8")
        await page_b.locator("input[type='number']").nth(1).fill("51.3")
        await page_b.wait_for_timeout(1500)

        ts_b = int(time.time()*1000)
        path_b = os.path.join(SCREENSHOT_DIR, f"media_{ts_b}_scenario_b_6day.png")
        await page_b.screenshot(path=path_b)
        print(f"Captured Scenario B: {path_b}")
        await page_b.close()

        # --- SCENARIO C: Compressive Strength Failure (35.0 MPa vs 40.0 target) ---
        print("Capturing Scenario C (Strength Deficit -5.0 MPa)...")
        d_c_id = seed_draft_via_backend()
        d_c = _MANUAL_DRAFTS.get(d_c_id)
        if d_c:
            d_c['qa_cube_id'] = f"QC-LOW-{uuid.uuid4().hex[:4].upper()}"
            d_c['lab_technician_id'] = "TECH-MUM-01"
            d_c['lab_technician_name'] = "Rahul Kumar"
            d_c['casting_date'] = "2026-08-09"
            d_c['testing_date_28_day'] = "2026-09-06"
            d_c['result_7_day_mpa'] = 30.8
            d_c['result_28_day_mpa'] = 35.0 # Deficit -5.0 MPa
            d_c['failure_reason_code'] = "NONE"
            d_c['laboratory_remarks'] = "Standard water curing verified."

        page_c = await browser.new_page(viewport={"width": 1400, "height": 900})
        await page_c.goto("http://localhost:5173")
        await page_c.wait_for_timeout(1000)
        await page_c.locator("button:has-text('Manual Production Entry')").click()
        await page_c.wait_for_timeout(1000)
        await page_c.locator("select").first.select_option(index=1)
        await page_c.locator("select").nth(1).select_option(value="M40_VW_UT_ISOLATED")
        await page_c.locator("button:has-text('Proceed')").click()
        await page_c.wait_for_timeout(500)
        await page_c.locator("input[type='text']").nth(0).fill("TM-MUM-402")
        await page_c.locator("input[type='text']").nth(1).fill(f"DC-{uuid.uuid4().hex[:6].upper()}")
        await page_c.locator("button:has-text('Proceed')").click()
        await page_c.wait_for_timeout(500)
        await page_c.locator("button:has-text('Proceed')").click()
        await page_c.wait_for_timeout(500)

        # Step 4: Strength 35.0 MPa (< 40.0 MPa target)
        await page_c.locator("input[type='text']").first.fill(f"QC-LOW-{uuid.uuid4().hex[:4].upper()}")
        await page_c.locator("input[type='date']").nth(0).fill("2026-08-09")
        await page_c.locator("input[type='date']").nth(1).fill("2026-09-06")
        await page_c.locator("input[type='number']").nth(0).fill("30.8")
        await page_c.locator("input[type='number']").nth(1).fill("35.0")
        await page_c.locator("button:has-text('Save Step 4')").click()
        await page_c.wait_for_timeout(2000)
        await page_c.locator("text=5. Quality Checks").click()
        await page_c.wait_for_timeout(2500)

        ts_c = int(time.time()*1000)
        path_c = os.path.join(SCREENSHOT_DIR, f"media_{ts_c}_scenario_c_strength.png")
        await page_c.screenshot(path=path_c)
        print(f"Captured Scenario C: {path_c}")
        await page_c.close()

        # --- SCENARIO D: Failure Reason Code (CURING_ISSUE) ---
        print("Capturing Scenario D (Failure Reason Exception CURING_ISSUE)...")
        d_d_id = seed_draft_via_backend()
        d_d = _MANUAL_DRAFTS.get(d_d_id)
        if d_d:
            d_d['qa_cube_id'] = f"QC-CURING-{uuid.uuid4().hex[:4].upper()}"
            d_d['lab_technician_id'] = "TECH-MUM-01"
            d_d['lab_technician_name'] = "Rahul Kumar"
            d_d['casting_date'] = "2026-08-09"
            d_d['testing_date_28_day'] = "2026-09-06"
            d_d['result_7_day_mpa'] = 30.8
            d_d['result_28_day_mpa'] = 51.3
            d_d['failure_reason_code'] = "CURING_ISSUE"
            d_d['failure_reason_text'] = "Water bath temperature excursion during curing phase."
            d_d['laboratory_remarks'] = "Curing temperature non-conformance recorded."

        page_d = await browser.new_page(viewport={"width": 1400, "height": 900})
        await page_d.goto("http://localhost:5173")
        await page_d.wait_for_timeout(1000)
        await page_d.locator("button:has-text('Manual Production Entry')").click()
        await page_d.wait_for_timeout(1000)
        await page_d.locator("select").first.select_option(index=1)
        await page_d.locator("select").nth(1).select_option(value="M40_VW_UT_ISOLATED")
        await page_d.locator("button:has-text('Proceed')").click()
        await page_d.wait_for_timeout(500)
        await page_d.locator("input[type='text']").nth(0).fill("TM-MUM-402")
        await page_d.locator("input[type='text']").nth(1).fill(f"DC-{uuid.uuid4().hex[:6].upper()}")
        await page_d.locator("button:has-text('Proceed')").click()
        await page_d.wait_for_timeout(500)
        await page_d.locator("button:has-text('Proceed')").click()
        await page_d.wait_for_timeout(500)

        # Step 4: CURING_ISSUE failure reason
        await page_d.locator("input[type='text']").first.fill(f"QC-CURING-{uuid.uuid4().hex[:4].upper()}")
        await page_d.locator("input[type='date']").nth(0).fill("2026-08-09")
        await page_d.locator("input[type='date']").nth(1).fill("2026-09-06")
        await page_d.locator("input[type='number']").nth(0).fill("30.8")
        await page_d.locator("input[type='number']").nth(1).fill("51.3")
        await page_d.locator("select").first.select_option(value="CURING_ISSUE")

        reason_in = page_d.locator("input[placeholder*='Detail root cause'], input[placeholder*='root cause']")
        if await reason_in.count() > 0:
            await reason_in.fill("Water bath temperature excursion during curing phase.")
        else:
            await page_d.locator("input[type='text']").nth(3).fill("Water bath temperature excursion during curing phase.")

        await page_d.locator("button:has-text('Save Step 4')").click()
        await page_d.wait_for_timeout(2000)
        await page_d.locator("text=5. Quality Checks").click()
        await page_d.wait_for_timeout(2500)

        ts_d = int(time.time()*1000)
        path_d = os.path.join(SCREENSHOT_DIR, f"media_{ts_d}_scenario_d_reason.png")
        await page_d.screenshot(path=path_d)
        print(f"Captured Scenario D: {path_d}")
        await page_d.close()

        # --- SCENARIO E: Non-Blocking Warning (W/B ratio 0.596) ---
        print("Capturing Scenario E (Non-Blocking Warning W/B 0.596)...")
        page_e = await browser.new_page(viewport={"width": 1400, "height": 900})
        await page_e.goto("http://localhost:5173")
        await page_e.wait_for_timeout(1000)
        await page_e.locator("button:has-text('Manual Production Entry')").click()
        await page_e.wait_for_timeout(1000)
        await page_e.locator("select").first.select_option(index=1)
        await page_e.locator("select").nth(1).select_option(value="M40_VW_UT_ISOLATED")
        await page_e.locator("button:has-text('Proceed')").click()
        await page_e.wait_for_timeout(500)
        await page_e.locator("input[type='text']").nth(0).fill("TM-MUM-402")
        await page_e.locator("input[type='text']").nth(1).fill(f"DC-{uuid.uuid4().hex[:6].upper()}")
        await page_e.locator("button:has-text('Proceed')").click()
        await page_e.wait_for_timeout(500)

        # Step 3: Water = 268.36 kg/m3 (W/B = 0.596 > 0.50)
        await page_e.locator("input[type='number']").nth(3).fill("268.36")
        await page_e.locator("button:has-text('Proceed')").click()
        await page_e.wait_for_timeout(500)

        # Step 4
        await page_e.locator("input[type='text']").first.fill(f"QC-WARN-{uuid.uuid4().hex[:4].upper()}")
        await page_e.locator("input[type='date']").nth(0).fill("2026-08-09")
        await page_e.locator("input[type='date']").nth(1).fill("2026-09-06")
        await page_e.locator("input[type='number']").nth(0).fill("30.8")
        await page_e.locator("input[type='number']").nth(1).fill("51.3")
        await page_e.locator("button:has-text('Save Step 4')").click()
        await page_e.wait_for_timeout(2000)
        await page_e.locator("text=5. Quality Checks").click()
        await page_e.wait_for_timeout(2500)

        ts_e = int(time.time()*1000)
        path_e = os.path.join(SCREENSHOT_DIR, f"media_{ts_e}_scenario_e_warning.png")
        await page_e.screenshot(path=path_e)
        print(f"Captured Scenario E: {path_e}")
        await page_e.close()

        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_all_authentic_scenarios())
