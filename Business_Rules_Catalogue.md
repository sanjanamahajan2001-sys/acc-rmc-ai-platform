# Immutable Business Rules & Engineering Catalogue

> **Engineering Standards**: This catalogue freezes all business rules, acceptance thresholds, strength equations, quality disposition criteria, and AI optimization constraints.

| Rule ID | Rule Name | Description & Mathematical Formula | Source / Standard | Applied System Module |
| :--- | :--- | :--- | :--- | :--- |
| `BR-001` | **Characteristic Strength (f_ck)** | The specified minimum compressive strength at 28 days below which not more than 5% of test results are expected to fall. | Derived from Mix Grade suffix (e.g. M-30 -> f_ck = 30.0 MPa). | Quality Classification, Compliance Check |
| `BR-002` | **Target Mean Strength (f_ck')** | Design target compressive strength accounting for standard deviation: f_ck' = f_ck + 1.65 * S. For M-30 (S=4.0), f_ck' = 36.6 MPa. | Calculated using IS 456 / IS 10262 standard deviation tables. | Mix Optimizer Constraint, Pass/Hold Rules |
| `BR-003` | **Water Binder Ratio (W/B)** | Mass ratio of total effective water to sum of all cementitious materials: W/B = Water / (OPC + GGBS + FlyAsh). | Forecast Col H formula: =G2/(D2+E2). Must strictly satisfy W/B <= 0.45 for durability. | AI Input Feature, Mix Optimization Boundary |
| `BR-004` | **Cube Strength Calculation** | Compressive Strength (MPa) = (Failure Load in kN * 1000) / Surface Area in mm2. For 150mm cubes, Area = 22500 mm2. | FT7 Form Row 32 formula: =B31/22.5. | QA Specimen Result Engine |
| `BR-005` | **Strength Gain Ratio (7d to 28d)** | Minimum expected 7-day strength must achieve >= 65% of characteristic strength f_ck. | QA Laboratory Validation Rule. | Early Warning Alert, Batch Hold Rule |
| `BR-006` | **Acceptance Limits (Pass/Hold)** | A batch passes QA if: (1) Mean 28d strength >= f_ck + 3 MPa, and (2) Individual cube strength >= f_ck - 3 MPa. | IS 456 Quality Control Standard. | Automated Batch Disposition (PASS/HOLD) |
| `BR-007` | **Material Dosing Tolerance** | Batching plant material dosing actual vs target tolerance bounds: Cement/Binders <= ±1.0%, Water <= ±1.0%, Aggregates <= ±2.0%, Admixture <= ±3.0%. | IS 4926 Ready Mixed Concrete Specification. | Digital Twin Variance Alert |
| `BR-008` | **Prediction Confidence Score** | Model prediction uncertainty metric derived from prediction interval standard error: Confidence = max(0, 100 - (2 * SE / Target * 100)). | AI Model Inference Engine. | Engineering Decision Support Dashboard |
| `BR-009` | **Similarity Score (Mix Matching)** | Cosine similarity score evaluating historical mix formulation closeness based on normalized OPC, GGBS, Water, and W/B vector distances. | AI Similarity Search Engine. | Mix Recipe Recommender |
| `BR-010` | **Optimization Constraints** | Linear programming optimization objective: Minimize Cost subject to: (1) Strength >= f_ck', (2) W/B <= Max_WB, (3) Slump in target range. | SLSQP / LP Mix Optimization Engine. | Composition Optimizer |
| `BR-011` | **Continuous Learning Trigger** | Automated model retraining pipeline triggers when >= 50 new verified 28-day strength lab results are logged. | MLOps Event Scheduler. | Continuous Retraining Pipeline |
| `BR-012` | **Retraining Trigger (Drift)** | Retraining triggers automatically if Concept Drift score (Kolmogorov-Smirnov test p-value < 0.05) is detected on W/B ratio. | Model Drift Monitor. | Model Governance & Registry |
