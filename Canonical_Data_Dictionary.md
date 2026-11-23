# Canonical Data Dictionary & Field Business Contract

> **Immutable Contract**: This dictionary establishes the single source of truth for canonical field naming across the Database Schema, REST APIs, AI Feature Store, Reports, and Dashboard Payload Contracts.

| Canonical Field | Type | Unit | Description | Source(s) | Used By |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `batch_id` | `UUID` | `-` | Unique batch mixing cycle identifier | Batching Report (PLC Log) | Database PK, Batch Twin, API, Audit |
| `delivery_note_no` | `String` | `-` | Challan / Dispatch order serial number | Batching Report Col D / Columns Col A | Delivery Entity, API, Dashboard |
| `plant_code` | `String` | `-` | Batching plant facility code | FT7 Form Row 8 / Header | Multi-Plant MDM, Filter API |
| `mix_grade` | `String` | `-` | Characteristic strength grade (e.g. M-30) | Batching Report Col C / FT7 Row 12 | Recipe MDM, AI Feature, Dashboard |
| `truck_number` | `String` | `-` | Transit mixer vehicle registration | Batching Report Col G / FT7 Row 13 | Fleet Management, Delivery API |
| `customer_name` | `String` | `-` | Purchasing commercial client name | Batching Report Col E / Columns Col H | Customer MDM, Dashboard Widget |
| `project_site` | `String` | `-` | Destination construction site location | Batching Report Col F / Columns Col I | Site MDM, Delivery API |
| `load_size_m3` | `Decimal` | `m3` | Volume of concrete batched in trip | Batching Report Col I / FT7 Row 14 | Volume Tracking, Dashboard KPI |
| `date_of_casting` | `Date` | `YYYY-MM-DD` | Date concrete was batched and cast | Batching Report Col A / FT7 Row 9 | Time-series Index, AI Feature |
| `time_batched` | `Time` | `HH:MM:SS` | Precise timestamp of batch mixing | Batching Report Col B / FT7 Row 8 | Batch Twin Timeline, Audit Log |
| `cement_target_kg` | `Decimal` | `kg` | Target specified mass of OPC cement | Batching Report Col K | Batch Twin, Variance Alert |
| `cement_actual_kg` | `Decimal` | `kg` | Measured actual mass of OPC dosed | Batching Report Col L / Forecast Col D | AI Input Feature (OPC), Batch Twin |
| `ggbs_target_kg` | `Decimal` | `kg` | Target specified mass of GGBS slag | Batching Report Col M | Batch Twin, Recipe Compliance |
| `ggbs_actual_kg` | `Decimal` | `kg` | Measured actual mass of GGBS dosed | Batching Report Col N / Forecast Col E | AI Input Feature (GGBS), Batch Twin |
| `flyash_target_kg` | `Decimal` | `kg` | Target specified mass of Fly Ash | Batching Report Col O | Batch Twin, Variance Engine |
| `flyash_actual_kg` | `Decimal` | `kg` | Measured actual mass of Fly Ash dosed | Batching Report Col P | AI Input Feature (FlyAsh), Batch Twin |
| `water_target_kg` | `Decimal` | `kg` | Target specified mixing water mass | Batching Report Col Q | Batch Twin, Water Calculator |
| `water_actual_kg` | `Decimal` | `kg` | Measured actual total water added | Batching Report Col R / Forecast Col G | AI Input Feature (Water), W/B Ratio |
| `admixture_target_kg` | `Decimal` | `kg` | Target chemical plasticizer dosage | Batching Report Col S | Batch Twin, Chemical Metering |
| `admixture_actual_kg` | `Decimal` | `kg` | Measured actual plasticizer dosed | Batching Report Col T / Forecast Col F | AI Input Feature (Admixture) |
| `agg_20mm_actual_kg` | `Decimal` | `kg` | Measured actual 20mm aggregate mass | Batching Report Col U | Batch Twin, Aggregate Ratio |
| `agg_10mm_actual_kg` | `Decimal` | `kg` | Measured actual 10mm aggregate mass | Batching Report Col V | Batch Twin, Aggregate Ratio |
| `crushed_sand_actual_kg` | `Decimal` | `kg` | Measured actual crushed sand mass | Batching Report Col W | Batch Twin, Sand Dosage |
| `agg_moisture_pct` | `Decimal` | `%` | Aggregate moisture percentage reading | Batching Report Col X | Batch Twin, Water Adjustment |
| `moisture_water_adj_kg` | `Decimal` | `kg` | Calculated water mass adjustment | Batching Report Col Z | Batch Twin, Flowmeter Control |
| `plant_slump_mm` | `Decimal` | `mm` | Measured concrete slump at batch plant | FT7 Form Row 16 | QA Compliance, Dashboard Slump Gauge |
| `site_slump_mm` | `Decimal` | `mm` | Measured concrete slump at jobsite | FT7 Form Row 15 | QA Compliance, Delivery Log |
| `concrete_temp_c` | `Decimal` | `°C` | Measured fresh concrete temperature | FT7 Form Row 17 | AI Feature (Temp), QA Log |
| `ambient_temp_c` | `Decimal` | `°C` | Measured ambient air temperature | FT7 Form Row 18 | AI Feature (Ambient), QA Log |
| `cube_ref_no` | `String` | `-` | Individual cube specimen identifier | FT7 Form Row 22 | Cube Specimen PK, QA Register |
| `cube_size_mm` | `String` | `mm` | Cube specimen dimensions (100mm/150mm) | FT7 Form Row 18 | Area Calculator, QA Register |
| `test_age_days` | `Integer` | `days` | Age of cube at testing (7d or 28d) | FT7 Form Row 27 | QA Maturity Filter, AI Target Label |
| `saturated_mass_kg` | `Decimal` | `kg` | Mass of saturated cube in air | FT7 Form Row 28 | Density Calculation, QA Audit |
| `failure_load_kn` | `Decimal` | `kN` | Maximum failure load on testing machine | FT7 Form Row 31 | Strength Calculation Input |
| `compressive_strength_mpa` | `Decimal` | `MPa` | Calculated specimen compressive strength | FT7 Form Row 32 | QA Register, AI Ground Truth Label |
| `strength_7d` | `Decimal` | `MPa` | Mean 7-day compressive strength | FT7 Form Row 34 | QA Signal, Early Predictor |
| `strength_28d` | `Decimal` | `MPa` | Mean 28-day compressive strength | FT7 Form Row 34 / Forecast Col I | AI Primary Target Label (y), KPI |
| `binder_ratio` | `Decimal` | `Ratio` | Water-to-Binder mass ratio (W/B) | Forecast Col H | AI Feature (W/B), Quality Rule |
