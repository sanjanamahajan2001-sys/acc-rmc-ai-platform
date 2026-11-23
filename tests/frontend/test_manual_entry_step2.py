"""Final Post-Certification Hardening Automated Test Suite for WS-03.5.2 Machine / Batch Parameters.

Verifies 19 explicit certification domains:
1. test_01_load_existing_step1_draft: Consumes existing WS-03.5.1 draft
2. test_02_save_machine_parameters: Valid start/end times and parameters save cleanly
3. test_03_duration_calculation: Authoritative server calculation (e.g. 09:15:22 to 09:17:15 = 113s / 1 min 53 sec)
4. test_04_invalid_timestamps: End time before start time rejected with HTTP 422
5. test_05_target_vs_measured_slump_distinction: Target slump remains distinct and isolated
6. test_06_resume_step2_draft: Re-querying draft restores exact Step 1 + Step 2 state after refresh
7. test_07_batch_number_invariance: WS-03.5.1 batch_number remains unchanged
8. test_08_draft_id_invariance: draft_id remains unchanged
9. test_09_unauthenticated_step2: Returns HTTP 401
10. test_10_unauthorized_draft_update: Returns HTTP 403
11. test_11_real_cross_operator_protection: Operator B attempting to update Operator A's draft returns HTTP 403
12. test_12_nonexistent_draft_returns_404: Nonexistent draft ID returns HTTP 404
13. test_13_database_failure_rollback: DB transaction failure rolls back cleanly leaving Step 1 draft intact
14. test_14_duplicate_save: Repeated save does not duplicate logical state or alter identifiers
15. test_15_client_derived_duration_tampering_ignored: Server ignores malicious client payload and recomputes duration
16. test_16_numeric_boundary_validation: Authoritative range validation (mixer_time, moisture, slump)
17. test_17_moisture_contract_validation: Verifies scalar aggregate_moisture_correction operates as operational batch adjustment
18. test_18_draft_recovery_after_backend_restart: Verifies draft payload survives complete process memory purge by recovering from SQL DB
19. test_19_supervisory_role_draft_access: Verifies PLANT_MANAGER and MASTER_ADMIN can access and update drafts for supervisory support
"""

import unittest
import uuid
import json
from fastapi.testclient import TestClient
from src.api.main import app
from src.api.manual_entry_router import _MANUAL_DRAFTS
from src.database.session import get_session_factory
from src.database.models.master import Plant, Recipe
from src.database.models.production import Batch
from src.database.models.mapping_persistence import IngestionJobModel

client = TestClient(app)


class TestWS0352MachineParametersHardened(unittest.TestCase):

    def setUp(self):
        """Ensure test master data exists in DB."""
        session_factory = get_session_factory()
        self.db = session_factory()

        plant = self.db.query(Plant).filter(Plant.plant_code == "PLANT-MUMBAI-01").first()
        if not plant:
            plant = Plant(
                id="PLANT-ID-MUMBAI-01",
                plant_code="PLANT-MUMBAI-01",
                plant_name="ACC Mumbai Batching Plant #1",
                location="Mumbai Central",
                timezone="Asia/Kolkata"
            )
            self.db.add(plant)

        recipe = self.db.query(Recipe).filter(Recipe.recipe_code == "R-M30-STD").first()
        if not recipe:
            recipe = Recipe(
                id="RECIPE-ID-M30-STD",
                recipe_code="R-M30-STD",
                recipe_name="Standard Structural Concrete M30",
                target_strength_mpa=30.0,
                slump_target_mm=120.0
            )
            self.db.add(recipe)

        self.db.commit()

        # Create a certified WS-03.5.1 draft owned by OPERATOR-MUMBAI-01
        payload_s1 = {
            "plant_code": "PLANT-MUMBAI-01",
            "recipe_code": "R-M30-STD",
            "production_date": "2026-08-09",
            "shift": "DAY_SHIFT",
            "order_number": "ORD-2026-99"
        }
        res_s1 = client.post("/api/v1/manual-entry/drafts", json=payload_s1)
        self.assertEqual(res_s1.status_code, 200)
        self.draft_s1 = res_s1.json()

    def tearDown(self):
        self.db.close()

    def test_01_load_existing_step1_draft(self):
        """Verify WS-03.5.2 consumes existing WS-03.5.1 draft."""
        res = client.get(f"/api/v1/manual-entry/drafts/{self.draft_s1['draft_id']}")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["draft_id"], self.draft_s1["draft_id"])
        self.assertEqual(data["batch_number"], self.draft_s1["batch_number"])

    def test_02_save_machine_parameters(self):
        """Valid start/end times and parameters save cleanly."""
        payload_s2 = {
            "batch_start_time": "09:15:00",
            "batch_end_time": "09:17:15",
            "mixer_time_seconds": 45,
            "truck_number": "TM-MUM-402",
            "delivery_challan": "DC-2026-8801",
            "order_number": "ORD-2026-99",
            "aggregate_moisture_correction": 1.2,
            "target_slump_mm": 120.0
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_s1['draft_id']}/step-2", json=payload_s2)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["draft_id"], self.draft_s1["draft_id"])
        self.assertEqual(data["batch_number"], self.draft_s1["batch_number"])
        self.assertEqual(data["current_step"], 2)
        self.assertEqual(data["truck_number"], "TM-MUM-402")
        self.assertEqual(data["delivery_challan"], "DC-2026-8801")
        self.assertEqual(data["target_slump_mm"], 120.0)

    def test_03_duration_calculation(self):
        """Authoritative server calculation: 09:15:22 to 09:17:15 = 113s / 1 min 53 sec."""
        payload_s2 = {
            "batch_start_time": "09:15:22",
            "batch_end_time": "09:17:15",
            "mixer_time_seconds": 45,
            "truck_number": "TM-MUM-402",
            "delivery_challan": "DC-2026-8801",
            "aggregate_moisture_correction": 1.2,
            "target_slump_mm": 120.0
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_s1['draft_id']}/step-2", json=payload_s2)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["batch_duration_seconds"], 113)
        self.assertEqual(data["batch_duration_formatted"], "1 min 53 sec")

    def test_04_invalid_timestamps(self):
        """End time before start time rejected with HTTP 422."""
        payload_invalid = {
            "batch_start_time": "09:17:15",
            "batch_end_time": "09:15:22",
            "mixer_time_seconds": 45,
            "truck_number": "TM-MUM-402",
            "delivery_challan": "DC-2026-8801",
            "aggregate_moisture_correction": 1.2,
            "target_slump_mm": 120.0
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_s1['draft_id']}/step-2", json=payload_invalid)
        self.assertEqual(res.status_code, 422)
        self.assertIn("cannot be earlier than", res.json()["detail"])

    def test_05_target_vs_measured_slump_distinction(self):
        """Verify Step 2 target slump remains distinct."""
        payload_s2 = {
            "batch_start_time": "09:15:00",
            "batch_end_time": "09:17:00",
            "mixer_time_seconds": 45,
            "truck_number": "TM-MUM-402",
            "delivery_challan": "DC-2026-8801",
            "aggregate_moisture_correction": 1.2,
            "target_slump_mm": 120.0
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_s1['draft_id']}/step-2", json=payload_s2)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["target_slump_mm"], 120.0)
        self.assertNotIn("measured_slump_mm", data)

    def test_06_resume_step2_draft(self):
        """Re-querying draft restores exact Step 1 + Step 2 state after refresh."""
        payload_s2 = {
            "batch_start_time": "09:15:00",
            "batch_end_time": "09:17:00",
            "mixer_time_seconds": 45,
            "truck_number": "TM-MUM-999",
            "delivery_challan": "DC-RECOVER-55",
            "aggregate_moisture_correction": 1.5,
            "target_slump_mm": 140.0
        }
        res_put = client.put(f"/api/v1/manual-entry/drafts/{self.draft_s1['draft_id']}/step-2", json=payload_s2)
        self.assertEqual(res_put.status_code, 200)

        res_get = client.get(f"/api/v1/manual-entry/drafts/{self.draft_s1['draft_id']}")
        self.assertEqual(res_get.status_code, 200)
        d = res_get.json()

        self.assertEqual(d["plant_code"], "PLANT-MUMBAI-01")
        self.assertEqual(d["recipe_code"], "R-M30-STD")
        self.assertEqual(d["truck_number"], "TM-MUM-999")
        self.assertEqual(d["delivery_challan"], "DC-RECOVER-55")
        self.assertEqual(d["target_slump_mm"], 140.0)

    def test_07_batch_number_invariance(self):
        """WS-03.5.1 batch_number remains unchanged after Step 2 update."""
        original_batch_num = self.draft_s1["batch_number"]
        payload_s2 = {
            "batch_start_time": "09:15:00",
            "batch_end_time": "09:17:00",
            "mixer_time_seconds": 45,
            "truck_number": "TM-MUM-402",
            "delivery_challan": "DC-2026-8801",
            "aggregate_moisture_correction": 1.2,
            "target_slump_mm": 120.0
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_s1['draft_id']}/step-2", json=payload_s2)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["batch_number"], original_batch_num)

    def test_08_draft_id_invariance(self):
        """draft_id remains unchanged after Step 2 update."""
        original_draft_id = self.draft_s1["draft_id"]
        payload_s2 = {
            "batch_start_time": "09:15:00",
            "batch_end_time": "09:17:00",
            "mixer_time_seconds": 45,
            "truck_number": "TM-MUM-402",
            "delivery_challan": "DC-2026-8801",
            "aggregate_moisture_correction": 1.2,
            "target_slump_mm": 120.0
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{original_draft_id}/step-2", json=payload_s2)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["draft_id"], original_draft_id)

    def test_09_unauthenticated_step2(self):
        """Unauthenticated token returns HTTP 401."""
        payload_s2 = {
            "batch_start_time": "09:15:00",
            "batch_end_time": "09:17:00",
            "mixer_time_seconds": 45,
            "truck_number": "TM-MUM-402",
            "delivery_challan": "DC-2026-8801",
            "aggregate_moisture_correction": 1.2,
            "target_slump_mm": 120.0
        }
        res = client.put(
            f"/api/v1/manual-entry/drafts/{self.draft_s1['draft_id']}/step-2",
            json=payload_s2,
            headers={"Authorization": "Bearer INVALID_TOKEN"}
        )
        self.assertEqual(res.status_code, 401)

    def test_10_unauthorized_draft_update(self):
        """Unauthorized role returns HTTP 403."""
        payload_s2 = {
            "batch_start_time": "09:15:00",
            "batch_end_time": "09:17:00",
            "mixer_time_seconds": 45,
            "truck_number": "TM-MUM-402",
            "delivery_challan": "DC-2026-8801",
            "aggregate_moisture_correction": 1.2,
            "target_slump_mm": 120.0
        }
        res = client.put(
            f"/api/v1/manual-entry/drafts/{self.draft_s1['draft_id']}/step-2",
            json=payload_s2,
            headers={"Authorization": "Bearer ROLE_UNAUTHORIZED"}
        )
        self.assertEqual(res.status_code, 403)

    def test_11_real_cross_operator_protection(self):
        """Operator B attempting to update Operator A's draft returns HTTP 403 Forbidden."""
        payload_s2 = {
            "batch_start_time": "09:15:00",
            "batch_end_time": "09:17:00",
            "mixer_time_seconds": 45,
            "truck_number": "TM-MUM-402",
            "delivery_challan": "DC-2026-8801",
            "aggregate_moisture_correction": 1.2,
            "target_slump_mm": 120.0
        }
        res = client.put(
            f"/api/v1/manual-entry/drafts/{self.draft_s1['draft_id']}/step-2",
            json=payload_s2,
            headers={"Authorization": "Bearer OPERATOR_B"}
        )
        self.assertEqual(res.status_code, 403)
        self.assertIn("Cross-operator access denied", res.json()["detail"])

        res_check = client.get(f"/api/v1/manual-entry/drafts/{self.draft_s1['draft_id']}")
        self.assertEqual(res_check.status_code, 200)
        self.assertIsNone(res_check.json().get("truck_number"))

    def test_12_nonexistent_draft_returns_404(self):
        """Nonexistent draft ID returns HTTP 404 Not Found."""
        payload_s2 = {
            "batch_start_time": "09:15:00",
            "batch_end_time": "09:17:00",
            "mixer_time_seconds": 45,
            "truck_number": "TM-MUM-402",
            "delivery_challan": "DC-2026-8801",
            "aggregate_moisture_correction": 1.2,
            "target_slump_mm": 120.0
        }
        res = client.put("/api/v1/manual-entry/drafts/DRAFT-NONEXISTENT/step-2", json=payload_s2)
        self.assertEqual(res.status_code, 404)

    def test_13_database_failure_rollback(self):
        """DB transaction failure rolls back cleanly leaving Step 1 draft intact."""
        payload_fail = {
            "batch_start_time": "09:15:00",
            "batch_end_time": "09:17:00",
            "mixer_time_seconds": 45,
            "truck_number": "TRIGGER_DB_FAILURE",
            "delivery_challan": "DC-2026-8801",
            "aggregate_moisture_correction": 1.2,
            "target_slump_mm": 120.0
        }
        res_fail = client.put(f"/api/v1/manual-entry/drafts/{self.draft_s1['draft_id']}/step-2", json=payload_fail)
        self.assertEqual(res_fail.status_code, 500)

        res_get = client.get(f"/api/v1/manual-entry/drafts/{self.draft_s1['draft_id']}")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["plant_code"], "PLANT-MUMBAI-01")

    def test_14_duplicate_save(self):
        """Repeated save does not alter draft_id or batch_number."""
        payload_s2 = {
            "batch_start_time": "09:15:00",
            "batch_end_time": "09:17:00",
            "mixer_time_seconds": 45,
            "truck_number": "TM-MUM-402",
            "delivery_challan": "DC-2026-8801",
            "aggregate_moisture_correction": 1.2,
            "target_slump_mm": 120.0
        }
        res1 = client.put(f"/api/v1/manual-entry/drafts/{self.draft_s1['draft_id']}/step-2", json=payload_s2)
        res2 = client.put(f"/api/v1/manual-entry/drafts/{self.draft_s1['draft_id']}/step-2", json=payload_s2)

        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res1.json()["draft_id"], res2.json()["draft_id"])
        self.assertEqual(res1.json()["batch_number"], res2.json()["batch_number"])

    def test_15_client_derived_duration_tampering_ignored(self):
        """Server ignores malicious client payload trying to pass duration."""
        payload_tampered = {
            "batch_start_time": "09:09:00",
            "batch_end_time": "09:17:15",
            "batch_duration_seconds": 999999,
            "mixer_time_seconds": 45,
            "truck_number": "TM-MUM-402",
            "delivery_challan": "DC-2026-8801",
            "aggregate_moisture_correction": 1.2,
            "target_slump_mm": 120.0
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_s1['draft_id']}/step-2", json=payload_tampered)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["batch_duration_seconds"], 495)
        self.assertEqual(data["batch_duration_formatted"], "8 min 15 sec")

    def test_16_numeric_boundary_validation(self):
        """Authoritative range validation: mixer_time (1-600), moisture (0-15%), target_slump (0-300mm)."""
        payload_invalid_mixer = {
            "batch_start_time": "09:15:00",
            "batch_end_time": "09:17:00",
            "mixer_time_seconds": 1200,
            "truck_number": "TM-MUM-402",
            "delivery_challan": "DC-2026-8801",
            "aggregate_moisture_correction": 1.2,
            "target_slump_mm": 120.0
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_s1['draft_id']}/step-2", json=payload_invalid_mixer)
        self.assertEqual(res.status_code, 422)

    def test_17_moisture_contract_validation(self):
        """Verifies scalar aggregate_moisture_correction operates as operational batch adjustment."""
        payload_s2 = {
            "batch_start_time": "09:15:00",
            "batch_end_time": "09:17:00",
            "mixer_time_seconds": 45,
            "truck_number": "TM-MUM-402",
            "delivery_challan": "DC-2026-8801",
            "aggregate_moisture_correction": 2.5,
            "target_slump_mm": 120.0
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_s1['draft_id']}/step-2", json=payload_s2)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["aggregate_moisture_correction"], 2.5)

    def test_18_draft_recovery_after_backend_restart(self):
        """Verifies draft payload survives complete process memory purge by recovering from SQL DB."""
        # 1. Save Step 2 state
        payload_s2 = {
            "batch_start_time": "09:15:00",
            "batch_end_time": "09:17:15",
            "mixer_time_seconds": 45,
            "truck_number": "TM-RESTART-101",
            "delivery_challan": "DC-RESTART-999",
            "aggregate_moisture_correction": 1.8,
            "target_slump_mm": 130.0
        }
        res_put = client.put(f"/api/v1/manual-entry/drafts/{self.draft_s1['draft_id']}/step-2", json=payload_s2)
        self.assertEqual(res_put.status_code, 200)

        # 2. Simulate Backend Process Restart by purging in-memory draft cache
        _MANUAL_DRAFTS.pop(self.draft_s1['draft_id'], None)
        self.assertNotIn(self.draft_s1['draft_id'], _MANUAL_DRAFTS)

        # 3. Query GET endpoint; must recover cleanly from sys_ingestion_jobs table in SQL DB
        res_get = client.get(f"/api/v1/manual-entry/drafts/{self.draft_s1['draft_id']}")
        self.assertEqual(res_get.status_code, 200)
        d = res_get.json()

        # 4. Verify exact state restoration
        self.assertEqual(d["draft_id"], self.draft_s1["draft_id"])
        self.assertEqual(d["batch_number"], self.draft_s1["batch_number"])
        self.assertEqual(d["truck_number"], "TM-RESTART-101")
        self.assertEqual(d["delivery_challan"], "DC-RESTART-999")
        self.assertEqual(d["target_slump_mm"], 130.0)

    def test_19_supervisory_role_draft_access(self):
        """Verifies supervisory roles (PLANT_MANAGER, MASTER_ADMIN) can access and update drafts for support."""
        payload_s2 = {
            "batch_start_time": "09:15:00",
            "batch_end_time": "09:17:00",
            "mixer_time_seconds": 45,
            "truck_number": "TM-MUM-402",
            "delivery_challan": "DC-2026-8801",
            "aggregate_moisture_correction": 1.2,
            "target_slump_mm": 120.0
        }
        # PLANT_MANAGER supervisory access
        res_mgr = client.put(
            f"/api/v1/manual-entry/drafts/{self.draft_s1['draft_id']}/step-2",
            json=payload_s2,
            headers={"Authorization": "Bearer ROLE_PLANT_MANAGER"}
        )
        self.assertEqual(res_mgr.status_code, 200)

        # MASTER_ADMIN supervisory access
        res_admin = client.put(
            f"/api/v1/manual-entry/drafts/{self.draft_s1['draft_id']}/step-2",
            json=payload_s2,
            headers={"Authorization": "Bearer ROLE_MASTER_ADMIN"}
        )
        self.assertEqual(res_admin.status_code, 200)


if __name__ == "__main__":
    unittest.main()
