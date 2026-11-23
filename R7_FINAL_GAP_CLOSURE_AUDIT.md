# R7 Final Gap Closure Audit

## 1. Audit Metadata
- **Platform**: ACC Ready-Mix Concrete (RMC) AI Platform
- **Workstream**: WS-03.6 R7 Data Contract Alignment & Integration Gap Closure
- **Phase**: Phase 0 — Read-Only Implementation Audit
- **Execution Mode**: READ-ONLY (No code, model, schema, test, or DB mutations executed)
- **Date**: 2026-08-11
- **Repository Path**: `wsl.localhost\Ubuntu-24.04\home\sanjana\acc-rmc-ai-platform\`

---

## 2. Scope
Audit existing WS-03.6 code, database schemas, ORM models, ingestion persistence services, parsers, and test suites across all backend components to evaluate the 4 implementation gaps (`GAP-01`, `GAP-02`, `GAP-03`, `GAP-04`) and baseline contract integrity prior to Phase 1-12 execution.

---

## 3. Read-Only Guarantee
Strict compliance verified:
- Zero production source code files modified.
- Zero test files modified.
- Zero database models or migrations modified.
- Zero schema or index changes executed.
- Zero database state mutated.
- All findings gathered via static code inspection and non-mutating test collection.

---

## 4. Existing WS-03.6 Baseline
- **Integrated Backend Test Suite**: 151 tests across `tests/backend/`.
- **Repository Unit/Integration Test Suite**: 491 tests across `tests/`.
- **WS-03.6 Authoritative Pre-R7 Baseline**: 304 tests referenced in workstream checkpoints.
- **Current R7 Dedicated Test Suite**: 6 tests in `tests/backend/test_ws03_6_r7_data_contract.py` (expanding to 16 test categories / 23 sub-tests in Phase 8).

---

## 5. GAP-01 — Canonical Batch Identity

### Current Behavior
- `src/parsers/excel_parser.py` line 100 generates `batch_number = f"BATCH-FT7-{sheet_name}"` when `challan_no` is unsupplied.
- `src/parsers/excel_parser.py` line 267 generates `batch_number = f"BATCH-STD-{s_clean}-{s_rand}"`.
- `src/parsers/excel_parser.py` line 364 generates `batch_number = f"BATCH-FCST-{s_name}-{session_prefix}-R{r}"`.

### Evidence
- `src/parsers/excel_parser.py`: L100, L267, L364.
- Source-specific prefixes (`BATCH-COL-`, `BATCH-FT7-`, `BATCH-STD-`, `BATCH-FCST-`) and sheet names/random tokens (`wb_prefix` equivalents) participate in business identity generation.

### Contract Violation
- Canonical human-readable identity MUST be `BATCH-{challan}` (e.g. `BATCH-1749`).
- Source-specific prefixes and `wb_prefix` are improperly mixed into canonical business identity.

### Required Fix
- Standardize `excel_parser.py` to generate `BATCH-{challan}` for all batching & quality worksheets.
- Retain `wb_prefix` strictly as technical source lineage / audit metadata in `logs_json` and job tracking. It must never determine `batch_number`, Batch uniqueness, entity resolution, or cross-source linkage.

### Files Affected
- [`src/parsers/excel_parser.py`](file:///wsl.localhost/Ubuntu-24.04/home/sanjana/acc-rmc-ai-platform/src/parsers/excel_parser.py)

---

## 6. GAP-02 — Production Event Resolution

### Current Behavior
- `src/services/ingestion_persistence_service.py` line 94 uses `.first()` on `Batch.batch_number` lookup without evaluating 3-part production event key (`plant_id + delivery_challan_number + production/casting date/time`).

### Evidence
- `src/services/ingestion_persistence_service.py`: L94: `existing_batch = self.db.query(Batch).filter(Batch.batch_number == payload.batch.batch_number, Batch.is_deleted == False).first()`.
- In `persist_canonical_payloads` lines 304–309 and 314–318: raises `ConcurrencyConflictException` when >1 candidate matches.

### Contract Violation
- Arbitrary `.first()` can match the wrong Batch entity when challan numbers recur across plants or production dates.
- Using `ConcurrencyConflictException` for business identity ambiguity violates contract separation (concurrency optimistic locking vs business identity ambiguity).

### Required Fix
- Remove `.first()` in Batch resolution across all entrypoints.
- Resolve using `plant_id + delivery_challan_number + normalized UTC date/time`.
- Production-event resolution must use canonical normalized UTC date/time when available without inventing timestamp tolerance windows.
- Raise domain business conflict exception (e.g. `EntityMappingException` / `BusinessConflictException`) when >1 candidate matches.

### Files Affected
- [`src/services/ingestion_persistence_service.py`](file:///wsl.localhost/Ubuntu-24.04/home/sanjana/acc-rmc-ai-platform/src/services/ingestion_persistence_service.py)

---

## 7. GAP-03 — Material Constituent Contract

### Current Behavior
- `src/services/ingestion_persistence_service.py` (`persist_canonical_payload` L126–127) adds `BatchMaterialConsumption` rows unconditionally without checking existing entries by `batch_id + material_id`.
- `persist_canonical_payloads` (L333–339) skips addition if `existing_mc` exists, but does not perform ENRICH or CONFLICT field comparison.

### Evidence
- `src/services/ingestion_persistence_service.py`: L126–127 & L333–339.

### Contract Violation
- Single-payload re-ingestion creates duplicate `BatchMaterialConsumption` rows.
- Re-ingestion skips validation without distinguishing `NO-OP` (identical values), `ENRICH` (valid new fields), and `CONFLICT` (mismatched metrics).

### Required Fix
- Enforce `batch_id + material_id` lookup across all persistence entrypoints.
- NO-OP on identical source/canonical values.
- Enrich valid new values (`planned_quantity`, `actual_quantity`, `moisture_percentage`, `absorption_percentage`, `moisture_correction_kg`, `source_material_code`).
- Raise explicit business CONFLICT on data contradictions without silent overwrites.

### Files Affected
- [`src/services/ingestion_persistence_service.py`](file:///wsl.localhost/Ubuntu-24.04/home/sanjana/acc-rmc-ai-platform/src/services/ingestion_persistence_service.py)

---

## 8. GAP-04 — FT7 Cube Contract

### Current Behavior
- `src/mappers/canonical_entity_mapper.py` lines 111–121 sets `status_val = "COMPLETED"` unless payload has zero consumptions. FT7-first batches without consumptions mapped via single-payload persistence default to `COMPLETED`.
- In `persist_canonical_payloads` line 325 sets `production_status = "PLANNED"` when consumptions are absent, but lacks seamless state machine transition when batching payload later arrives.

### Evidence
- `src/mappers/canonical_entity_mapper.py`: L111–121.
- `src/services/ingestion_persistence_service.py`: L302–303, L325.

### Contract Violation
- FT7-first batches are initially assigned `COMPLETED` status in single-payload entrypoints instead of `PLANNED`.

### Required Fix
- Ensure FT7-first ingestion creates Batch anchor with `production_status = "PLANNED"`.
- Upon subsequent batching payload arrival, transition `production_status = "COMPLETED"`.
- Preserve 6 individual cube specimens and separate 7D/28D sets attached to `existing_batch.id`.

### Files Affected
- [`src/mappers/canonical_entity_mapper.py`](file:///wsl.localhost/Ubuntu-24.04/home/sanjana/acc-rmc-ai-platform/src/mappers/canonical_entity_mapper.py)
- [`src/services/ingestion_persistence_service.py`](file:///wsl.localhost/Ubuntu-24.04/home/sanjana/acc-rmc-ai-platform/src/services/ingestion_persistence_service.py)

---

## 9. Business Conflict Semantics
- **Idempotent Re-ingestion**: Produces `NO-OP` without raising exceptions.
- **Business Identity Ambiguity & Data Contradictions**: Raises a domain business conflict exception (`EntityMappingException` / `BusinessConflictException`).
- **Optimistic Locking / Version Conflicts**: Continues raising `ConcurrencyConflictException` / `StaleDataError`.

---

## 10. Database Constraint Audit
- **Batch (`prd_batches`)**: `batch_number` column has `unique=True` (L35 in `src/database/models/production.py`). Human-readable `BATCH-{challan}` requires production-event identity (`plant_id + delivery_challan_number + production_start_time`) for resolution.
- **BatchMaterialConsumption (`prd_batch_material_consumptions`)**: FKs to `prd_batches.id` & `mst_materials.id`. Authoritative domain key: `(batch_id, material_id)`.
- **ConcreteSample (`lab_samples`)**: `sample_number` has `unique=True`, FK `batch_id` to `prd_batches.id`. Authoritative domain key: `(batch_id, sample_number)`.
- **CubeSet (`lab_cube_sets`)**: `cube_set_number` has `unique=True`, FK `sample_id` to `lab_samples.id`. Authoritative domain key: `(sample_id, age_days)`.
- **CubeTest (`lab_cube_tests`)**: FK `cube_set_id` to `lab_cube_sets.id`. Authoritative domain key: `(cube_set_id, mould_identifier)`.

---

## 11. Existing Test Coverage
- **Requirements 1–6**: Partially tested in `tests/backend/test_ws03_6_r7_data_contract.py` (6 existing tests).
- **Requirements 7–15**: Require expanded test implementations in `tests/backend/test_ws03_6_r7_data_contract.py`.
- **Requirements 16A–16H**: Covered across existing WS-03.6 tests:
  - `16A` (Optimistic locking): `test_ws03_6_phase5_concurrency.py::test_01`
  - `16B` (Version increment): `test_ws03_6_phase5_concurrency.py::test_02`
  - `16C` (Stale update rejection): `test_ws03_6_phase5_concurrency.py::test_03`
  - `16D` (Atomic rollback): `test_ws03_6_phase5_concurrency.py::test_04`
  - `16E` (Session confirmation): `test_ws03_6_phase5_concurrency.py::test_06`
  - `16F` (Duplicate source protection): `test_ws03_6_phase5_concurrency.py::test_05`
  - `16G` (Timeout retry): `test_ws03_6_phase5_concurrency.py::test_07`
  - `16H` (FAILED session retry): `test_ws03_6_phase5_concurrency.py::test_08`

---

## 12. Contract Inconsistencies Discovered
- **`wb_prefix`**: Must be preserved in technical lineage metadata (`logs_json` / ingestion job attributes) while removed from `batch_number` business identity.
- **Laboratory Identity**: ORM relationships establish `ConcreteSample -> Batch`, `CubeSet -> ConcreteSample`, `CubeTest -> CubeSet`. Identity keys must follow these exact foreign key boundaries.

---

## 13. Files Requiring Modification
- [`src/parsers/excel_parser.py`](file:///wsl.localhost/Ubuntu-24.04/home/sanjana/acc-rmc-ai-platform/src/parsers/excel_parser.py)
- [`src/services/ingestion_persistence_service.py`](file:///wsl.localhost/Ubuntu-24.04/home/sanjana/acc-rmc-ai-platform/src/services/ingestion_persistence_service.py)
- [`src/mappers/canonical_entity_mapper.py`](file:///wsl.localhost/Ubuntu-24.04/home/sanjana/acc-rmc-ai-platform/src/mappers/canonical_entity_mapper.py)
- [`tests/backend/test_ws03_6_r7_data_contract.py`](file:///wsl.localhost/Ubuntu-24.04/home/sanjana/acc-rmc-ai-platform/tests/backend/test_ws03_6_r7_data_contract.py)

---

## 14. Files That Must Remain Frozen
- Dashboard UI components (`frontend/src/...`)
- Active Alembic migration history (unless Phase 7 DB audit identifies missing invariant)
- WS-03.6 Phase 5 concurrency locking modules (`src/services/ingestion_uow.py`)

---

## 15. R7 Implementation Readiness
All 4 gaps audited with empirical file/line evidence. All safety checks passed. Read-only compliance verified.

---

## 16. Phase 1–12 Dependency Map
`Phase 0 (Audit)` -> `Phase 1 (Identity)` -> `Phase 2 (Event Resolution)` -> `Phase 3 (State Handling)` -> `Phase 4 (FT7-first)` -> `Phase 5 (Lab Idempotency)` -> `Phase 6 (Conflict Semantics)` -> `Phase 7 (DB Constraint Audit)` -> `Phase 8 (R7 Tests)` -> `Phase 9 (Full Regression)` -> `Phase 10 (Physical Reconciliation)` -> `Phase 11 (Browser Verification)` -> `Phase 12 (Documentation)`

---

## 17. Audit Conclusion
`PHASE 0 STATUS: READY FOR IMPLEMENTATION`
