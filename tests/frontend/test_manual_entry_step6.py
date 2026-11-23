import unittest
from datetime import datetime, timezone
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.sql import text

from src.api.main import app
from src.api.manual_entry_router import _MANUAL_DRAFTS
from src.database.session import get_session_factory
from src.database.models.master import Plant, Recipe
from src.database.models.production import Batch

client = TestClient(app)

class TestManualEntryStep6(unittest.TestCase):
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

        # Seed clean draft for Step 6 testing
        res = client.post("/api/v1/manual-entry/drafts", json={
            "plant_code": "PLANT-MUMBAI-01",
            "recipe_code": "M40_VW_UT_ISOLATED",
            "production_date": "2026-08-09",
            "shift": "DAY"
        })
        self.assertEqual(res.status_code, 200)
        self.draft_id = res.json()["draft_id"]

        # Step 2
        res2 = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-2", json={
            "batch_start_time": "09:15:00",
            "batch_end_time": "09:17:15",
            "mixer_time_seconds": 45,
            "truck_number": "TM-MUM-402",
            "delivery_challan": f"DC-STEP6-{uuid.uuid4().hex[:4].upper()}",
            "aggregate_moisture_correction": 1.2,
            "target_slump_mm": 120.0
        })
        self.assertEqual(res2.status_code, 200)

        # Step 3
        res3 = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json={
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
        self.assertEqual(res3.status_code, 200)

        # Step 4
        res4 = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-4", json={
            "qa_cube_id": f"QC-STEP6-{uuid.uuid4().hex[:4].upper()}",
            "lab_technician_id": "TECH-MUM-01",
            "lab_technician_name": "Rahul Kumar",
            "casting_date": "2026-08-09",
            "testing_date_28_day": "2026-09-06",
            "result_7_day_mpa": 30.8,
            "result_28_day_mpa": 51.3,
            "failure_reason_code": "NONE",
            "laboratory_remarks": "Standard 28-day water curing verified."
        })
        self.assertEqual(res4.status_code, 200)

    def tearDown(self):
        if self.draft_id in _MANUAL_DRAFTS:
            del _MANUAL_DRAFTS[self.draft_id]
        self.db.close()

    def test_01_final_review_endpoint_returns_authoritative_data(self):
        """GET /final-review returns complete draft and re-evaluated Quality Gate."""
        res = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/final-review")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("draft", data)
        self.assertIn("quality_gate", data)
        self.assertEqual(data["quality_gate"]["overall_status"], "QUALITY_CLEAR")
        self.assertTrue(data["quality_gate"]["final_review_eligible"])
        self.assertFalse(data["is_submitted"])

    def test_02_clean_pass_can_submit_production_batch(self):
        """Clean QUALITY_CLEAR draft can be submitted to production DB."""
        res = client.post(f"/api/v1/manual-entry/drafts/{self.draft_id}/submit")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        try:
            self.assertTrue(data["success"])
            self.assertIn("PRD-BATCH-", data["production_batch_id"])
            self.assertEqual(data["quality_status"], "QUALITY_CLEAR")
        finally:
            if "production_batch_id" in data:
                self.db.execute(text("DELETE FROM prd_batches WHERE id = :id"), {"id": data["production_batch_id"]})
                self.db.commit()

    def test_03_review_required_draft_can_submit(self):
        """Draft with W/B ratio warning (REVIEW_REQUIRED) can submit to production DB."""
        _MANUAL_DRAFTS[self.draft_id]["water_kg_m3"] = 268.36 # W/B = 0.596 > 0.50
        _MANUAL_DRAFTS[self.draft_id]["effective_water_kg_m3"] = 268.36
        _MANUAL_DRAFTS[self.draft_id]["w_b_ratio"] = 0.596

        res = client.post(f"/api/v1/manual-entry/drafts/{self.draft_id}/submit")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        try:
            self.assertTrue(data["success"])
            self.assertEqual(data["quality_status"], "REVIEW_REQUIRED")
        finally:
            if "production_batch_id" in data:
                self.db.execute(text("DELETE FROM prd_batches WHERE id = :id"), {"id": data["production_batch_id"]})
                self.db.commit()


    def test_04_blocked_draft_cannot_submit(self):
        """Draft with 6-day invalid curing age (BLOCKED) is rejected with HTTP 422."""
        _MANUAL_DRAFTS[self.draft_id]["testing_date_28_day"] = "2026-08-15" # 6 days!

        res = client.post(f"/api/v1/manual-entry/drafts/{self.draft_id}/submit")
        self.assertEqual(res.status_code, 422)
        detail = res.json()["detail"]
        self.assertEqual(detail["error"], "SUBMISSION_REJECTED")
        self.assertEqual(detail["quality_status"], "BLOCKED")
        self.assertFalse(detail["final_review_eligible"])

    def test_05_strength_deficit_cannot_submit(self):
        """Draft with strength deficit (35.0 MPa vs 40.0 MPa target) is rejected with HTTP 422."""
        _MANUAL_DRAFTS[self.draft_id]["result_28_day_mpa"] = 35.0

        res = client.post(f"/api/v1/manual-entry/drafts/{self.draft_id}/submit")
        self.assertEqual(res.status_code, 422)
        detail = res.json()["detail"]
        self.assertEqual(detail["quality_status"], "BLOCKED")

    def test_06_failure_reason_code_cannot_submit(self):
        """Draft with CURING_ISSUE failure reason code is rejected with HTTP 422."""
        _MANUAL_DRAFTS[self.draft_id]["failure_reason_code"] = "CURING_ISSUE"
        _MANUAL_DRAFTS[self.draft_id]["failure_reason_text"] = "Water bath temperature excursion."

        res = client.post(f"/api/v1/manual-entry/drafts/{self.draft_id}/submit")
        self.assertEqual(res.status_code, 422)
        detail = res.json()["detail"]
        self.assertEqual(detail["quality_status"], "BLOCKED")

    def test_07_stale_client_server_revalidation_rejects_submission(self):
        """Gate B: Client has previously evaluated clear review, backend becomes corrupted, submit rejects."""
        # 1. GET final review returns clear
        res1 = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}/final-review")
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.json()["quality_gate"]["overall_status"], "QUALITY_CLEAR")

        # 2. Behind client's back, backend state becomes invalid
        _MANUAL_DRAFTS[self.draft_id]["testing_date_28_day"] = "2026-08-15"

        # 3. Client clicks Submit -> POST /submit revalidation rejects
        res2 = client.post(f"/api/v1/manual-entry/drafts/{self.draft_id}/submit")
        self.assertEqual(res2.status_code, 422)
        self.assertEqual(res2.json()["detail"]["error"], "SUBMISSION_REJECTED")

    def test_08_idempotent_repeated_submission(self):
        """Repeated submission POST returns same production batch result without second DB insertion."""
        res1 = client.post(f"/api/v1/manual-entry/drafts/{self.draft_id}/submit")
        self.assertEqual(res1.status_code, 200)
        data1 = res1.json()
        batch_id = data1["production_batch_id"]

        try:
            # Submit same draft second time
            res2 = client.post(f"/api/v1/manual-entry/drafts/{self.draft_id}/submit")
            self.assertEqual(res2.status_code, 200)
            data2 = res2.json()
            self.assertTrue(data2["already_submitted"])
            self.assertEqual(data2["production_batch_id"], batch_id)
        finally:
            self.db.execute(text("DELETE FROM prd_batches WHERE id = :id"), {"id": batch_id})
            self.db.commit()



    def test_09_duplicate_batch_number_prd_batches_rejects(self):
        """Submit fails if batch number already committed in prd_batches."""
        dup_b_num = _MANUAL_DRAFTS[self.draft_id]["batch_number"]
        existing_id = f"PRD-EXISTING-{uuid.uuid4().hex[:6].upper()}"

        self.db.execute(text(
            "INSERT INTO prd_batches (id, batch_number, order_id, dispatch_schedule_id, recipe_id, plant_id, production_status, planned_quantity_m3, created_at, updated_at, is_deleted, version_id) "
            "VALUES (:id, :b_num, 'ORD-01', 'DSP-01', 'REC-01', 'PLT-01', 'COMPLETED', 6.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0, 1)"
        ), {"id": existing_id, "b_num": dup_b_num})
        self.db.commit()

        try:
            res = client.post(f"/api/v1/manual-entry/drafts/{self.draft_id}/submit")
            self.assertEqual(res.status_code, 422)
            reasons = str(res.json()["detail"]["blocking_reasons"])
            self.assertIn("already committed in production database", reasons)
        finally:
            self.db.execute(text("DELETE FROM prd_batches WHERE id = :id"), {"id": existing_id})
            self.db.commit()


    def test_10_cross_operator_submit_forbidden(self):
        """Operator B submitting Operator A draft gets HTTP 403 Forbidden."""
        headers = {"Authorization": "Bearer OPERATOR_B_TOKEN"}
        res = client.post(f"/api/v1/manual-entry/drafts/{self.draft_id}/submit", headers=headers)
        self.assertEqual(res.status_code, 403)


    def test_12_duplicate_delivery_challan_prd_batches_rejects(self):
        """Submit fails with HTTP 422 if delivery challan is already committed in prd_batches."""
        dup_challan = _MANUAL_DRAFTS[self.draft_id]["delivery_challan"]
        existing_id = f"PRD-CHALLAN-{uuid.uuid4().hex[:6].upper()}"

        challan_col = "delivery_challan_number" if hasattr(Batch, "delivery_challan_number") else ("delivery_challan" if hasattr(Batch, "delivery_challan") else None)
        if challan_col:
            self.db.execute(text(
                f"INSERT INTO prd_batches (id, batch_number, order_id, dispatch_schedule_id, recipe_id, plant_id, production_status, planned_quantity_m3, {challan_col}, created_at, updated_at, is_deleted, version_id) "
                "VALUES (:id, 'BATCH-UNIQUE-DC-01', 'ORD-01', 'DSP-01', 'REC-01', 'PLT-01', 'COMPLETED', 6.0, :challan, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0, 1)"
            ), {"id": existing_id, "challan": dup_challan})
            self.db.commit()

            try:
                res = client.post(f"/api/v1/manual-entry/drafts/{self.draft_id}/submit")
                self.assertEqual(res.status_code, 422)
                reasons = str(res.json()["detail"]["blocking_reasons"])
                self.assertIn("Delivery Challan", reasons)
            finally:
                self.db.execute(text("DELETE FROM prd_batches WHERE id = :id"), {"id": existing_id})
                self.db.commit()

    def test_13_duplicate_qa_cube_id_prd_batches_rejects(self):
        """Submit fails with HTTP 422 if QA cube ID is already committed in prd_batches."""
        dup_cube = _MANUAL_DRAFTS[self.draft_id]["qa_cube_id"]
        existing_id = f"PRD-CUBE-{uuid.uuid4().hex[:6].upper()}"

        cube_col = "qa_cube_id" if hasattr(Batch, "qa_cube_id") else None
        if cube_col:
            self.db.execute(text(
                f"INSERT INTO prd_batches (id, batch_number, order_id, dispatch_schedule_id, recipe_id, plant_id, production_status, planned_quantity_m3, {cube_col}, created_at, updated_at, is_deleted, version_id) "
                "VALUES (:id, 'BATCH-UNIQUE-CUBE-01', 'ORD-01', 'DSP-01', 'REC-01', 'PLT-01', 'COMPLETED', 6.0, :cube, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0, 1)"
            ), {"id": existing_id, "cube": dup_cube})
            self.db.commit()

            try:
                res = client.post(f"/api/v1/manual-entry/drafts/{self.draft_id}/submit")
                self.assertEqual(res.status_code, 422)
                reasons = str(res.json()["detail"]["blocking_reasons"])
                self.assertIn("QA Cube ID", reasons)
            finally:
                self.db.execute(text("DELETE FROM prd_batches WHERE id = :id"), {"id": existing_id})
                self.db.commit()

    def test_13_submission_transaction_rolls_back_on_db_exception(self):
        """Transaction Atomicity Test: Controlled DB exception inside submit transaction block rolls back insertion and leaves draft status unsubmitted."""
        initial_count = self.db.query(Batch).count()
        initial_status = _MANUAL_DRAFTS[self.draft_id]["status"]

        # Corrupt draft's plant_code to invalid string to trigger DB exception inside try block
        _MANUAL_DRAFTS[self.draft_id]["plant_code"] = "INVALID_NON_EXISTENT_PLANT_FOR_EXCEPTION"

        res = client.post(f"/api/v1/manual-entry/drafts/{self.draft_id}/submit")
        # Assert exception handler caught failure and returned HTTP 422 / 500
        self.assertIn(res.status_code, [400, 422, 500])

        # Assert DB transaction rolled back cleanly and draft status was NOT updated to SUBMITTED
        final_count = self.db.query(Batch).count()
        final_status = _MANUAL_DRAFTS[self.draft_id]["status"]

        self.assertEqual(final_count, initial_count)
        self.assertNotEqual(final_status, "SUBMITTED")
        self.assertEqual(final_status, initial_status)

    def test_14_production_isolation_prd_batches_clean(self):
        """Verify test teardown leaves 0 records in prd_batches."""
        clean_db = get_session_factory()()
        try:
            count = clean_db.query(Batch).count()
            self.assertEqual(count, 0)
        finally:
            clean_db.close()





if __name__ == "__main__":
    unittest.main()
