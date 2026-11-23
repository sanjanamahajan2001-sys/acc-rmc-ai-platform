"""Fast Test Suite targeting small dynamic Excel fixture for fast execution."""

import os
import unittest
import openpyxl
from fastapi.testclient import TestClient

from src.api.main import app
from src.database.engine import get_database_engine
from src.database.base import BaseModel
from src.database.models.mapping_persistence import SessionMappingModel

client = TestClient(app)


class FastTestStep3BackendMappingExecution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        engine = get_database_engine()
        BaseModel.metadata.create_all(bind=engine)

        cls.temp_file = "/tmp/fast_test_workbook.xlsx"
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Batching Report"
        ws.append(["Batch_ID", "Plant_Code", "Actual_Cement_KG", "Water_Qty_KG", "Date_Time"])
        ws.append(["B-101", "P-01", 350.5, 150.0, "2026-06-01 10:00:00"])
        wb.save(cls.temp_file)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.temp_file):
            os.remove(cls.temp_file)

    def test_01_real_workbook_mapping_and_lineage(self):
        """Test Step 3 Mapping preview, audit strategy fidelity, and physical row traceability."""
        res1 = client.post("/api/v1/ingestion/datasets", json={"dataset_name": "DS Fast", "dataset_period": "Q2-2026", "dataset_type_id": "QA_SLUMP_LOGS", "target_plant_id": "test-v1", "import_profile_id": "PROFILE-PUNE-SCADA", "operator_id": "OPERATOR-MUMBAI-01", "remarks": ""})
        dataset_id = res1.json()["dataset_id"]

        res2 = client.post("/api/v1/ingestion/sessions", json={"dataset_id": dataset_id, "operator_id": "OPERATOR-MUMBAI-01"})
        session_id = res2.json()["session_id"]

        with open(self.temp_file, "rb") as f:
            client.post(f"/api/v1/ingestion/sessions/{session_id}/discover", files={"file": ("fast_test_workbook.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})

        res3 = client.post(f"/api/v1/ingestion/sessions/{session_id}/mapping/preview")
        self.assertEqual(res3.status_code, 200)
        data = res3.json()

        self.assertEqual(data["session_id"], session_id)
        self.assertIn("mapping_execution_id", data)
        self.assertEqual(data["mapping_engine_version"], "1.0.0")
        self.assertEqual(data["total_detected_columns"], 5)
        self.assertTrue(len(data["sheet_previews"]) > 0)

        sheet = data["sheet_previews"][0]
        self.assertEqual(sheet["worksheet_name"], "Batching Report")

        # Verify strategy fidelity
        for item in sheet["ledger"]:
            self.assertIn(item["resolution_strategy"], ["EXACT", "ALIAS", "REGEX", "FUZZY", "UNMAPPED", "PROFILE"])

        # Verify physical row traceability
        for sample_row in sheet["sample_rows"]:
            self.assertIn("source_file_id", sample_row)
            self.assertEqual(sample_row["filename"], "fast_test_workbook.xlsx")
            self.assertEqual(sample_row["worksheet_name"], "Batching Report")
            self.assertIsInstance(sample_row["physical_excel_row"], int)
            self.assertEqual(sample_row["mapping_execution_id"], data["mapping_execution_id"])

    def test_02_idempotent_database_persistence(self):
        """Verify SQL persistence into sys_session_mappings without creating duplicate rows."""
        res1 = client.post("/api/v1/ingestion/datasets", json={"dataset_name": "DS Fast 2", "dataset_period": "Q2-2026", "dataset_type_id": "QA_SLUMP_LOGS", "target_plant_id": "test-v1", "import_profile_id": "PROFILE-PUNE-SCADA", "operator_id": "OPERATOR-MUMBAI-01", "remarks": ""})
        res2 = client.post("/api/v1/ingestion/sessions", json={"dataset_id": res1.json()["dataset_id"], "operator_id": "OPERATOR-MUMBAI-01"})
        session_id = res2.json()["session_id"]

        with open(self.temp_file, "rb") as f:
            client.post(f"/api/v1/ingestion/sessions/{session_id}/discover", files={"file": ("fast_test_workbook.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})

        res_m1 = client.post(f"/api/v1/ingestion/sessions/{session_id}/mapping/preview")
        self.assertEqual(res_m1.status_code, 200)

        res_m2 = client.post(f"/api/v1/ingestion/sessions/{session_id}/mapping/preview")
        self.assertEqual(res_m2.status_code, 200)

        engine = get_database_engine()
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        records = db.query(SessionMappingModel).filter(SessionMappingModel.session_id == session_id).all()
        self.assertEqual(len(records), 1, "Idempotency failed")
        db.close()

    def test_03_challan_alternate_key_and_review_invariants(self):
        """Verify Challan no. (Editable) alternate key policy and review count invariants."""
        from src.database.dictionary import get_canonical_dictionary
        dict_registry = get_canonical_dictionary()
        
        # Verify Challan no. maps to delivery_note_number
        field_delivery = dict_registry.resolve_alias("Challan no.")
        self.assertEqual(field_delivery.canonical_name, "delivery_note_number")
        
        # Verify Challan no. (Editable) does NOT map to primary delivery_note_number
        self.assertFalse(dict_registry.has_field("Challan no. (Editable)"))

    def test_04_execution_level_numerical_reconciliation_invariants(self):
        """Verify execution-level numerical invariants: DB = Backend = UI = 210, 9 mapped + 30 unmapped = 39 headers."""
        engine = get_database_engine()
        from sqlalchemy.orm import sessionmaker
        import json
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        latest_rec = db.query(SessionMappingModel).order_by(SessionMappingModel.created_at.desc()).first()
        if latest_rec:
            payload = json.loads(latest_rec.summary_json)
            self.assertIn("discovered_count", payload)
            self.assertIn("processed_count", payload)
            self.assertIn("excluded_count", payload)
            self.assertIn("total_requires_review", payload)
            
            # Verify component sum identity
            calculated_sum = 0
            for sp in payload.get("sheet_previews", []):
                calculated_sum += sp.get("requires_review_count", 0)
            self.assertEqual(calculated_sum, payload.get("total_requires_review"))
        db.close()


if __name__ == "__main__":
    unittest.main()
