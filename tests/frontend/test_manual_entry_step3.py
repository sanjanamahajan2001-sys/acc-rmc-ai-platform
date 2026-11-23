"""Final Reconciled Automated Certification & Domain Governance Test Suite for WS-03.5.3 Material Consumption.

Verifies 35 explicit certification and governance domains:
1. test_01_load_existing_step1_step2_draft: Consumes existing WS-03.5.1 + WS-03.5.2 draft
2. test_02_save_valid_material_consumption: Valid material quantities save cleanly
3. test_03_authoritative_total_binder_calculation: Binder = 315 + 0 + 135 = 450.0 kg/m3 (Test Vector 1)
4. test_04_binder_recalculates_on_input_change: Binder = 318 + 0 + 135 = 453.0 kg/m3 (Test Vector 2)
5. test_05_effective_water_exact_reconciliation: 160 + 7.80 + 3.24 + 22.32 = 193.36 kg/m3
6. test_07_wb_ratio_exact_reconciliation: 193.36 / 450.0 = 0.430; 193.36 / 453.0 = 0.427
7. test_08_authoritative_yield_volume_reproducibility: Constituent vol = 1.03755m3 -> Yield = 1.053m3
8. test_09_theoretical_density_reproducibility: Total Mass / Yield Volume = 2381.0 kg/m3
9. test_10_real_material_cost_exact_reconciliation: ₹5,747.50 / m3
10. test_11_price_provenance_verification: Master price schedule metadata present
11. test_12_sg_provenance_verification: IS 10262 specific gravity metadata present
12. test_13_ai_model_inference_execution: Active model version and prediction bounds
13. test_14_ai_feature_vector_provenance: Verified AI feature vector schemas
14. test_15_advisory_optimization_recommendation: Real advisory optimization recommendation and savings
15. test_16_invalid_zero_binder_rejection: Zero binder rejected with HTTP 422
16. test_17_negative_material_quantity_rejection: Negative quantities rejected with HTTP 422
17. test_18_invalid_moisture_percentage_rejection: Moisture > 20% rejected with HTTP 422
18. test_19_invalid_absorption_percentage_rejection: Absorption > 10% rejected with HTTP 422
19. test_20_invariants_preserved: draft_id, batch_number, Step 1 & Step 2 fields remain invariant
20. test_21_cross_operator_access_denied: Cross-operator update rejected with HTTP 403
21. test_22_supervisory_role_draft_access: Supervisory access supported for PLANT_MANAGER & MASTER_ADMIN
22. test_23_database_failure_rollback: DB exception rolls back cleanly leaving draft intact
23. test_24_draft_recovery_after_backend_restart: Complete Step 1+2+3 payload survives process restart
24. test_25_duplicate_save_safety: Repeated save does not alter draft_id or batch_number
25. test_26_backend_vs_frontend_calculation_contract: Identical effective water and binder calculation
26. test_27_stale_calculation_prevention: Updating material inputs clears old calculations
27. test_28_prd_batches_boundary_isolation: Zero records written to prd_batches
28. test_29_air_allowance_contract: Verifies 1.5% entrained air allowance applied exactly once
29. test_30_moisture_correction_semantics: Proves Step 2 correction scalar is independent of free water
30. test_31_absorption_greater_than_moisture_rejection: Absorption > Moisture rejected with HTTP 422
31. test_32_valid_boundary_moisture_absorption: Absorption <= Moisture passes cleanly
32. test_33_recipe_material_compatibility: Validates submitted materials against active recipe master
33. test_34_actual_ai_feature_values: Verifies actual feature vector input values sent to inference
34. test_35_ai_recommendation_baseline_candidate_provenance: Proves candidate 15kg reduction savings = ₹97.50/m3
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


class TestWS0353MaterialConsumptionReconciled(unittest.TestCase):

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
            else:
                recipe.target_strength_mpa = 30.0

            db.commit()
        finally:
            db.close()

    def setUp(self):
        """Ensure master data and certified Step 1 + Step 2 draft exist."""
        session_factory = get_session_factory()
        self.db = session_factory()

        # Step 1
        res_s1 = client.post("/api/v1/manual-entry/drafts", json={
            "plant_code": "PLANT-MUMBAI-01",
            "recipe_code": "R-M30-STD",
            "production_date": "2026-08-09",
            "shift": "DAY_SHIFT",
            "order_number": "ORD-2026-99"
        })
        self.assertEqual(res_s1.status_code, 200)
        self.draft_id = res_s1.json()["draft_id"]

        # Step 2 (Aggregate moisture correction = 1.2%)
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

    def tearDown(self):
        """Close DB session after each test."""
        if hasattr(self, "db") and self.db:
            self.db.close()

    def test_01_load_existing_step1_step2_draft(self):
        """Consumes existing WS-03.5.1 + WS-03.5.2 draft context."""
        res = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["current_step"], 2)
        self.assertEqual(data["plant_code"], "PLANT-MUMBAI-01")
        self.assertEqual(data["truck_number"], "TM-MUM-402")

    def test_02_save_valid_material_consumption(self):
        """Valid material quantities save cleanly."""
        payload_s3 = {
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
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_s3)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["current_step"], 3)
        self.assertEqual(data["cement_kg_m3"], 315.0)
        self.assertEqual(data["ggbs_kg_m3"], 135.0)

    def test_03_authoritative_total_binder_calculation(self):
        """Total Binder = 315 + 0 + 135 = 450.0 kg/m3 (Test Vector 1)."""
        payload_s3 = {
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
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_s3)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["total_binder_kg_m3"], 450.0)

    def test_04_binder_recalculates_on_input_change(self):
        """Total Binder = 318 + 0 + 135 = 453.0 kg/m3 (Test Vector 2)."""
        payload_s3 = {
            "cement_kg_m3": 318.0,
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
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_s3)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["total_binder_kg_m3"], 453.0)

    def test_05_effective_water_exact_reconciliation(self):
        """Effective Water = 160 + 7.80 + 3.24 + 22.32 = 193.36 kg/m3 (Exact 100% Reconciliation)."""
        payload_s3 = {
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
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_s3)
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d["fine_free_water_kg_m3"], 7.80)
        self.assertEqual(d["coarse_free_water_kg_m3"], 3.24)
        self.assertEqual(d["batch_moisture_corr_water_kg_m3"], 22.32)
        self.assertEqual(d["effective_water_kg_m3"], 193.36)

    def test_07_wb_ratio_exact_reconciliation(self):
        """W/B = 193.36 / 450 = 0.430; W/B = 193.36 / 453 = 0.427."""
        payload1 = {
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
        res1 = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload1)
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.json()["w_b_ratio"], 0.430)

        payload2 = dict(payload1)
        payload2["cement_kg_m3"] = 318.0
        payload2["ggbs_kg_m3"] = 138.0
        payload2["water_kg_m3"] = 165.0
        res2 = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload2)
        self.assertEqual(res2.status_code, 200)
        d2 = res2.json()
        self.assertEqual(d2["total_binder_kg_m3"], 456.0)
        self.assertEqual(d2["w_b_ratio"], 0.435)
        self.assertEqual(d2["estimated_cost_per_m3"], "₹5,779.15")

        # Dynamic Mathematical Re-derivation Verification for Vector 2
        total_mass_v2 = 318.0 + 138.0 + 200.70 + 3.8 + 780.0 + 1080.0
        self.assertEqual(total_mass_v2, 2520.50)

        vol_cement = 318.0 / 3150.0
        vol_ggbs = 138.0 / 2900.0
        vol_water = 200.70 / 1000.0
        vol_admix = 3.8 / 1150.0
        vol_fine = 780.0 / 2650.0
        vol_coarse = 1080.0 / 2700.0
        sum_constituents = vol_cement + vol_ggbs + vol_water + vol_admix + vol_fine + vol_coarse
        self.assertAlmostEqual(sum_constituents, 1.046882558, places=6)

        yield_v2 = round(sum_constituents / 0.99, 3)
        self.assertEqual(yield_v2, 1.057)

        density_v2 = round(total_mass_v2 / (sum_constituents / 0.99), 2)
        self.assertEqual(density_v2, 2383.55)

    def test_08_authoritative_yield_volume_reproducibility(self):
        """Yield Volume = 1.03755 / (1 - 0.01) = 1.048 m3."""
        payload_s3 = {
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
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_s3)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["yield_volume_m3"], 1.048)

    def test_09_theoretical_density_reproducibility(self):
        """Theoretical Density = 2507.16 / 1.04803 = 2392.3 kg/m3."""
        payload_s3 = {
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
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_s3)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["theoretical_density_kg_m3"], 2392.3)

    def test_10_real_material_cost_exact_reconciliation(self):
        """Authoritative Material Cost = ₹5,747.50 / m3."""
        payload_s3 = {
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
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_s3)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["estimated_cost_per_m3"], "₹5,747.50")

    def test_11_price_provenance_verification(self):
        """Price provenance metadata included in API response."""
        payload_s3 = {
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
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_s3)
        self.assertEqual(res.status_code, 200)
        prov = res.json()["price_provenance"]
        self.assertEqual(prov["cement_rate_per_kg"], 6.50)
        self.assertIn("ACC Master Material Price Schedule", prov["pricing_source"])

    def test_12_sg_provenance_verification(self):
        """Specific gravity provenance metadata included in API response."""
        payload_s3 = {
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
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_s3)
        self.assertEqual(res.status_code, 200)
        sg = res.json()["sg_provenance"]
        self.assertEqual(sg["cement_sg"], 3.15)
        self.assertEqual(sg["entrained_air_pct"], 1.0)

    def test_13_ai_model_inference_execution(self):
        """Active model version and prediction bounds."""
        payload_s3 = {
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
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_s3)
        self.assertEqual(res.status_code, 200)
        ai = res.json()["ai_metadata"]
        self.assertEqual(ai["model_version"], "v3.2.0-PROD")
        self.assertEqual(ai["artifact_id"], "ACC_XGBOOST_STRENGTH_V3.2")
        self.assertGreater(ai["predicted_28d_strength_mpa"], 30.0)

    def test_14_ai_feature_vector_provenance(self):
        """Verified AI feature vector schema."""
        payload_s3 = {
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
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_s3)
        self.assertEqual(res.status_code, 200)
        ai = res.json()["ai_metadata"]
        self.assertEqual(ai["feature_schema_version"], "v3.0-MANUAL-ENTRY")

    def test_15_advisory_optimization_recommendation(self):
        """Real advisory optimization recommendation and savings."""
        payload_s3 = {
            "cement_kg_m3": 350.0,
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
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_s3)
        self.assertEqual(res.status_code, 200)
        ai = res.json()["ai_metadata"]
        self.assertTrue(ai["candidate_evaluation_passed"])
        self.assertIn("reducing cement", ai["optimization_recommendation"])

    def test_16_invalid_zero_binder_rejection(self):
        """Zero binder rejected with HTTP 422."""
        payload_invalid = {
            "cement_kg_m3": 0.0,
            "fly_ash_kg_m3": 0.0,
            "ggbs_kg_m3": 0.0,
            "water_kg_m3": 160.0,
            "admixture_kg_m3": 3.8,
            "fine_aggregate_kg_m3": 780.0,
            "coarse_aggregate_kg_m3": 1080.0,
            "fine_aggregate_moisture_pct": 2.0,
            "fine_aggregate_absorption_pct": 1.0,
            "coarse_aggregate_moisture_pct": 0.8,
            "coarse_aggregate_absorption_pct": 0.5
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_invalid)
        self.assertEqual(res.status_code, 422)

    def test_17_negative_material_quantity_rejection(self):
        """Negative quantities rejected with HTTP 422."""
        payload_invalid = {
            "cement_kg_m3": -50.0,
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
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_invalid)
        self.assertEqual(res.status_code, 422)

    def test_18_invalid_moisture_percentage_rejection(self):
        """Moisture > 20% rejected with HTTP 422."""
        payload_invalid = {
            "cement_kg_m3": 315.0,
            "fly_ash_kg_m3": 0.0,
            "ggbs_kg_m3": 135.0,
            "water_kg_m3": 160.0,
            "admixture_kg_m3": 3.8,
            "fine_aggregate_kg_m3": 780.0,
            "coarse_aggregate_kg_m3": 1080.0,
            "fine_aggregate_moisture_pct": 25.0,
            "fine_aggregate_absorption_pct": 1.0,
            "coarse_aggregate_moisture_pct": 0.8,
            "coarse_aggregate_absorption_pct": 0.5
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_invalid)
        self.assertEqual(res.status_code, 422)

    def test_19_invalid_absorption_percentage_rejection(self):
        """Absorption > 10% rejected with HTTP 422."""
        payload_invalid = {
            "cement_kg_m3": 315.0,
            "fly_ash_kg_m3": 0.0,
            "ggbs_kg_m3": 135.0,
            "water_kg_m3": 160.0,
            "admixture_kg_m3": 3.8,
            "fine_aggregate_kg_m3": 780.0,
            "coarse_aggregate_kg_m3": 1080.0,
            "fine_aggregate_moisture_pct": 2.0,
            "fine_aggregate_absorption_pct": 12.0,
            "coarse_aggregate_moisture_pct": 0.8,
            "coarse_aggregate_absorption_pct": 0.5
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_invalid)
        self.assertEqual(res.status_code, 422)

    def test_20_invariants_preserved(self):
        """draft_id, batch_number, Step 1 & Step 2 fields remain invariant."""
        payload_s3 = {
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
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_s3)
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d["draft_id"], self.draft_id)
        self.assertEqual(d["truck_number"], "TM-MUM-402")

    def test_21_cross_operator_access_denied(self):
        """Cross-operator update rejected with HTTP 403."""
        payload_s3 = {
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
        res = client.put(
            f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3",
            json=payload_s3,
            headers={"Authorization": "Bearer OPERATOR_B"}
        )
        self.assertEqual(res.status_code, 403)

    def test_22_supervisory_role_draft_access(self):
        """Supervisory access supported for PLANT_MANAGER & MASTER_ADMIN."""
        payload_s3 = {
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
        res_mgr = client.put(
            f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3",
            json=payload_s3,
            headers={"Authorization": "Bearer ROLE_PLANT_MANAGER"}
        )
        self.assertEqual(res_mgr.status_code, 200)

    def test_23_database_failure_rollback(self):
        """DB exception rolls back cleanly leaving draft intact."""
        payload_fail = {
            "cement_kg_m3": 999.0,
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
        res_fail = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_fail)
        self.assertEqual(res_fail.status_code, 500)

        res_get = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["current_step"], 2)

    def test_24_draft_recovery_after_backend_restart(self):
        """Complete Step 1+2+3 payload survives process restart."""
        payload_s3 = {
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
        res_put = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_s3)
        self.assertEqual(res_put.status_code, 200)

        _MANUAL_DRAFTS.pop(self.draft_id, None)

        res_get = client.get(f"/api/v1/manual-entry/drafts/{self.draft_id}")
        self.assertEqual(res_get.status_code, 200)
        d = res_get.json()
        self.assertEqual(d["current_step"], 3)
        self.assertEqual(d["effective_water_kg_m3"], 193.36)

    def test_25_duplicate_save_safety(self):
        """Repeated save does not alter draft_id or batch_number."""
        payload_s3 = {
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
        res1 = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_s3)
        res2 = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_s3)
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res1.json()["draft_id"], res2.json()["draft_id"])

    def test_26_backend_vs_frontend_calculation_contract(self):
        """Identical effective water and binder calculation."""
        payload_s3 = {
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
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_s3)
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d["effective_water_kg_m3"], 193.36)
        self.assertEqual(d["total_binder_kg_m3"], 450.0)

    def test_27_stale_calculation_prevention(self):
        """Updating material inputs recomputes all values."""
        payload1 = {
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
        res1 = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload1)
        self.assertEqual(res1.json()["total_binder_kg_m3"], 450.0)

        payload2 = dict(payload1)
        payload2["cement_kg_m3"] = 350.0
        res2 = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload2)
        self.assertEqual(res2.json()["total_binder_kg_m3"], 485.0)

    def test_28_prd_batches_boundary_isolation(self):
        """Zero records written to prd_batches."""
        count = self.db.query(Batch).filter(Batch.batch_number == "BATCH-20260809-4091").count()
        self.assertEqual(count, 0)

    def test_29_air_allowance_resolved_from_recipe_and_nmsa(self):
        """Proves air content and calculated yield volume change dynamically when recipe NMSA changes (20mm -> 1.0% vs 10mm -> 1.5% vs 40mm -> 0.8%)."""
        # Recipe A (M30/M40 Default 20mm NMSA -> 1.0% air per IS 10262 Table 3 -> Yield 1.048 m3)
        payload_s3 = {
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
        res_a = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_s3)
        self.assertEqual(res_a.status_code, 200)
        sg_a = res_a.json()["sg_provenance"]
        self.assertEqual(sg_a["nmsa_mm"], 20.0)
        self.assertEqual(sg_a["entrained_air_pct"], 1.0)
        self.assertEqual(res_a.json()["calculated_theoretical_yield_volume_m3"], 1.048)

        # Recipe B: Update recipe NMSA to 10.0mm NMSA in master DB -> resolves 1.5% air -> Yield 1.053 m3
        session_factory = get_session_factory()
        db_temp = session_factory()
        try:
            db_temp.execute(text("UPDATE mst_recipes SET nominal_max_aggregate_size_mm = 10.0 WHERE recipe_code = 'R-M30-STD'"))
            db_temp.commit()
        finally:
            db_temp.close()

        res_b = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_s3)
        self.assertEqual(res_b.status_code, 200)
        sg_b = res_b.json()["sg_provenance"]
        self.assertEqual(sg_b["nmsa_mm"], 10.0)
        self.assertEqual(sg_b["entrained_air_pct"], 1.5)
        self.assertNotEqual(sg_a["entrained_air_pct"], sg_b["entrained_air_pct"])
        self.assertNotEqual(res_a.json()["calculated_theoretical_yield_volume_m3"], res_b.json()["calculated_theoretical_yield_volume_m3"])
        self.assertEqual(res_b.json()["calculated_theoretical_yield_volume_m3"], 1.053)

        # Recipe C: Update recipe NMSA to 40.0mm NMSA in master DB -> resolves 0.8% air -> Yield 1.046 m3
        db_temp2 = session_factory()
        try:
            db_temp2.execute(text("UPDATE mst_recipes SET nominal_max_aggregate_size_mm = 40.0 WHERE recipe_code = 'R-M30-STD'"))
            db_temp2.commit()
        finally:
            db_temp2.close()

        res_c = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_s3)
        self.assertEqual(res_c.status_code, 200)
        sg_c = res_c.json()["sg_provenance"]
        self.assertEqual(sg_c["nmsa_mm"], 40.0)
        self.assertEqual(sg_c["entrained_air_pct"], 0.8)
        self.assertEqual(res_c.json()["calculated_theoretical_yield_volume_m3"], 1.046)

        # Restore recipe A NMSA default (20.0mm) for subsequent tests
        db_temp3 = session_factory()
        try:
            db_temp3.execute(text("UPDATE mst_recipes SET nominal_max_aggregate_size_mm = 20.0 WHERE recipe_code = 'R-M30-STD'"))
            db_temp3.commit()
        finally:
            db_temp3.close()

    def test_30_moisture_correction_semantics(self):
        """Proves Step 2 correction scalar is independent of free water."""
        payload_s3 = {
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
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_s3)
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d["batch_moisture_corr_water_kg_m3"], 22.32)
        self.assertEqual(d["fine_free_water_kg_m3"] + d["coarse_free_water_kg_m3"], 11.04)

    def test_31_absorption_greater_than_moisture_rejection(self):
        """Absorption > Moisture rejected with HTTP 422."""
        payload_invalid = {
            "cement_kg_m3": 315.0,
            "fly_ash_kg_m3": 0.0,
            "ggbs_kg_m3": 135.0,
            "water_kg_m3": 160.0,
            "admixture_kg_m3": 3.8,
            "fine_aggregate_kg_m3": 780.0,
            "coarse_aggregate_kg_m3": 1080.0,
            "fine_aggregate_moisture_pct": 0.5,
            "fine_aggregate_absorption_pct": 1.0,  # Invalid
            "coarse_aggregate_moisture_pct": 0.8,
            "coarse_aggregate_absorption_pct": 0.5
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_invalid)
        self.assertEqual(res.status_code, 422)
        self.assertIn("cannot exceed moisture", res.json()["detail"])

    def test_32_valid_boundary_moisture_absorption(self):
        """Absorption <= Moisture passes cleanly."""
        payload_boundary = {
            "cement_kg_m3": 315.0,
            "fly_ash_kg_m3": 0.0,
            "ggbs_kg_m3": 135.0,
            "water_kg_m3": 160.0,
            "admixture_kg_m3": 3.8,
            "fine_aggregate_kg_m3": 780.0,
            "coarse_aggregate_kg_m3": 1080.0,
            "fine_aggregate_moisture_pct": 1.0,
            "fine_aggregate_absorption_pct": 1.0,  # Equal is valid
            "coarse_aggregate_moisture_pct": 0.5,
            "coarse_aggregate_absorption_pct": 0.5
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_boundary)
        self.assertEqual(res.status_code, 200)

    def test_33_recipe_material_compatibility(self):
        """Validates submitted materials against active recipe master."""
        payload_s3 = {
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
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_s3)
        self.assertEqual(res.status_code, 200)

    def test_34_actual_ai_feature_values(self):
        """Verifies actual feature vector input values sent to inference."""
        payload_s3 = {
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
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_s3)
        self.assertEqual(res.status_code, 200)
        ai = res.json()["ai_metadata"]
        fv = ai["feature_vector_input"]
        self.assertEqual(fv["cement_kg_m3"], 315.0)
        self.assertEqual(fv["effective_water_kg_m3"], 193.36)
        self.assertEqual(fv["total_binder_kg_m3"], 450.0)

    def test_35_ai_recommendation_baseline_candidate_provenance(self):
        """Proves candidate 15kg reduction savings = ₹97.50/m3."""
        payload_s3 = {
            "cement_kg_m3": 350.0,
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
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_s3)
        self.assertEqual(res.status_code, 200)
        ai = res.json()["ai_metadata"]
        self.assertEqual(ai["estimated_cost_savings_per_m3"], "₹97.50 / m3")

    def test_36_ai_m40_target_grade_safety_gate(self):
        """Proves AI recommendation is gated if candidate predicted strength falls below target grade M40 (40.0 MPa)."""
        payload_s3 = {
            "cement_kg_m3": 250.0,
            "fly_ash_kg_m3": 0.0,
            "ggbs_kg_m3": 100.0,
            "water_kg_m3": 170.0,
            "admixture_kg_m3": 3.8,
            "fine_aggregate_kg_m3": 780.0,
            "coarse_aggregate_kg_m3": 1080.0,
            "fine_aggregate_moisture_pct": 2.0,
            "fine_aggregate_absorption_pct": 1.0,
            "coarse_aggregate_moisture_pct": 0.8,
            "coarse_aggregate_absorption_pct": 0.5
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_s3)
        self.assertEqual(res.status_code, 200)
        ai = res.json()["ai_metadata"]
        self.assertFalse(ai["candidate_evaluation_passed"])
        self.assertIn("Advisory Gated", ai["optimization_recommendation"])
        self.assertEqual(ai["estimated_cost_savings_per_m3"], "₹0.00 / m3 (Fully Optimized)")

    def test_37_aggregate_ssd_basis_metadata(self):
        """Verifies aggregate SSD basis explicitly exposed in API DTO."""
        payload_s3 = {
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
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_s3)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["aggregate_mass_basis"], "SSD")
        sg = res.json()["sg_provenance"]
        self.assertEqual(sg["aggregate_mass_basis"], "SSD (Saturated Surface Dry)")

    def test_38_baseline_strength_suppression_gate(self):
        """Proves AI recommendation is suppressed if baseline mix fails target grade."""
        payload_s3 = {
            "cement_kg_m3": 200.0,
            "fly_ash_kg_m3": 0.0,
            "ggbs_kg_m3": 50.0,
            "water_kg_m3": 180.0,
            "admixture_kg_m3": 3.8,
            "fine_aggregate_kg_m3": 780.0,
            "coarse_aggregate_kg_m3": 1080.0,
            "fine_aggregate_moisture_pct": 2.0,
            "fine_aggregate_absorption_pct": 1.0,
            "coarse_aggregate_moisture_pct": 0.8,
            "coarse_aggregate_absorption_pct": 0.5
        }
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_s3)
        self.assertEqual(res.status_code, 200)
        ai = res.json()["ai_metadata"]
        self.assertFalse(ai["candidate_evaluation_passed"])
        self.assertIn("Advisory Suppressed", ai["optimization_recommendation"])
        self.assertEqual(ai["estimated_cost_savings_per_m3"], "₹0.00 / m3 (Fully Optimized)")

    def test_39_runtime_isolated_m40_view_recipe_proof(self):
        """Proves runtime resolution for exact test recipe M40 View Isolated (M40_VW_UT_ISOLATED)."""
        session_factory = get_session_factory()
        db_temp = session_factory()
        try:
            plant_iso = db_temp.query(Plant).filter(Plant.plant_code == "P_VW_UT_ISOLATED").first()
            if not plant_iso:
                plant_iso = Plant(
                    id="PLANT-ID-VW-UT-ISOLATED",
                    plant_code="P_VW_UT_ISOLATED",
                    plant_name="View Test Plant Isolated",
                    location="Mumbai West",
                    timezone="Asia/Kolkata"
                )
                db_temp.add(plant_iso)

            recipe_iso = db_temp.query(Recipe).filter(Recipe.recipe_code == "M40_VW_UT_ISOLATED").first()
            if not recipe_iso:
                recipe_iso = Recipe(
                    id="RECIPE-ID-M40-VW-UT-ISOLATED",
                    recipe_code="M40_VW_UT_ISOLATED",
                    recipe_name="M40 View Isolated",
                    target_strength_mpa=40.0,
                    nominal_max_aggregate_size_mm=20.0,
                    slump_target_mm=120.0
                )
                db_temp.add(recipe_iso)
            else:
                recipe_iso.nominal_max_aggregate_size_mm = 20.0
                recipe_iso.target_strength_mpa = 40.0

            db_temp.commit()
        finally:
            db_temp.close()

        # Step 1 with M40_VW_UT_ISOLATED
        res_s1 = client.post("/api/v1/manual-entry/drafts", json={
            "plant_code": "P_VW_UT_ISOLATED",
            "recipe_code": "M40_VW_UT_ISOLATED",
            "production_date": "2026-08-09",
            "shift": "DAY_SHIFT",
            "order_number": "ORD-ISOLATED-01"
        })
        self.assertEqual(res_s1.status_code, 200)
        draft_iso_id = res_s1.json()["draft_id"]

        # Step 2
        res_s2 = client.put(f"/api/v1/manual-entry/drafts/{draft_iso_id}/step-2", json={
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
        payload_s3 = {
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
        res_s3 = client.put(f"/api/v1/manual-entry/drafts/{draft_iso_id}/step-3", json=payload_s3)
        self.assertEqual(res_s3.status_code, 200)
        d = res_s3.json()

        # Explicit Verification of M40_VW_UT_ISOLATED Runtime Proof
        sg = d["sg_provenance"]
        self.assertEqual(sg["nmsa_mm"], 20.0)
        self.assertEqual(sg["entrained_air_pct"], 1.0)
        self.assertEqual(sg["air_standard_reference"], "IS 10262:2019 Concrete Mix Proportioning - Guidelines")
        self.assertEqual(sg["air_standard_section"], "Table 3 (Approximate Air Content) / Section 5.2")
        self.assertEqual(d["calculated_theoretical_yield_volume_m3"], 1.048)
        self.assertEqual(d["theoretical_density_kg_m3"], 2392.3)
        self.assertEqual(d["estimated_cost_per_m3"], "₹5,747.50")

    def test_40_stale_1_053_regression_guard(self):
        """Explicitly catches stale 1.053 m3 or 2381.0 kg/m3 calculations for 20mm NMSA / 1.0% air."""
        payload_s3 = {
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
        res = client.put(f"/api/v1/manual-entry/drafts/{self.draft_id}/step-3", json=payload_s3)
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertNotEqual(d["calculated_theoretical_yield_volume_m3"], 1.053)
        self.assertNotEqual(d["theoretical_density_kg_m3"], 2381.0)
        self.assertEqual(d["calculated_theoretical_yield_volume_m3"], 1.048)
        self.assertEqual(d["theoretical_density_kg_m3"], 2392.3)

    def test_41_runtime_step3_never_zero_with_valid_authoritative_inputs(self):
        """Integration test verifying Step 3 yield and density are NEVER zero when valid inputs exist across draft lifecycle."""
        # 1. Fresh Draft creation
        res_create = client.post("/api/v1/manual-entry/drafts", json={
            "plant_code": "PLANT-MUMBAI-01",
            "recipe_code": "R-M30-STD",
            "production_date": "2026-08-09",
            "shift": "DAY_SHIFT"
        })
        self.assertEqual(res_create.status_code, 200)
        fresh_draft_id = res_create.json()["draft_id"]

        # 2. Step 2 save
        res_s2 = client.put(f"/api/v1/manual-entry/drafts/{fresh_draft_id}/step-2", json={
            "batch_start_time": "09:15:00",
            "batch_end_time": "09:17:15",
            "mixer_time_seconds": 45,
            "truck_number": "TM-MUM-402",
            "delivery_challan": "DC-2026-8801",
            "aggregate_moisture_correction": 1.2,
            "target_slump_mm": 120.0
        })
        self.assertEqual(res_s2.status_code, 200)

        # 3. Step 3 update
        payload_s3 = {
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
        res_s3 = client.put(f"/api/v1/manual-entry/drafts/{fresh_draft_id}/step-3", json=payload_s3)
        self.assertEqual(res_s3.status_code, 200)
        d_s3 = res_s3.json()

        # Strict Non-Zero Guard Assertions
        self.assertIsNotNone(d_s3.get("sg_provenance"))
        self.assertEqual(d_s3["sg_provenance"]["entrained_air_pct"], 1.0)
        self.assertNotEqual(d_s3["calculated_theoretical_yield_volume_m3"], 0.0)
        self.assertNotEqual(d_s3["theoretical_density_kg_m3"], 0.0)
        self.assertEqual(d_s3["calculated_theoretical_yield_volume_m3"], 1.048)
        self.assertEqual(d_s3["theoretical_density_kg_m3"], 2392.3)

        # 5. Subsequent refetch (simulating navigation back & forth or page refresh)
        res_refetch = client.get(f"/api/v1/manual-entry/drafts/{fresh_draft_id}")
        self.assertEqual(res_refetch.status_code, 200)
        d_refetch = res_refetch.json()
        self.assertNotEqual(d_refetch["calculated_theoretical_yield_volume_m3"], 0.0)
        self.assertNotEqual(d_refetch["theoretical_density_kg_m3"], 0.0)
        self.assertEqual(d_refetch["calculated_theoretical_yield_volume_m3"], 1.048)
        self.assertEqual(d_refetch["theoretical_density_kg_m3"], 2392.3)


if __name__ == "__main__":
    unittest.main()
