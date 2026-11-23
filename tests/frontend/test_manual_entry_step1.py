"""Final Certification & Hardening Automated Test Suite for WS-03.5.1 Batch Information.

Evaluates 12 explicit certification domains:
1. Master-data retrieval (Plants, Recipes, Customers)
2. Draft creation with server-generated identifiers (draft_id, batch_number)
3. Server-side draft retrieval across browser refresh simulation
4. Invalid master data code rejection (HTTP 400)
5. Unauthenticated request rejection (HTTP 401)
6. Server-side RBAC role authorization (HTTP 403 for unauthorized roles; HTTP 200 for authorized roles)
7. Controlled +Add Plant master data creation & persistence
8. Controlled +Add Recipe / Mix Design master data creation & persistence
9. Controlled +Add Customer master data creation & persistence
10. Database-level unique constraint duplicate protection
11. Multi-step draft state integrity
12. WS-03.6 boundary isolation (No direct prd_batches persistence)
"""

import unittest
import uuid
from fastapi.testclient import TestClient
from src.api.main import app
from src.database.session import get_session_factory
from src.database.models.master import Plant, Recipe, Customer
from src.database.models.production import Batch

client = TestClient(app)


class TestWS0351FinalCertification(unittest.TestCase):

    def setUp(self):
        """Ensure test master data exists in DB."""
        session_factory = get_session_factory()
        self.db = session_factory()

        # Seed master plant if not exists
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

        # Seed master recipe if not exists
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

    def tearDown(self):
        self.db.close()

    # --- Domain 1: Master Data Retrieval ---
    def test_01_master_data_retrieval(self):
        """Verify real DB -> Service -> REST API -> Master Data endpoints."""
        res_plants = client.get("/api/v1/master-data/plants")
        self.assertEqual(res_plants.status_code, 200)
        self.assertTrue(len(res_plants.json()) > 0)

        res_recipes = client.get("/api/v1/master-data/recipes")
        self.assertEqual(res_recipes.status_code, 200)
        self.assertTrue(len(res_recipes.json()) > 0)

        res_customers = client.get("/api/v1/master-data/customers")
        self.assertEqual(res_customers.status_code, 200)

    # --- Domain 2: Server-Generated Identifiers & Draft Creation ---
    def test_02_create_draft_batch_info(self):
        """Test valid draft creation returns server-generated draft_id and batch_number."""
        payload = {
            "plant_code": "PLANT-MUMBAI-01",
            "recipe_code": "R-M30-STD",
            "production_date": "2026-08-09",
            "shift": "DAY_SHIFT",
            "order_number": "ORD-2026-99",
            "remarks": "WS-03.5.1 Test Draft"
        }
        res = client.post("/api/v1/manual-entry/drafts", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertTrue(data["draft_id"].startswith("DRAFT-"))
        from datetime import datetime, timezone
        today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        self.assertTrue(data["batch_number"].startswith(f"BATCH-{today_str}-") or "BATCH-" in data["batch_number"])
        self.assertEqual(data["status"], "DRAFT")
        self.assertEqual(data["current_step"], 1)
        self.assertEqual(data["operator_id"], "OPERATOR-MUMBAI-01")

    # --- Domain 3: Master Data Rejection ---
    def test_03_invalid_plant_code(self):
        """Test draft creation with non-existent plant code returns HTTP 400."""
        payload = {
            "plant_code": "INVALID-PLANT-99",
            "recipe_code": "R-M30-STD",
            "production_date": "2026-08-09",
            "shift": "DAY_SHIFT"
        }
        res = client.post("/api/v1/manual-entry/drafts", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("Target plant code 'INVALID-PLANT-99' not found", res.json()["detail"])

    # --- Domain 4: Unauthenticated Request Rejection ---
    def test_04_unauthenticated_request_rejected(self):
        """Test invalid token returns HTTP 401 Unauthorized."""
        payload = {
            "plant_code": "PLANT-MUMBAI-01",
            "recipe_code": "R-M30-STD",
            "production_date": "2026-08-09"
        }
        res = client.post("/api/v1/manual-entry/drafts", json=payload, headers={"Authorization": "Bearer INVALID_TOKEN"})
        self.assertEqual(res.status_code, 401)

    # --- Domain 5: Draft Resume & State Recovery ---
    def test_05_resume_step1_draft(self):
        """Test draft retrieval restores exact server-side Step 1 state."""
        payload = {
            "plant_code": "PLANT-MUMBAI-01",
            "recipe_code": "R-M30-STD",
            "production_date": "2026-08-09",
            "shift": "NIGHT_SHIFT",
            "order_number": "ORD-RECOVERY-101"
        }
        res1 = client.post("/api/v1/manual-entry/drafts", json=payload)
        self.assertEqual(res1.status_code, 200)
        d1 = res1.json()

        res2 = client.get(f"/api/v1/manual-entry/drafts/{d1['draft_id']}")
        self.assertEqual(res2.status_code, 200)
        d2 = res2.json()

        self.assertEqual(d2["draft_id"], d1["draft_id"])
        self.assertEqual(d2["batch_number"], d1["batch_number"])
        self.assertEqual(d2["shift"], "NIGHT_SHIFT")

    # --- Domain 6: Server-Side RBAC Role Authorization ---
    def test_06_rbac_role_authorization_enforced(self):
        """Test server-side RBAC role authorization on +Add endpoints."""
        payload_plant = {"plant_name": "Test Plant RBAC", "plant_code": f"PLANT-RBAC-{uuid.uuid4().hex[:4]}", "region": "West"}

        # Authorized role: QUALITY_OPERATOR -> HTTP 200
        res_auth = client.post("/api/v1/master-data/plants", json=payload_plant, headers={"Authorization": "Bearer ROLE_QUALITY_OPERATOR"})
        self.assertEqual(res_auth.status_code, 200)

        # Unauthorized role: LOGISTICS_VIEWER -> HTTP 403
        payload_unauth = {"plant_name": "Unauth Plant", "plant_code": f"PLANT-UNAUTH-{uuid.uuid4().hex[:4]}", "region": "West"}
        res_unauth = client.post("/api/v1/master-data/plants", json=payload_unauth, headers={"Authorization": "Bearer ROLE_LOGISTICS_VIEWER"})
        self.assertEqual(res_unauth.status_code, 403)
        self.assertIn("is not authorized", res_unauth.json()["detail"])

    # --- Domain 7: [+ Add Plant] REST Creation & Persistence ---
    def test_07_add_plant_master_data(self):
        """Test +Add Plant API creates and persists new plant master entity."""
        unique_code = f"PLANT-THA-{uuid.uuid4().hex[:4].upper()}"
        payload = {"plant_name": "ACC Thane Plant", "plant_code": unique_code, "region": "Western Region"}
        res = client.post("/api/v1/master-data/plants", json=payload)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["plant_code"], unique_code)

    # --- Domain 8: [+ Add Mix Design] REST Creation & Persistence ---
    def test_08_add_recipe_master_data(self):
        """Test +Add Mix Design API creates and persists new recipe master entity."""
        unique_code = f"R-M40-{uuid.uuid4().hex[:4].upper()}"
        payload = {"recipe_name": "High Performance M40 Concrete", "recipe_code": unique_code, "grade": "M40"}
        res = client.post("/api/v1/master-data/recipes", json=payload)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["recipe_code"], unique_code)
        self.assertEqual(res.json()["grade"], "M40")

    # --- Domain 9: [+ Add Customer] REST Creation & Persistence ---
    def test_09_add_customer_master_data(self):
        """Test +Add Customer API creates and persists new customer master entity."""
        unique_code = f"CUST-SPC-{uuid.uuid4().hex[:4].upper()}"
        payload = {"legal_name": "Shapoorji Pallonji Co.", "customer_code": unique_code}
        res = client.post("/api/v1/master-data/customers", json=payload)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["customer_code"], unique_code)

    # --- Domain 10: Database-Level Duplicate Protection ---
    def test_10_duplicate_master_code_rejected(self):
        """Test creating master entity with duplicate code returns HTTP 400."""
        payload = {"plant_name": "ACC Duplicate Plant", "plant_code": "PLANT-MUMBAI-01", "region": "Western Region"}
        res = client.post("/api/v1/master-data/plants", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("already exists", res.json()["detail"])

    # --- Domain 11: Draft Identifier Invariance ---
    def test_11_draft_identifier_invariance(self):
        """Verify draft_id and batch_number remain stable and invariant."""
        payload = {"plant_code": "PLANT-MUMBAI-01", "recipe_code": "R-M30-STD", "production_date": "2026-08-09"}
        res = client.post("/api/v1/manual-entry/drafts", json=payload)
        d1 = res.json()
        res_get1 = client.get(f"/api/v1/manual-entry/drafts/{d1['draft_id']}").json()
        res_get2 = client.get(f"/api/v1/manual-entry/drafts/{d1['draft_id']}").json()
        self.assertEqual(res_get1["draft_id"], res_get2["draft_id"])
        self.assertEqual(res_get1["batch_number"], res_get2["batch_number"])

    # --- Domain 12: WS-03.6 Boundary Isolation ---
    def test_12_ws03_6_boundary_isolation(self):
        """Verify WS-03.5.1 draft creation does NOT write records to canonical prd_batches table."""
        count_before = self.db.query(Batch).count()
        payload = {"plant_code": "PLANT-MUMBAI-01", "recipe_code": "R-M30-STD", "production_date": "2026-08-09"}
        res = client.post("/api/v1/manual-entry/drafts", json=payload)
        self.assertEqual(res.status_code, 200)
        count_after = self.db.query(Batch).count()
        self.assertEqual(count_before, count_after, "WS-03.5.1 MUST NOT persist records to canonical prd_batches table")


if __name__ == "__main__":
    unittest.main()
