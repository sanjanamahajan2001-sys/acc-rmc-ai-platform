# ACC RMC AI Platform — Master Production Implementation Blueprint (v2.0)

## 1. Executive Summary & Architectural Evolution

Following a rigorous architectural review, the **ACC RMC AI Platform** implementation roadmap has been restructured into **22 granular, production-hardened workstreams**. 

This revised master blueprint shifts the platform from a monolithic service roadmap to a clean, domain-driven, event-bus-backed architecture. It introduces explicit state machines for batch and QA lifecycles, connector-based ingestion capabilities, dedicated AI dataset/inference segregation, and early frozen API availability to support continuous UI integration testing.

---

## 2. Master Workstream Phasing (22 Workstreams)

```
+---------------------------------------------------------------------------------------------------+
|                                MASTER WORKSTREAM ROADMAP (22 WORKSTREAMS)                          |
+---------------------------------------------------------------------------------------------------+
| WS-01: Platform Foundation & Core Project Structure                                               |
| WS-02: Multi-Environment Configuration, Secrets & Feature Flag Management                         |
| WS-03: Canonical Database Schema, Migrations & Indexing Strategy                                 |
| WS-04: Generic Data Repositories & Data Access Layer (DAL)                                        |
| WS-05: In-Memory Event Bus & Event-Driven Architecture                                            |
| WS-06: Task Scheduler & Background Orchestration Framework                                        |
| WS-07: Connector-Based Import Engine & Parser Core Framework                                      |
| WS-08: Production Excel Connector & Dual OpenPyXL Parsing Engine                                  |
| WS-09: Single-Batch Entry & Operational Workflow Layer                                            |
| WS-10: Master Data Management (MDM) & Multi-Plant Governance                                      |
| WS-11: Batch Domain & Production Lifecycle State Machine                                          |
| WS-12: QA & Laboratory Domain State Machine (FT7 & Cubes)                                         |
| WS-13: Digital Batch Twin & Real-time Material Variance Engine                                    |
| WS-14: Enterprise Reporting Engine (PDF, Excel, CSV, Audit Exports)                               |
| WS-15: Frozen Dashboard API Layer & Continuous Frontend Integration                                |
| WS-16: AI Feature Store & Time-Series Pipeline Infrastructure                                     |
| WS-17: Dataset Builder & Historical Signal Extraction Engine                                      |
| WS-18: Model Training, Validation & Registry Pipeline                                             |
| WS-19: Model Inference, Serving & Explainability Engine                                           |
| WS-20: Mixture Composition Optimization & Cost Reduction Engine                                   |
| WS-21: Continuous Learning, Outcome Reconciliation & Drift Monitoring                             |
| WS-22: DevOps, Hardening, Security & Production Certification                                     |
+---------------------------------------------------------------------------------------------------+
```

---

## 3. Detailed Workstream Specifications

### WS-01: Platform Foundation & Core Project Structure
- **Objective**: Establish the standardized enterprise directory structure (`src/`, `config/`, `logging/`, `exceptions/`, `middleware/`, `constants/`, `shared/`, `database/`, `tests/`, `docs/`, `scripts/`).
- **Deliverables**: Foundation directory structure, global exception handlers, `structlog` setup, `pytest` base harness.

---

### WS-02: Multi-Environment Configuration, Secrets & Feature Flag Management
- **Objective**: Implement environment-isolated settings (`Development`, `QA`, `Staging`, `Production`) with dynamic feature flags and secret management.
- **Deliverables**: `Pydantic-Settings` config engine, vault/env secret loaders, feature flag service.

---

### WS-03: Canonical Database Schema, Migrations & Indexing Strategy
- **Objective**: Freeze the 100% canonical database schema before writing business logic.
- **Deliverables**: Alembic migration scripts for master, transaction, QA, audit, and temporal tables.

---

### WS-04: Generic Data Repositories & Data Access Layer (DAL)
- **Objective**: Implement type-safe repository abstractions isolating database access from domain services.
- **Deliverables**: `BaseRepository`, `BatchRepository`, `FT7Repository`, `DeliveryRepository`.

---

### WS-05: In-Memory Event Bus & Event-Driven Architecture
- **Objective**: Implement an internal async event bus (`EventPublisher`, `EventListener`) decoupling domain side-effects.
- **Deliverables**: `EventBus` core, standard events (`BatchCreated`, `DispatchIssued`, `FT7Generated`, `LabTestRecorded`, `PredictionRequested`).

---

### WS-06: Task Scheduler & Background Orchestration Framework
- **Objective**: Build a centralized scheduler framework (`APScheduler`/`Celery`) for automated tasks.
- **Deliverables**: Scheduler service, background task wrappers for imports, retraining, backups, and health monitoring.

---

### WS-07: Connector-Based Import Engine & Parser Core Framework
- **Objective**: Design an extensible connector architecture supporting current Excel and future ERP/SCADA/REST/MQTT streams.
- **Deliverables**: `BaseConnector`, `IngestionPipeline`, `QuarantineService`.

---

### WS-08: Production Excel Connector & Dual OpenPyXL Parsing Engine
- **Objective**: Implement the certified Excel connector for historical backfilling and daily batch log ingestion.
- **Deliverables**: `ExcelConnector`, `AnchorPatternMatcher`, `CellDeunifier`.

---

### WS-09: Single-Batch Entry & Operational Workflow Layer
- **Objective**: Expose operational REST APIs for manual batch data entry and single dispatch creation.
- **Deliverables**: `POST /api/v1/batches/single`, validation handlers.

---

### WS-10: Master Data Management (MDM) & Multi-Plant Governance
- **Objective**: Provide CRUD and versioning services for plants, customers, sites, trucks, and mix recipes.
- **Deliverables**: MDM domain services, multi-tenant isolation rules.

---

### WS-11: Batch Domain & Production Lifecycle State Machine
- **Objective**: Encapsulate batch domain logic and enforce state transitions: `Created` $\rightarrow$ `Batched` $\rightarrow$ `Dispatched` $\rightarrow$ `Delivered` $\rightarrow$ `Sampled` $\rightarrow$ `7Day` $\rightarrow$ `28Day` $\rightarrow$ `Closed`.
- **Deliverables**: `BatchStateMachine`, `BatchDomainService`.

---

### WS-12: QA & Laboratory Domain State Machine (FT7 & Cubes)
- **Objective**: Encapsulate FT7 sampling certificate and cube test lifecycles: `Created` $\rightarrow$ `Pending` $\rightarrow$ `7DayComplete` $\rightarrow$ `28DayComplete` $\rightarrow$ `Verified` $\rightarrow$ `Archived`.
- **Deliverables**: `FT7StateMachine`, `QADomainService`, $MPa$ calculation engine.

---

### WS-13: Digital Batch Twin & Real-time Material Variance Engine
- **Objective**: Compute target vs actual material dosing variances and aggregate moisture adjustments.
- **Deliverables**: `DigitalBatchTwinService`, `VarianceCalculationEngine`.

---

### WS-14: Enterprise Reporting Engine (PDF, Excel, CSV, Audit Exports)
- **Objective**: Provide automated report generation for QA certificates, batch summaries, and compliance audits.
- **Deliverables**: `ReportGenerationService`, PDF/Excel exporter plugins.

---

### WS-15: Frozen Dashboard API Layer & Continuous Frontend Integration
- **Objective**: Expose optimized, backward-compatible API endpoints serving the frozen UI dashboard throughout development.
- **Deliverables**: Dashboard REST API controllers (`GET /api/v1/dashboard/*`).

---

### WS-16: AI Feature Store & Time-Series Pipeline Infrastructure
- **Objective**: Manage time-series feature calculation (W/B ratio, binder index, temperature factors).
- **Deliverables**: `FeatureStoreService`, time-series aggregators.

---

### WS-17: Dataset Builder & Historical Signal Extraction Engine
- **Objective**: Extract, clean, and pair historical mix features with 7-day and 28-day ground truth strength labels.
- **Deliverables**: `DatasetBuilderService`, feature vector export tasks.

---

### WS-18: Model Training, Validation & Registry Pipeline
- **Objective**: Train and validate multivariable regression models (`LINEST` linear and LightGBM) with MLflow experiment tracking.
- **Deliverables**: `ModelTrainingPipeline`, `MLflowRegistryService`.

---

### WS-19: Model Inference, Serving & Explainability Engine
- **Objective**: Provide real-time 7d/28d strength predictions and feature attribution (SHAP values).
- **Deliverables**: `InferenceService`, `ExplainabilityEngine`.

---

### WS-20: Mixture Composition Optimization & Cost Reduction Engine
- **Objective**: Provide constrained optimization algorithms (SLSQP) to minimize binder cost under target strength $f_{ck}'$ constraints.
- **Deliverables**: `MixOptimizationEngine`, cost minimization APIs.

---

### WS-21: Continuous Learning, Outcome Reconciliation & Drift Monitoring
- **Objective**: Reconcile predictions against actual 28-day lab results, monitor W/B drift via KS tests, and trigger automated retraining.
- **Deliverables**: `ReconciliationEngine`, `DriftMonitorService`, `RetrainingPipeline`.

---

### WS-22: DevOps, Hardening, Security & Production Certification
- **Objective**: Enforce OAuth2/RBAC security, Docker containerization, Nginx proxy setup, Prometheus monitoring, and execute final production certification.
- **Deliverables**: `docker-compose.prod.yml`, `nginx.conf`, Security Audit Report.

---

## 4. File Locations

- **Master Implementation Blueprint v2.0**: [`Master_Production_Implementation_Blueprint.md`](file://wsl.localhost/Ubuntu-24.04/home/sanjana/acc-rmc-ai-platform/Master_Production_Implementation_Blueprint.md)
- **Artifact Mirror**: [`Master_Production_Implementation_Blueprint.md`](file:///C:/Users/acer/.gemini/antigravity/brain/4fe36a86-34a3-44c5-8725-e56313d016b4/Master_Production_Implementation_Blueprint.md)
