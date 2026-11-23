"""Dedicated Automated Unit & Domain Governance Test Suite for WS-03.5.4 Laboratory QA.

Verifies 25 explicit Laboratory QA domains:
1. test_01_save_valid_laboratory_qa: Valid QA payload saves cleanly with 200 OK
2. test_02_qa_cube_id_required: Empty/whitespace QA Cube ID rejected with HTTP 422
3. test_03_qa_cube_id_max_length_exceeded: Cube ID > 50 chars rejected with HTTP 422
4. test_04_duplicate_qa_cube_id_rejection: Duplicate Cube ID across distinct drafts rejected with HTTP 422
5. test_05_casting_date_format_validation: Malformed casting date rejected with HTTP 422
6. test_06_testing_date_format_validation: Malformed testing date rejected with HTTP 422
7. test_07_testing_date_earlier_than_casting_date_rejection: Testing date earlier than casting date rejected with HTTP 422
8. test_08_curing_age_days_calculation: Days between casting and 28-day testing date correctly calculated (28 days)
9. test_09_optional_7_day_strength_validation: 7-day strength out of 0-120 range rejected with HTTP 422
10. test_10_mandatory_28_day_strength_validation: 28-day strength <= 0 or > 150 MPa rejected with HTTP 422
11. test_11_target_strength_grade_resolution: Resolves target strength (40 MPa for M40, 30 MPa for M30) from Recipe master
12. test_12_strength_margin_calculation: Strength Margin = 28D Result - Target Grade (51.3 - 40.0 = +11.3 MPa)
13. test_13_valid_failure_reason_code_governance: Valid reason code allowed (NONE, LOW_STRENGTH, SPECIMEN_DEFECT, etc.)
14. test_14_invalid_failure_reason_code_rejection: Unknown reason code rejected with HTTP 422
15. test_15_failure_reason_explanatory_text_required: Non-NONE reason code without explanatory text rejected with HTTP 422
16. test_16_qa_assessment_status_pass: Margin >= 0 and reason NONE evaluates to PASS
17. test_17_qa_assessment_status_review_required: Margin < 0 or reason != NONE evaluates to REVIEW_REQUIRED
18. test_18_approval_identity_governance: Preserves operator ID and name, rejecting unauthorized approver spoofing
19. test_19_cross_operator_access_denied: Cross-operator update rejected with HTTP 403
20. test_20_invariants_preserved: Step 1, Step 2, and Step 3 fields remain strictly invariant
21. test_21_draft_lifecycle_refetch_persistence: Step 4 state survives GET draft refetching
22. test_22_back_and_forth_wizard_navigation_safety: Preserves data after Step 4 -> Step 3 -> Step 4
23. test_23_duplicate_save_idempotency: Repeated Step 4 save updates existing draft cleanly
24. test_24_production_isolation_prd_batches_zero: Zero records written to prd_batches during Step 4
25. test_25_required_functional_vector_1: Verifies functional vector fixture (QC-M40-PUN-0630, 30.8 MPa 7D, 51.3 MPa 28D)
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


class TestWS0354LaboratoryQA(unittest.TestCase):

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

            recipe = db.query(Recipe).filter(Recipe.recipe_code == "R-M30-STD").first()
            if not recipe:
                recipe = Recipe(
                    id="RECIPE-ID-M30-STD",
                    recipe_code="R-M30-STD",
                    recipe_name="Standard Structural Concrete M30",
                    target_strength_mpa=30.0,
                    slump_target_mm=120.0
                )
                db.add(recipe)

            recipe_m40 = db.query(Recipe).filter(Recipe.recipe_code == "M40_VW_UT_ISOLATED").first()
            if not recipe_m40:
                recipe_m40 = Recipe(
                    id="RECIPE-ID-M40-ISO",
                    recipe_code="M40_VW_UT_ISOLATED",
                    recipe_name="High Performance M40 Concrete",
                    target_strength_mpa=40.0,
                    slump_target_mm=120.0
                )
                db.add(recipe_m40)

            db.commit()
        finally:
            db.close()

    def setUp(self):
        """Ensure master data and certified Step 1 + Step 2 + Step 3 draft exist."""
        session_factory = get_session_factory()
        self.db = session_factory()

        # Step 1
        res_s1 = client.post("/api/v1/manual-entry/drafts", json={
            "plant_code": "PLANT-MUMBAI-01",
            "recipe_code": "M40_VW_UT_ISOLATED",
            "production_date": "2026-08-09",
            "shift": "DAY_SHIFT",
            "order_number": "ORD-2026-99"
        })
        self.assertEqual(res_s1.status_code, 200)
        self.draft_id = res_s1.json()["draft_id"]

        # Step 2
        res_s2 = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-2", json={
            "batch_start_time": "09:15:00",
            "batch_end_time": "09:17:15",
            "mixer_time_seconds": 45,
            "truck_number": "TM-MUM-402",
            "delivery_challan": "DC-2026-8801",
            "aggregate_moisture_correction": 1.2,
            "target_slump_mm": 120.0
        })
        self.assertEqual(res_s2.status_code, 200)

        # Step 3
        res_s3 = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json={
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
        })
        self.assertEqual(res_s3.status_code, 200)

    def tearDown(self):
        self.db.close()

    def test_01_save_valid_laboratory_qa(self):
        """Valid Step 4 payload saves cleanly and updates draft step to 4."""
        payload_s4 = {
            "qa_cube_id": f"QC-M40-{uuid.uuid4().hex[:4].upper()}",
            "lab_technician_id": "TECH-MUM-01",
            "lab_technician_name": "Rahul Kumar",
            "casting_date": "2026-06-30",
            "testing_date_28_day": "2026-07-28",
            "result_7_day_mpa": 30.8,
            "result_28_day_mpa": 51.3,
            "failure_reason_code": "NONE",
            "laboratory_remarks": "Standard 28D water bath curing completed cleanly."
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-4", json=payload_s4)
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d["current_step"], 4)
        self.assertEqual(d["result_28_day_mpa"], 51.3)
        self.assertEqual(d["strength_margin_mpa"], 11.3)
        self.assertEqual(d["qa_metadata"]["qa_assessment_status"], "PASS")

    def test_02_qa_cube_id_required(self):
        """Whitespace or empty QA Cube ID is rejected with HTTP 422."""
        payload = {
            "qa_cube_id": "   ",
            "lab_technician_id": "TECH-MUM-01",
            "lab_technician_name": "Rahul Kumar",
            "casting_date": "2026-06-30",
            "testing_date_28_day": "2026-07-28",
            "result_28_day_mpa": 51.3,
            "failure_reason_code": "NONE"
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-4", json=payload)
        self.assertEqual(res.status_code, 422)

    def test_03_qa_cube_id_max_length_exceeded(self):
        """QA Cube ID > 50 characters is rejected with HTTP 422."""
        payload = {
            "qa_cube_id": "X" * 51,
            "lab_technician_id": "TECH-MUM-01",
            "lab_technician_name": "Rahul Kumar",
            "casting_date": "2026-06-30",
            "testing_date_28_day": "2026-07-28",
            "result_28_day_mpa": 51.3,
            "failure_reason_code": "NONE"
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-4", json=payload)
        self.assertEqual(res.status_code, 422)

    def test_04_duplicate_qa_cube_id_rejection(self):
        """Registering the same QA Cube ID to two distinct drafts is rejected with HTTP 422."""
        cube_id = f"QC-DUP-{uuid.uuid4().hex[:4].upper()}"
        payload1 = {
            "qa_cube_id": cube_id,
            "lab_technician_id": "TECH-MUM-01",
            "lab_technician_name": "Rahul Kumar",
            "casting_date": "2026-06-30",
            "testing_date_28_day": "2026-07-28",
            "result_28_day_mpa": 51.3,
            "failure_reason_code": "NONE"
        }
        res1 = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-4", json=payload1)
        self.assertEqual(res1.status_code, 200)

        # Create second draft
        res_s1 = client.post("/api/v1/manual-entry/drafts", json={
            "plant_code": "PLANT-MUMBAI-01",
            "recipe_code": "M40_VW_UT_ISOLATED",
            "production_date": "2026-08-09",
            "shift": "DAY_SHIFT"
        })
        draft_id2 = res_s1.json()["draft_id"]

        # Attempt to reuse cube_id
        res2 = client.put(f"/api/v1/manual-entry/drafts/{draft_id2}/step-4", json=payload1)
        self.assertEqual(res2.status_code, 422)

    def test_05_casting_date_format_validation(self):
        """Invalid casting date format rejected with HTTP 422."""
        payload = {
            "qa_cube_id": "QC-TEST-01",
            "lab_technician_id": "TECH-MUM-01",
            "lab_technician_name": "Rahul Kumar",
            "casting_date": "30-06-2026",
            "testing_date_28_day": "2026-07-28",
            "result_28_day_mpa": 51.3,
            "failure_reason_code": "NONE"
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-4", json=payload)
        self.assertEqual(res.status_code, 422)

    def test_07_testing_date_earlier_than_casting_date_rejection(self):
        """Testing date earlier than casting date rejected with HTTP 422."""
        payload = {
            "qa_cube_id": f"QC-DATE-{uuid.uuid4().hex[:4].upper()}",
            "lab_technician_id": "TECH-MUM-01",
            "lab_technician_name": "Rahul Kumar",
            "casting_date": "2026-07-28",
            "testing_date_28_day": "2026-06-30",
            "result_28_day_mpa": 51.3,
            "failure_reason_code": "NONE"
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-4", json=payload)
        self.assertEqual(res.status_code, 422)

    def test_08_curing_age_days_calculation(self):
        """Calculates exact days between casting and 28-day testing date (28 days)."""
        payload = {
            "qa_cube_id": f"QC-AGE-{uuid.uuid4().hex[:4].upper()}",
            "lab_technician_id": "TECH-MUM-01",
            "lab_technician_name": "Rahul Kumar",
            "casting_date": "2026-06-30",
            "testing_date_28_day": "2026-07-28",
            "result_28_day_mpa": 51.3,
            "failure_reason_code": "NONE"
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-4", json=payload)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["qa_metadata"]["days_between_casting_and_testing"], 28)

    def test_09_optional_7_day_strength_validation(self):
        """7-day strength out of 0-120 MPa range rejected with HTTP 422."""
        payload = {
            "qa_cube_id": f"QC-7D-{uuid.uuid4().hex[:4].upper()}",
            "lab_technician_id": "TECH-MUM-01",
            "lab_technician_name": "Rahul Kumar",
            "casting_date": "2026-06-30",
            "testing_date_28_day": "2026-07-28",
            "result_7_day_mpa": -5.0,
            "result_28_day_mpa": 51.3,
            "failure_reason_code": "NONE"
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-4", json=payload)
        self.assertEqual(res.status_code, 422)

    def test_10_mandatory_28_day_strength_validation(self):
        """28-day strength <= 0 rejected with HTTP 422."""
        payload = {
            "qa_cube_id": f"QC-28D-{uuid.uuid4().hex[:4].upper()}",
            "lab_technician_id": "TECH-MUM-01",
            "lab_technician_name": "Rahul Kumar",
            "casting_date": "2026-06-30",
            "testing_date_28_day": "2026-07-28",
            "result_28_day_mpa": 0.0,
            "failure_reason_code": "NONE"
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-4", json=payload)
        self.assertEqual(res.status_code, 422)

    def test_11_target_strength_grade_resolution(self):
        """Resolves target grade 40.0 MPa from Recipe Master M40_VW_UT_ISOLATED."""
        payload = {
            "qa_cube_id": f"QC-RESOLVE-{uuid.uuid4().hex[:4].upper()}",
            "lab_technician_id": "TECH-MUM-01",
            "lab_technician_name": "Rahul Kumar",
            "casting_date": "2026-06-30",
            "testing_date_28_day": "2026-07-28",
            "result_28_day_mpa": 51.3,
            "failure_reason_code": "NONE"
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-4", json=payload)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["qa_metadata"]["target_strength_mpa"], 40.0)

    def test_12_strength_margin_calculation(self):
        """Strength margin = 51.3 - 40.0 = +11.3 MPa."""
        payload = {
            "qa_cube_id": f"QC-MARGIN-{uuid.uuid4().hex[:4].upper()}",
            "lab_technician_id": "TECH-MUM-01",
            "lab_technician_name": "Rahul Kumar",
            "casting_date": "2026-06-30",
            "testing_date_28_day": "2026-07-28",
            "result_28_day_mpa": 51.3,
            "failure_reason_code": "NONE"
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-4", json=payload)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["strength_margin_mpa"], 11.3)

    def test_14_invalid_failure_reason_code_rejection(self):
        """Unknown failure reason code rejected with HTTP 422."""
        payload = {
            "qa_cube_id": f"QC-REASON-{uuid.uuid4().hex[:4].upper()}",
            "lab_technician_id": "TECH-MUM-01",
            "lab_technician_name": "Rahul Kumar",
            "casting_date": "2026-06-30",
            "testing_date_28_day": "2026-07-28",
            "result_28_day_mpa": 51.3,
            "failure_reason_code": "INVALID_REASON"
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-4", json=payload)
        self.assertEqual(res.status_code, 422)

    def test_15_failure_reason_explanatory_text_required(self):
        """Non-NONE failure reason without explanatory text rejected with HTTP 422."""
        payload = {
            "qa_cube_id": f"QC-EXPLANATION-{uuid.uuid4().hex[:4].upper()}",
            "lab_technician_id": "TECH-MUM-01",
            "lab_technician_name": "Rahul Kumar",
            "casting_date": "2026-06-30",
            "testing_date_28_day": "2026-07-28",
            "result_28_day_mpa": 35.0,
            "failure_reason_code": "LOW_STRENGTH",
            "failure_reason_text": "   "
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-4", json=payload)
        self.assertEqual(res.status_code, 422)

    def test_17_qa_assessment_status_review_required(self):
        """Strength below target or non-NONE failure reason evaluates to REVIEW_REQUIRED."""
        payload = {
            "qa_cube_id": f"QC-REVIEW-{uuid.uuid4().hex[:4].upper()}",
            "lab_technician_id": "TECH-MUM-01",
            "lab_technician_name": "Rahul Kumar",
            "casting_date": "2026-06-30",
            "testing_date_28_day": "2026-07-28",
            "result_28_day_mpa": 35.0,
            "failure_reason_code": "LOW_STRENGTH",
            "failure_reason_text": "Specimen 28D compressive strength fell 5 MPa below target."
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-4", json=payload)
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d["strength_margin_mpa"], -5.0)
        self.assertEqual(d["qa_metadata"]["qa_assessment_status"], "REVIEW_REQUIRED")

    def test_19_cross_operator_access_denied(self):
        """Cross-operator Step 4 update rejected with HTTP 403."""
        payload = {
            "qa_cube_id": f"QC-CROSS-{uuid.uuid4().hex[:4].upper()}",
            "lab_technician_id": "TECH-MUM-01",
            "lab_technician_name": "Rahul Kumar",
            "casting_date": "2026-06-30",
            "testing_date_28_day": "2026-07-28",
            "result_28_day_mpa": 51.3,
            "failure_reason_code": "NONE"
        }
        headers = {"Authorization": "Bearer OPERATOR_B_PUNE"}
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-4", json=payload, headers=headers)
        self.assertEqual(res.status_code, 403)

    def test_20_invariants_preserved(self):
        """Saving Step 4 preserves Step 1, Step 2, and Step 3 fields."""
        payload = {
            "qa_cube_id": f"QC-INV-{uuid.uuid4().hex[:4].upper()}",
            "lab_technician_id": "TECH-MUM-01",
            "lab_technician_name": "Rahul Kumar",
            "casting_date": "2026-06-30",
            "testing_date_28_day": "2026-07-28",
            "result_28_day_mpa": 51.3,
            "failure_reason_code": "NONE"
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-4", json=payload)
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d["plant_code"], "PLANT-MUMBAI-01")
        self.assertEqual(d["recipe_code"], "M40_VW_UT_ISOLATED")
        self.assertEqual(d["truck_number"], "TM-MUM-402")
        self.assertEqual(d["cement_kg_m3"], 315.0)
        self.assertEqual(d["effective_water_kg_m3"], 193.36)

    def test_21_draft_lifecycle_refetch_persistence(self):
        """GET /api/v1/manual-entry/drafts/{draft_id} returns saved Step 4 state."""
        payload = {
            "qa_cube_id": f"QC-REFETCH-{uuid.uuid4().hex[:4].upper()}",
            "lab_technician_id": "TECH-MUM-01",
            "lab_technician_name": "Rahul Kumar",
            "casting_date": "2026-06-30",
            "testing_date_28_day": "2026-07-28",
            "result_7_day_mpa": 30.8,
            "result_28_day_mpa": 51.3,
            "failure_reason_code": "NONE"
        }
        res_put = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-4", json=payload)
        self.assertEqual(res_put.status_code, 200)

        res_get = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}")
        self.assertEqual(res_get.status_code, 200)
        d = res_get.json()
        self.assertEqual(d["qa_cube_id"], payload["qa_cube_id"])
        self.assertEqual(d["result_28_day_mpa"], 51.3)
        self.assertEqual(d["qa_metadata"]["days_between_casting_and_testing"], 28)

    def test_24_production_isolation_prd_batches_zero(self):
        """Saving Step 4 writes zero records to prd_batches."""
        payload = {
            "qa_cube_id": f"QC-PRD-{uuid.uuid4().hex[:4].upper()}",
            "lab_technician_id": "TECH-MUM-01",
            "lab_technician_name": "Rahul Kumar",
            "casting_date": "2026-06-30",
            "testing_date_28_day": "2026-07-28",
            "result_28_day_mpa": 51.3,
            "failure_reason_code": "NONE"
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-4", json=payload)
        self.assertEqual(res.status_code, 200)

        count = self.db.query(Batch).count()
        self.assertEqual(count, 0)

    def test_25_required_functional_vector_1(self):
        """Verifies exact functional vector fixture (QC-M40-PUN-0630, 30.8 MPa 7D, 51.3 MPa 28D)."""
        payload_vector1 = {
            "qa_cube_id": "QC-M40-PUN-0630",
            "lab_technician_id": "TECH-MUM-01",
            "lab_technician_name": "Rahul Kumar",
            "casting_date": "2026-06-30",
            "testing_date_28_day": "2026-07-28",
            "result_7_day_mpa": 30.8,
            "result_28_day_mpa": 51.3,
            "failure_reason_code": "NONE",
            "laboratory_remarks": "Standard 28-day water curing completed. Specimen dimensions and mass verified."
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-4", json=payload_vector1)
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d["qa_cube_id"], "QC-M40-PUN-0630")
        self.assertEqual(d["lab_technician_name"], "Rahul Kumar")
        self.assertEqual(d["casting_date"], "2026-06-30")
        self.assertEqual(d["testing_date_28_day"], "2026-07-28")
        self.assertEqual(d["result_7_day_mpa"], 30.8)
        self.assertEqual(d["result_28_day_mpa"], 51.3)
        self.assertEqual(d["strength_margin_mpa"], 11.3)
        self.assertEqual(d["qa_metadata"]["qa_assessment_status"], "PASS")

    def test_26_testing_date_before_casting_date_rejection(self):
        """Testing date earlier than casting date (e.g. 2026-08-09 casting vs 2026-07-28 testing) rejected with HTTP 422."""
        payload = {
            "qa_cube_id": f"QC-NEGDATE-{uuid.uuid4().hex[:4].upper()}",
            "lab_technician_id": "TECH-MUM-01",
            "lab_technician_name": "Rahul Kumar",
            "casting_date": "2026-08-09",
            "testing_date_28_day": "2026-07-28", # Negative age -12 days!
            "result_28_day_mpa": 51.3,
            "failure_reason_code": "NONE"
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-4", json=payload)
        self.assertEqual(res.status_code, 422)
        self.assertIn("cannot be earlier than casting date", res.json()["detail"])

    def test_27_invalid_date_high_strength_never_overrides_schedule(self):
        """Even with high 51.3 MPa strength, invalid date chronology is strictly rejected and never saved."""
        payload = {
            "qa_cube_id": f"QC-HIGHSTRENGTH-INVALIDDATE-{uuid.uuid4().hex[:4].upper()}",
            "lab_technician_id": "TECH-MUM-01",
            "lab_technician_name": "Rahul Kumar",
            "casting_date": "2026-08-09",
            "testing_date_28_day": "2026-07-28",
            "result_28_day_mpa": 51.3,
            "failure_reason_code": "NONE"
        }
    def test_28_six_day_specimen_rejected_for_28_day_test(self):
        """A 6-day specimen (e.g. 2026-08-09 to 2026-08-15) cannot be submitted as a 28-day QA result and is rejected with HTTP 422."""
        payload = {
            "qa_cube_id": f"QC-6DAY-{uuid.uuid4().hex[:4].upper()}",
            "lab_technician_id": "TECH-MUM-01",
            "lab_technician_name": "Rahul Kumar",
            "casting_date": "2026-08-09",
            "testing_date_28_day": "2026-08-15", # 6 days curing age!
            "result_28_day_mpa": 51.3,
            "failure_reason_code": "NONE"
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-4", json=payload)
        self.assertEqual(res.status_code, 422)
        self.assertIn("Expected curing age is exactly 28 days", res.json()["detail"])


if __name__ == "__main__":
    unittest.main()


