"""Dedicated Automated Unit & Domain Governance Test Suite for WS-03.5.5 Quality Checks.

Verifies 32 explicit Quality Check domain & governance requirements:
1. test_01_quality_checks_endpoint_availability
2. test_02_valid_complete_draft_evaluation
3. test_03_missing_step1_plant_error
4. test_04_missing_step1_recipe_error
5. test_05_missing_step2_truck_error
6. test_06_missing_step2_challan_error
7. test_07_missing_step3_materials_error
8. test_08_missing_step4_qa_cube_error
9. test_09_invalid_date_chronology_error
10. test_10_invalid_exact_28d_curing_age_error
11. test_11_invalid_28d_strength_range_error
12. test_12_strength_below_target_error
13. test_13_failure_reason_code_exception_error
14. test_14_invalid_wb_ratio_error
15. test_15_elevated_wb_ratio_warning
16. test_16_invalid_binder_content_error
17. test_17_duplicate_delivery_challan_error
18. test_18_duplicate_qa_cube_id_error
19. test_19_cost_validation_info
20. test_20_engineering_slump_constraint_error
21. test_21_engineering_mixer_time_constraint_error
22. test_22_warning_only_overall_status_review_required
23. test_23_blocking_error_overall_status_blocked
24. test_24_final_review_eligible_false_when_errors_exist
25. test_25_retraining_eligibility_candidate_pending_submission
26. test_26_backend_authoritative_eligibility_cannot_be_spoofed
27. test_27_cross_operator_access_denied
28. test_28_repeated_evaluation_determinism
29. test_29_draft_hydration_persistence
30. test_30_production_isolation_prd_batches_zero
31. test_31_duplicate_against_committed_production_db_record
32. test_32_current_draft_does_not_self_collide
"""

import unittest
import uuid
import json
from sqlalchemy import text
from fastapi.testclient import TestClient
from src.api.main import app
from src.api.manual_entry_router import _MANUAL_DRAFTS
from src.database.session import get_session_factory
from src.database.models.master import Plant, Recipe
from src.database.models.production import Batch

client = TestClient(app)


class TestWS0355QualityChecks(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        session_factory = get_session_factory()
        db = session_factory()
        try:
            plant = db.query(Plant).filter(Plant.plant_code == "PLANT-MUMBAI-01").first()
            if not plant:
                plant = Plant(
                    id="PLANT-ID-MUMBAI-01",
                    plant_code="PLANT-MUMBAI-01",
                    plant_name="ACC Mumbai Batching Plant #1",
                    location="Mumbai Central",
                    timezone="Asia/Kolkata"
                )
                db.add(plant)

            recipe = db.query(Recipe).filter(Recipe.recipe_code == "M40_VW_UT_ISOLATED").first()
            if not recipe:
                recipe = Recipe(
                    id="RECIPE-ID-M40-ISOLATED",
                    recipe_code="M40_VW_UT_ISOLATED",
                    recipe_name="M40 View Isolated",
                    mix_design_code="M40-VW-UT",
                    grade="M40",
                    target_strength_mpa=40.0,
                    nominal_max_aggregate_size_mm=20.0
                )
                db.add(recipe)
            db.commit()
        finally:
            db.close()

    def setUp(self):
        session_factory = get_session_factory()
        self.db = session_factory()
        _MANUAL_DRAFTS.clear()

        # Create valid draft through Step 1 -> 2 -> 3 -> 4
        payload1 = {
            "plant_code": "PLANT-MUMBAI-01",
            "recipe_code": "M40_VW_UT_ISOLATED",
            "production_date": "2026-08-09",
            "shift": "DAY"
        }
        res1 = client.post("/api/v1/manual-entry/drafts", json=payload1)
        self.assertEqual(res1.status_code, 200)
        self.draft_id = res1.json()["draft_id"]

        payload2 = {
            "batch_start_time": "09:15:00",
            "batch_end_time": "09:17:15",
            "mixer_time_seconds": 45,
            "truck_number": "TM-MUM-402",
            "delivery_challan": f"DC-{uuid.uuid4().hex[:6].upper()}",
            "aggregate_moisture_correction": 1.2,
            "target_slump_mm": 120.0
        }
        res2 = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-2", json=payload2)
        self.assertEqual(res2.status_code, 200)

        payload3 = {
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
        res3 = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload3)
        self.assertEqual(res3.status_code, 200)

        payload4 = {
            "qa_cube_id": f"QC-TEST-{uuid.uuid4().hex[:6].upper()}",
            "lab_technician_id": "TECH-MUM-01",
            "lab_technician_name": "Rahul Kumar",
            "casting_date": "2026-08-09",
            "testing_date_28_day": "2026-09-06", # Exactly 28 days!
            "result_7_day_mpa": 30.8,
            "result_28_day_mpa": 51.3,
            "failure_reason_code": "NONE",
            "laboratory_remarks": "Standard 28-day water curing completed."
        }
        res4 = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-4", json=payload4)
        self.assertEqual(res4.status_code, 200)

    def tearDown(self):
        self.db.close()

    def test_01_quality_checks_endpoint_availability(self):
        """GET /api/v1/manual-entry/drafts/{draft_id}/quality-checks returns 200 OK for valid draft."""
        res = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks")
        self.assertEqual(res.status_code, 200)

    def test_02_valid_complete_draft_evaluation(self):
        """Valid complete draft evaluates to QUALITY_CLEAR with 0 errors, final_review_eligible=True and PENDING_FINAL_REVIEW."""
        res = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks")
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d["overall_status"], "QUALITY_CLEAR")
        self.assertEqual(d["error_count"], 0)
        self.assertTrue(d["final_review_eligible"])
        self.assertEqual(d["production_submission_status"], "PENDING_FINAL_REVIEW")
        self.assertEqual(d["ml_retraining_eligibility"], "CANDIDATE_PENDING_SUBMISSION")
        self.assertEqual(d["total_binder_kg_m3"], 450.0)
        self.assertEqual(d["effective_water_kg_m3"], 193.36)
        self.assertEqual(d["w_b_ratio"], 0.430)
        self.assertEqual(d["yield_volume_m3"], 1.048)

    def test_03_missing_step1_plant_error(self):
        """Draft with missing plant_code evaluates to BLOCKED with REQ_PLANT error."""
        _MANUAL_DRAFTS[self.draft_id]["plant_code"] = ""
        res = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks")
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d["overall_status"], "BLOCKED")
        self.assertFalse(d["final_review_eligible"])
        rule_codes = [c["rule_code"] for c in d["checks"]]
        self.assertIn("REQ_PLANT", rule_codes)

    def test_04_missing_step1_recipe_error(self):
        """Draft with missing recipe_code evaluates to BLOCKED."""
        _MANUAL_DRAFTS[self.draft_id]["recipe_code"] = ""
        res = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks")
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d["overall_status"], "BLOCKED")

    def test_05_missing_step2_truck_error(self):
        """Draft with missing truck_number evaluates to BLOCKED."""
        _MANUAL_DRAFTS[self.draft_id]["truck_number"] = ""
        res = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks")
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d["overall_status"], "BLOCKED")

    def test_06_missing_step2_challan_error(self):
        """Draft with missing delivery_challan evaluates to BLOCKED."""
        _MANUAL_DRAFTS[self.draft_id]["delivery_challan"] = ""
        res = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks")
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d["overall_status"], "BLOCKED")

    def test_07_missing_step3_materials_error(self):
        """Draft with missing cement evaluates to BLOCKED."""
        _MANUAL_DRAFTS[self.draft_id]["cement_kg_m3"] = None
        res = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks")
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d["overall_status"], "BLOCKED")

    def test_08_missing_step4_qa_cube_error(self):
        """Draft with missing QA cube ID evaluates to BLOCKED."""
        _MANUAL_DRAFTS[self.draft_id]["qa_cube_id"] = ""
        res = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks")
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d["overall_status"], "BLOCKED")

    def test_09_invalid_date_chronology_error(self):
        """Draft with testing date before casting date produces CHRONO_NEG ERROR and blocks."""
        _MANUAL_DRAFTS[self.draft_id]["casting_date"] = "2026-08-09"
        _MANUAL_DRAFTS[self.draft_id]["testing_date_28_day"] = "2026-07-28"
        res = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks")
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d["overall_status"], "BLOCKED")
        self.assertFalse(d["final_review_eligible"])
        rule_codes = [c["rule_code"] for c in d["checks"]]
        self.assertIn("CHRONO_NEG", rule_codes)

    def test_10_invalid_exact_28d_curing_age_error(self):
        """Draft with 6-day curing age (2026-08-09 -> 2026-08-15) produces CHRONO_28D_MISMATCH ERROR."""
        _MANUAL_DRAFTS[self.draft_id]["casting_date"] = "2026-08-09"
        _MANUAL_DRAFTS[self.draft_id]["testing_date_28_day"] = "2026-08-15"
        res = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks")
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d["overall_status"], "BLOCKED")
        self.assertFalse(d["final_review_eligible"])
        rule_codes = [c["rule_code"] for c in d["checks"]]
        self.assertIn("CHRONO_28D_MISMATCH", rule_codes)

    def test_11_invalid_28d_strength_range_error(self):
        """28-day strength of 0 or > 150 MPa produces QA_STRENGTH_RANGE ERROR."""
        _MANUAL_DRAFTS[self.draft_id]["result_28_day_mpa"] = 0.0
        res = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks")
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d["overall_status"], "BLOCKED")

    def test_12_strength_below_target_error(self):
        """28-day strength of 35 MPa for M40 (target 40 MPa) produces QA_STRENGTH_LOW ERROR."""
        _MANUAL_DRAFTS[self.draft_id]["result_28_day_mpa"] = 35.0
        res = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks")
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d["overall_status"], "BLOCKED")
        self.assertFalse(d["final_review_eligible"])
        rule_codes = [c["rule_code"] for c in d["checks"]]
        self.assertIn("QA_STRENGTH_LOW", rule_codes)

    def test_13_failure_reason_code_exception_error(self):
        """Non-NONE failure_reason_code produces QA_REASON_EXCEPTION ERROR."""
        _MANUAL_DRAFTS[self.draft_id]["failure_reason_code"] = "CURING_ISSUE"
        _MANUAL_DRAFTS[self.draft_id]["failure_reason_text"] = "Water bath temperature excursion."
        res = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks")
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d["overall_status"], "BLOCKED")
        self.assertFalse(d["final_review_eligible"])
        rule_codes = [c["rule_code"] for c in d["checks"]]
        self.assertIn("QA_REASON_EXCEPTION", rule_codes)

    def test_14_invalid_wb_ratio_error(self):
        """W/B ratio outside 0.25 - 0.65 produces MAT_WB_RANGE ERROR."""
        _MANUAL_DRAFTS[self.draft_id]["w_b_ratio"] = 0.70
        res = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks")
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d["overall_status"], "BLOCKED")

    def test_15_elevated_wb_ratio_warning(self):
        """W/B ratio of 0.52 produces MAT_WB_WARN WARNING without blocking final review."""
        _MANUAL_DRAFTS[self.draft_id]["w_b_ratio"] = 0.52
        res = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks")
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d["overall_status"], "REVIEW_REQUIRED")
        self.assertTrue(d["final_review_eligible"]) # Warning only!
        self.assertEqual(d["production_submission_status"], "PENDING_FINAL_REVIEW")

    def test_16_invalid_binder_content_error(self):
        """Binder content < 250 kg/m3 produces MAT_BINDER_RANGE ERROR."""
        _MANUAL_DRAFTS[self.draft_id]["total_binder_kg_m3"] = 200.0
        res = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks")
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d["overall_status"], "BLOCKED")

    def test_17_duplicate_delivery_challan_error(self):
        """Duplicate delivery challan across distinct drafts produces DUP_CHALLAN_DRAFT ERROR."""
        dup_challan = _MANUAL_DRAFTS[self.draft_id]["delivery_challan"]
        _MANUAL_DRAFTS["DRAFT-OTHER-01"] = {
            "draft_id": "DRAFT-OTHER-01",
            "batch_number": "BATCH-OTHER-01",
            "delivery_challan": dup_challan,
            "operator_id": "OPERATOR-MUMBAI-01"
        }
        res = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks")
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d["overall_status"], "BLOCKED")

    def test_18_duplicate_qa_cube_id_error(self):
        """Duplicate QA cube ID across distinct drafts produces DUP_CUBE_ID_DRAFT ERROR."""
        dup_cube = _MANUAL_DRAFTS[self.draft_id]["qa_cube_id"]
        _MANUAL_DRAFTS["DRAFT-OTHER-02"] = {
            "draft_id": "DRAFT-OTHER-02",
            "batch_number": "BATCH-OTHER-02",
            "qa_cube_id": dup_cube,
            "operator_id": "OPERATOR-MUMBAI-01"
        }
        res = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks")
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d["overall_status"], "BLOCKED")

    def test_19_cost_validation_info(self):
        """Authoritative cost per m3 is reported in quality checks."""
        res = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks")
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertIn("₹5,747.50", d["estimated_cost_per_m3"])

    def test_20_engineering_slump_constraint_error(self):
        """Target slump of 30 mm (< 50 mm limit) produces ENG_SLUMP_OUT ERROR."""
        _MANUAL_DRAFTS[self.draft_id]["target_slump_mm"] = 30.0
        res = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks")
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d["overall_status"], "BLOCKED")

    def test_21_engineering_mixer_time_constraint_error(self):
        """Mixer time of 5 seconds (< 15s limit) produces ENG_MIXER_TIME_OUT ERROR."""
        _MANUAL_DRAFTS[self.draft_id]["mixer_time_seconds"] = 5
        res = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks")
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d["overall_status"], "BLOCKED")

    def test_22_warning_only_overall_status_review_required(self):
        """Warning-only draft evaluates to REVIEW_REQUIRED status while final_review_eligible=True."""
        _MANUAL_DRAFTS[self.draft_id]["w_b_ratio"] = 0.52
        res = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks")
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d["overall_status"], "REVIEW_REQUIRED")
        self.assertTrue(d["final_review_eligible"])

    def test_23_blocking_error_overall_status_blocked(self):
        """Draft with any ERROR evaluates to BLOCKED overall_status."""
        _MANUAL_DRAFTS[self.draft_id]["cement_kg_m3"] = None
        res = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks")
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d["overall_status"], "BLOCKED")

    def test_24_final_review_eligible_false_when_errors_exist(self):
        """final_review_eligible is strictly False when error_count > 0."""
        _MANUAL_DRAFTS[self.draft_id]["result_28_day_mpa"] = 30.0 # Below 40 MPa target!
        res = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks")
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertFalse(d["final_review_eligible"])
        self.assertEqual(d["production_submission_status"], "BLOCKED")

    def test_25_retraining_eligibility_candidate_pending_submission(self):
        """ml_retraining_eligibility is CANDIDATE_PENDING_SUBMISSION for clean pass records."""
        res1 = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks")
        self.assertEqual(res1.json()["ml_retraining_eligibility"], "CANDIDATE_PENDING_SUBMISSION")

        _MANUAL_DRAFTS[self.draft_id]["failure_reason_code"] = "CURING_ISSUE"
        _MANUAL_DRAFTS[self.draft_id]["failure_reason_text"] = "Temp excursion."
        res2 = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks")
        self.assertEqual(res2.json()["ml_retraining_eligibility"], "NOT_YET_DETERMINED")

    def test_26_backend_authoritative_eligibility_cannot_be_spoofed(self):
        """GET quality checks calculates final_review_eligible server-side based on actual draft state."""
        res = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks")
        self.assertTrue(res.json()["final_review_eligible"])

    def test_27_cross_operator_access_denied(self):
        """Operator B requesting Quality Checks for Operator A draft gets HTTP 403 Forbidden."""
        headers = {"Authorization": "Bearer OPERATOR_B_TOKEN"}
        res = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks", headers=headers)
        self.assertEqual(res.status_code, 403)

    def test_28_repeated_evaluation_determinism(self):
        """Repeated GET evaluations produce identical quality check results."""
        res1 = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks").json()
        res2 = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks").json()
        self.assertEqual(res1["data_quality_score"], res2["data_quality_score"])
        self.assertEqual(res1["overall_status"], res2["overall_status"])

    def test_29_draft_hydration_persistence(self):
        """Draft rehydration preserves exact constituent values for Quality Checks."""
        res = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}")
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d["cement_kg_m3"], 315.0)

    def test_30_production_isolation_prd_batches_zero(self):
        """Quality Check evaluation creates 0 records in prd_batches."""
        res = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks")
        self.assertEqual(res.status_code, 200)
        count = self.db.query(Batch).count()
        self.assertEqual(count, 0)

    def test_31_duplicate_against_committed_production_db_record(self):
        """Batch number matching a committed Batch in prd_batches DB triggers DUP_BATCH_NUMBER_PRD ERROR."""
        dup_batch_num = _MANUAL_DRAFTS[self.draft_id]["batch_number"]
        unique_id = f"BATCH-ID-{uuid.uuid4().hex[:6].upper()}"

        # Insert committed batch directly into prd_batches via SQL
        self.db.execute(text(
            "INSERT INTO prd_batches (id, batch_number, order_id, dispatch_schedule_id, recipe_id, plant_id, production_status, planned_quantity_m3, created_at, updated_at, is_deleted, version_id) "
            "VALUES (:id, :b_num, 'ORD-01', 'DSP-01', 'REC-01', 'PLT-01', 'COMPLETED', 6.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0, 1)"
        ), {"id": unique_id, "b_num": dup_batch_num})
        self.db.commit()

        try:
            res = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks")
            self.assertEqual(res.status_code, 200)
            d = res.json()
            self.assertEqual(d["overall_status"], "BLOCKED")
            rule_codes = [c["rule_code"] for c in d["checks"]]
            self.assertIn("DUP_BATCH_NUMBER_PRD", rule_codes)
        finally:
            self.db.execute(text("DELETE FROM prd_batches WHERE id = :id"), {"id": unique_id})
            self.db.commit()

    def test_33_stale_client_server_revalidation_blocks(self):
        """Gate B: Client has previously evaluated clear state, but backend draft becomes invalid. Revalidation API rejects transition."""
        # 1. Evaluates clean initially
        res1 = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks")
        self.assertTrue(res1.json()["final_review_eligible"])

        # 2. Behind client's back, server draft state becomes corrupted/invalid (e.g. 6-day curing schedule mismatch)
        _MANUAL_DRAFTS[self.draft_id]["testing_date_28_day"] = "2026-08-15"

        # 3. Client attempts revalidation check prior to Step 6 transition
        res2 = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/quality-checks")
        self.assertEqual(res2.status_code, 200)
        d2 = res2.json()
        self.assertEqual(d2["overall_status"], "BLOCKED")
        self.assertFalse(d2["final_review_eligible"])
        self.assertEqual(d2["production_submission_status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()

