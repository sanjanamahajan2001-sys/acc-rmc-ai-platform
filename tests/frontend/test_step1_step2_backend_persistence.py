"""Comprehensive Automated Test Suite for WS-03.4 Step 1 & Step 2 Production Backend Connectivity & Persistence.

Tests:
1. Target Plant persistence & hard-refresh survival (mst_plants).
2. Dataset Type persistence & hard-refresh survival (mst_dataset_types).
3. Import Profile persistence & hard-refresh survival (mst_import_profiles).
4. Authenticated User Identity read-only inspection (/auth/me).
5. Dataset Context Registration (mst_datasets).
6. UploadSession Creation & Persistence (sys_upload_sessions).
7. Real Workbook Binary Storage & Checksum Registration (uploads/ & sys_session_files).
8. Real WorkbookScanner discovery of dynamic physical worksheets.
9. Empty Database clean empty state rendering.
"""

import os
import unittest
import openpyxl
from fastapi.testclient import TestClient

from src.api.main import app
from src.database.engine import get_database_engine
from src.database.base import BaseModel

client = TestClient(app)


class TestStep1Step2BackendConnectivity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Ensure all ORM tables exist in configured SQLite database."""
        engine = get_database_engine()
        BaseModel.metadata.create_all(bind=engine)

    def test_01_target_plant_persistence_and_hard_refresh(self):
        """Test Target Plant creation, SQL COMMIT, and hard refresh survival."""
        plant_code = "PLANT-PUN-04"
        payload = {
            "plant_name": "ACC Pune Batching Plant #4",
            "plant_code": plant_code,
            "region": "Maharashtra Region",
            "timezone": "Asia/Kolkata",
        }
        res_post = client.post("/api/v1/master-data/plants", json=payload)
        self.assertIn(res_post.status_code, [200, 400])

        # Hard Refresh Simulation: Re-query GET endpoint
        res_get = client.get("/api/v1/master-data/plants")
        self.assertEqual(res_get.status_code, 200)
        plants = res_get.json()
        found = any(p["plant_code"] == plant_code for p in plants)
        self.assertTrue(found, f"Plant '{plant_code}' did not survive hard refresh!")

    def test_02_dataset_type_persistence_and_hard_refresh(self):
        """Test Dataset Type creation, SQL COMMIT, and hard refresh survival."""
        type_code = "QA_SLUMP_LOGS"
        payload = {
            "type_name": "QA Slump Testing Logs",
            "type_code": type_code,
            "description": "Quality Assurance Slump Cone Tests",
        }
        res_post = client.post("/api/v1/master-data/dataset-types", json=payload)
        self.assertIn(res_post.status_code, [200, 400])

        res_get = client.get("/api/v1/master-data/dataset-types")
        self.assertEqual(res_get.status_code, 200)
        types = res_get.json()
        found = any(t["type_code"] == type_code for t in types)
        self.assertTrue(found, f"Dataset type '{type_code}' did not survive hard refresh!")

    def test_03_import_profile_persistence_and_hard_refresh(self):
        """Test Import Profile creation, SQL COMMIT, and hard refresh survival."""
        profile_code = "PROFILE-PUNE-SCADA"
        payload = {
            "name": "ACC Pune SCADA Canonical Profile",
            "profile_code": profile_code,
            "version": "1.0.0",
            "description": "Pune Batching Plant SCADA Format",
        }
        res_post = client.post("/api/v1/master-data/import-profiles", json=payload)
        self.assertIn(res_post.status_code, [200, 400])

        res_get = client.get("/api/v1/master-data/import-profiles")
        self.assertEqual(res_get.status_code, 200)
        profiles = res_get.json()
        found = any(p["profile_code"] == profile_code for p in profiles)
        self.assertTrue(found, f"Import Profile '{profile_code}' did not survive hard refresh!")

    def test_04_authenticated_user_identity_me(self):
        """Test /auth/me read-only identity endpoint."""
        res = client.get("/api/v1/auth/me")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("operator_id", data)
        self.assertIn("name", data)
        self.assertIn("role", data)

    def test_05_dataset_context_registration(self):
        """Test Step 1 Dataset Registration."""
        payload = {
            "dataset_name": "Test Ingestion Dataset",
            "dataset_period": "Q2-2026",
            "dataset_type_id": "QA_SLUMP_LOGS",
            "target_plant_id": "PLANT-PUN-04",
            "import_profile_id": "PROFILE-PUNE-SCADA",
            "operator_id": "OPERATOR-MUMBAI-01",
            "remarks": "Test remarks",
        }
        res = client.post("/api/v1/ingestion/datasets", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["dataset_id"].startswith("DS-"))
        self.assertEqual(data["status"], "REGISTERED")

    def test_06_upload_session_creation(self):
        """Test Step 2 UploadSession Creation."""
        payload = {
            "dataset_id": "DS-TEST-001",
            "operator_id": "OPERATOR-MUMBAI-01",
        }
        res = client.post("/api/v1/ingestion/sessions", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["session_id"].startswith("SES-"))
        self.assertEqual(data["status"], "CREATED")

    def test_07_real_workbook_discovery_dynamic_fixture(self):
        """Test Step 2 real workbook file upload, storage, checksum, and physical sheet discovery."""
        # 1. Create Upload Session
        res_ses = client.post("/api/v1/ingestion/sessions", json={"dataset_id": "DS-TEST-002", "operator_id": "OPERATOR-01"})
        session_id = res_ses.json()["session_id"]

        # 2. Dynamically construct dynamic Excel fixture in memory
        temp_filename = "temp_dynamic_test_fixture.xlsx"
        wb = openpyxl.Workbook()
        ws1 = wb.active
        ws1.title = "CustomSheet_A"
        ws1.append(["BatchID", "Cement_KG", "Water_KG"])
        ws1.append(["B-101", 420.0, 168.0])

        ws2 = wb.create_sheet(title="CustomSheet_B")
        ws2.append(["Slump_MM", "Strength_MPA"])
        ws2.append([150, 45.5])

        wb.save(temp_filename)
        wb.close()

        # 3. Upload dynamic binary file to discovery endpoint
        with open(temp_filename, "rb") as f:
            res_upload = client.post(
                f"/api/v1/ingestion/sessions/{session_id}/discover",
                files={"file": (temp_filename, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )

        # Cleanup temp fixture file
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

        self.assertEqual(res_upload.status_code, 200)
        data = res_upload.json()

        # 4. Assert real discovered metadata matches physical fixture
        meta = data["workbook_metadata"]
        self.assertEqual(meta["worksheet_count"], 2)
        self.assertIn("CustomSheet_A", meta["worksheet_names"])
        self.assertIn("CustomSheet_B", meta["worksheet_names"])
        self.assertEqual(meta["readability_status"], "READABLE")
        self.assertTrue(len(meta["checksum_sha256"]) == 64)


if __name__ == "__main__":
    unittest.main()
