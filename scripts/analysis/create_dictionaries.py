import csv
import json

def build_data_dictionary():
    fields = [
        # Batching & Delivery Fields
        ("batch_id", "UUID", "-", "Unique batch mixing cycle identifier", "Batching Report (PLC Log)", "Database PK, Batch Twin, API, Audit"),
        ("delivery_note_no", "String", "-", "Challan / Dispatch order serial number", "Batching Report Col D / Columns Col A", "Delivery Entity, API, Dashboard"),
        ("plant_code", "String", "-", "Batching plant facility code", "FT7 Form Row 8 / Header", "Multi-Plant MDM, Filter API"),
        ("mix_grade", "String", "-", "Characteristic strength grade (e.g. M-30)", "Batching Report Col C / FT7 Row 12", "Recipe MDM, AI Feature, Dashboard"),
        ("truck_number", "String", "-", "Transit mixer vehicle registration", "Batching Report Col G / FT7 Row 13", "Fleet Management, Delivery API"),
        ("customer_name", "String", "-", "Purchasing commercial client name", "Batching Report Col E / Columns Col H", "Customer MDM, Dashboard Widget"),
        ("project_site", "String", "-", "Destination construction site location", "Batching Report Col F / Columns Col I", "Site MDM, Delivery API"),
        ("load_size_m3", "Decimal", "m3", "Volume of concrete batched in trip", "Batching Report Col I / FT7 Row 14", "Volume Tracking, Dashboard KPI"),
        ("date_of_casting", "Date", "YYYY-MM-DD", "Date concrete was batched and cast", "Batching Report Col A / FT7 Row 9", "Time-series Index, AI Feature"),
        ("time_batched", "Time", "HH:MM:SS", "Precise timestamp of batch mixing", "Batching Report Col B / FT7 Row 8", "Batch Twin Timeline, Audit Log"),
        
        # Material Dosage Fields (Target vs Actual)
        ("cement_target_kg", "Decimal", "kg", "Target specified mass of OPC cement", "Batching Report Col K", "Batch Twin, Variance Alert"),
        ("cement_actual_kg", "Decimal", "kg", "Measured actual mass of OPC dosed", "Batching Report Col L / Forecast Col D", "AI Input Feature (OPC), Batch Twin"),
        ("ggbs_target_kg", "Decimal", "kg", "Target specified mass of GGBS slag", "Batching Report Col M", "Batch Twin, Recipe Compliance"),
        ("ggbs_actual_kg", "Decimal", "kg", "Measured actual mass of GGBS dosed", "Batching Report Col N / Forecast Col E", "AI Input Feature (GGBS), Batch Twin"),
        ("flyash_target_kg", "Decimal", "kg", "Target specified mass of Fly Ash", "Batching Report Col O", "Batch Twin, Variance Engine"),
        ("flyash_actual_kg", "Decimal", "kg", "Measured actual mass of Fly Ash dosed", "Batching Report Col P", "AI Input Feature (FlyAsh), Batch Twin"),
        ("water_target_kg", "Decimal", "kg", "Target specified mixing water mass", "Batching Report Col Q", "Batch Twin, Water Calculator"),
        ("water_actual_kg", "Decimal", "kg", "Measured actual total water added", "Batching Report Col R / Forecast Col G", "AI Input Feature (Water), W/B Ratio"),
        ("admixture_target_kg", "Decimal", "kg", "Target chemical plasticizer dosage", "Batching Report Col S", "Batch Twin, Chemical Metering"),
        ("admixture_actual_kg", "Decimal", "kg", "Measured actual plasticizer dosed", "Batching Report Col T / Forecast Col F", "AI Input Feature (Admixture)"),
        ("agg_20mm_actual_kg", "Decimal", "kg", "Measured actual 20mm aggregate mass", "Batching Report Col U", "Batch Twin, Aggregate Ratio"),
        ("agg_10mm_actual_kg", "Decimal", "kg", "Measured actual 10mm aggregate mass", "Batching Report Col V", "Batch Twin, Aggregate Ratio"),
        ("crushed_sand_actual_kg", "Decimal", "kg", "Measured actual crushed sand mass", "Batching Report Col W", "Batch Twin, Sand Dosage"),
        ("agg_moisture_pct", "Decimal", "%", "Aggregate moisture percentage reading", "Batching Report Col X", "Batch Twin, Water Adjustment"),
        ("moisture_water_adj_kg", "Decimal", "kg", "Calculated water mass adjustment", "Batching Report Col Z", "Batch Twin, Flowmeter Control"),
        
        # Laboratory QA & Physical Cube Testing Fields
        ("plant_slump_mm", "Decimal", "mm", "Measured concrete slump at batch plant", "FT7 Form Row 16", "QA Compliance, Dashboard Slump Gauge"),
        ("site_slump_mm", "Decimal", "mm", "Measured concrete slump at jobsite", "FT7 Form Row 15", "QA Compliance, Delivery Log"),
        ("concrete_temp_c", "Decimal", "°C", "Measured fresh concrete temperature", "FT7 Form Row 17", "AI Feature (Temp), QA Log"),
        ("ambient_temp_c", "Decimal", "°C", "Measured ambient air temperature", "FT7 Form Row 18", "AI Feature (Ambient), QA Log"),
        ("cube_ref_no", "String", "-", "Individual cube specimen identifier", "FT7 Form Row 22", "Cube Specimen PK, QA Register"),
        ("cube_size_mm", "String", "mm", "Cube specimen dimensions (100mm/150mm)", "FT7 Form Row 18", "Area Calculator, QA Register"),
        ("test_age_days", "Integer", "days", "Age of cube at testing (7d or 28d)", "FT7 Form Row 27", "QA Maturity Filter, AI Target Label"),
        ("saturated_mass_kg", "Decimal", "kg", "Mass of saturated cube in air", "FT7 Form Row 28", "Density Calculation, QA Audit"),
        ("failure_load_kn", "Decimal", "kN", "Maximum failure load on testing machine", "FT7 Form Row 31", "Strength Calculation Input"),
        ("compressive_strength_mpa", "Decimal", "MPa", "Calculated specimen compressive strength", "FT7 Form Row 32", "QA Register, AI Ground Truth Label"),
        ("strength_7d", "Decimal", "MPa", "Mean 7-day compressive strength", "FT7 Form Row 34", "QA Signal, Early Predictor"),
        ("strength_28d", "Decimal", "MPa", "Mean 28-day compressive strength", "FT7 Form Row 34 / Forecast Col I", "AI Primary Target Label (y), KPI"),
        ("binder_ratio", "Decimal", "Ratio", "Water-to-Binder mass ratio (W/B)", "Forecast Col H", "AI Feature (W/B), Quality Rule")
    ]
    
    # Save CSV
    csv_path = "/home/sanjana/acc-rmc-ai-platform/Canonical_Data_Dictionary.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(["Canonical Field", "Type", "Unit", "Description", "Source(s)", "Used By"])
        for row in fields:
            writer.writerow(row)
            
    # Save Markdown
    md_path = "/home/sanjana/acc-rmc-ai-platform/Canonical_Data_Dictionary.md"
    with open(md_path, "w", encoding="utf-8") as out:
        out.write("# Canonical Data Dictionary & Field Business Contract\n\n")
        out.write("> **Immutable Contract**: This dictionary establishes the single source of truth for canonical field naming across the Database Schema, REST APIs, AI Feature Store, Reports, and Dashboard Payload Contracts.\n\n")
        out.write("| Canonical Field | Type | Unit | Description | Source(s) | Used By |\n")
        out.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for row in fields:
            out.write(f"| `{row[0]}` | `{row[1]}` | `{row[2]}` | {row[3]} | {row[4]} | {row[5]} |\n")

    print("Canonical Data Dictionary generated!")

def build_business_rules_catalogue():
    rules = [
        ("BR-001", "Characteristic Strength (f_ck)", "The specified minimum compressive strength at 28 days below which not more than 5% of test results are expected to fall.", "Derived from Mix Grade suffix (e.g. M-30 -> f_ck = 30.0 MPa).", "Quality Classification, Compliance Check"),
        ("BR-002", "Target Mean Strength (f_ck')", "Design target compressive strength accounting for standard deviation: f_ck' = f_ck + 1.65 * S. For M-30 (S=4.0), f_ck' = 36.6 MPa.", "Calculated using IS 456 / IS 10262 standard deviation tables.", "Mix Optimizer Constraint, Pass/Hold Rules"),
        ("BR-003", "Water Binder Ratio (W/B)", "Mass ratio of total effective water to sum of all cementitious materials: W/B = Water / (OPC + GGBS + FlyAsh).", "Forecast Col H formula: =G2/(D2+E2). Must strictly satisfy W/B <= 0.45 for durability.", "AI Input Feature, Mix Optimization Boundary"),
        ("BR-004", "Cube Strength Calculation", "Compressive Strength (MPa) = (Failure Load in kN * 1000) / Surface Area in mm2. For 150mm cubes, Area = 22500 mm2.", "FT7 Form Row 32 formula: =B31/22.5.", "QA Specimen Result Engine"),
        ("BR-005", "Strength Gain Ratio (7d to 28d)", "Minimum expected 7-day strength must achieve >= 65% of characteristic strength f_ck.", "QA Laboratory Validation Rule.", "Early Warning Alert, Batch Hold Rule"),
        ("BR-006", "Acceptance Limits (Pass/Hold)", "A batch passes QA if: (1) Mean 28d strength >= f_ck + 3 MPa, and (2) Individual cube strength >= f_ck - 3 MPa.", "IS 456 Quality Control Standard.", "Automated Batch Disposition (PASS/HOLD)"),
        ("BR-007", "Material Dosing Tolerance", "Batching plant material dosing actual vs target tolerance bounds: Cement/Binders <= ±1.0%, Water <= ±1.0%, Aggregates <= ±2.0%, Admixture <= ±3.0%.", "IS 4926 Ready Mixed Concrete Specification.", "Digital Twin Variance Alert"),
        ("BR-008", "Prediction Confidence Score", "Model prediction uncertainty metric derived from prediction interval standard error: Confidence = max(0, 100 - (2 * SE / Target * 100)).", "AI Model Inference Engine.", "Engineering Decision Support Dashboard"),
        ("BR-009", "Similarity Score (Mix Matching)", "Cosine similarity score evaluating historical mix formulation closeness based on normalized OPC, GGBS, Water, and W/B vector distances.", "AI Similarity Search Engine.", "Mix Recipe Recommender"),
        ("BR-010", "Optimization Constraints", "Linear programming optimization objective: Minimize Cost subject to: (1) Strength >= f_ck', (2) W/B <= Max_WB, (3) Slump in target range.", "SLSQP / LP Mix Optimization Engine.", "Composition Optimizer"),
        ("BR-011", "Continuous Learning Trigger", "Automated model retraining pipeline triggers when >= 50 new verified 28-day strength lab results are logged.", "MLOps Event Scheduler.", "Continuous Retraining Pipeline"),
        ("BR-012", "Retraining Trigger (Drift)", "Retraining triggers automatically if Concept Drift score (Kolmogorov-Smirnov test p-value < 0.05) is detected on W/B ratio.", "Model Drift Monitor.", "Model Governance & Registry")
    ]
    
    # Save Markdown
    md_path = "/home/sanjana/acc-rmc-ai-platform/Business_Rules_Catalogue.md"
    with open(md_path, "w", encoding="utf-8") as out:
        out.write("# Immutable Business Rules & Engineering Catalogue\n\n")
        out.write("> **Engineering Standards**: This catalogue freezes all business rules, acceptance thresholds, strength equations, quality disposition criteria, and AI optimization constraints.\n\n")
        out.write("| Rule ID | Rule Name | Description & Mathematical Formula | Source / Standard | Applied System Module |\n")
        out.write("| :--- | :--- | :--- | :--- | :--- |\n")
        for row in rules:
            out.write(f"| `{row[0]}` | **{row[1]}** | {row[2]} | {row[3]} | {row[4]} |\n")

    print("Business Rules Catalogue generated!")

if __name__ == "__main__":
    build_data_dictionary()
    build_business_rules_catalogue()
