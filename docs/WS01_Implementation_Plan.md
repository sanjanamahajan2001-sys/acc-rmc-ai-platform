# Implementation Plan — Workstream WS-01: Platform Foundation & Core Project Structure (v2.0)

## Executive Summary

Workstream **WS-01** (Platform Foundation & Core Project Structure) defines the architectural groundwork, package organization, coding standards, logging hierarchy, exception handling, configuration management, and testing harnesses for the ACC RMC AI Platform.

This document serves as the implementation plan. No source code or directory scaffolding has been created yet.

---

## Mini Workstream Breakdown

To ensure modularity and production readiness, **WS-01** is divided into **7 mini workstreams**:

```
+-----------------------------------------------------------------------------------------------+
|                                    WS-01 MINI WORKSTREAMS                                     |
+-----------------------------------------------------------------------------------------------+
| WS-01.1: Enterprise Project Directory Layout & Package Boundaries                            |
| WS-01.2: Coding Standards, Naming Conventions & Import Rules                                  |
| WS-01.3: Base Exception Hierarchy & Global Error Handling Architecture                       |
| WS-01.4: Structured Logging Infrastructure & Audit Context Propagation                        |
| WS-01.5: Multi-Environment Configuration & Settings Engine Architecture                       |
| WS-01.6: Foundation Core Types, Constants & Enum Registries                                   |
| WS-01.7: Testing Foundation, Quality Gates & Certification Framework                          |
+-----------------------------------------------------------------------------------------------+
```

---

## Detailed Mini Workstream Specifications

### Mini Workstream WS-01.1: Enterprise Project Directory Layout & Package Boundaries
- **Objective**: Define explicit package boundaries and module exports to prevent circular imports across modules.
- **Business Purpose**: Ensures strict architectural isolation as team size and plant integrations grow.
- **Technical Scope**: Package init exports, top-level namespace declarations, `.gitignore` rules.
- **Dependencies**:
  - **Depends On**: None (First Step)
  - **Blocked By**: None
  - **Enables**: WS-01.2, WS-01.3, WS-01.4, WS-01.5, WS-01.6, WS-01.7, WS-02 to WS-22
- **Non-Goals**:
  - No database migration creation
  - No domain service implementation
  - No REST route handlers
- **Future Extension Notes**:
  - Modular plugin architecture for third-party ERP connectors
  - Sub-package decoupling for microservice extraction if needed
- **Deliverables**: Directory tree specification, namespace packaging rules.
- **Acceptance Criteria**: 100% clean package imports without circular reference errors.

---

### Mini Workstream WS-01.2: Coding Standards, Naming Conventions & Import Rules
- **Objective**: Freeze static analysis rules, strict type hints, and import formatting.
- **Business Purpose**: Ensures maintainability, readability, and zero implicit type coercion bugs.
- **Technical Scope**: `pyproject.toml` configurations for `ruff` (linter), `mypy --strict` (type checker), `black` (formatter), `isort` (import sorter).
- **Dependencies**:
  - **Depends On**: WS-01.1
  - **Blocked By**: WS-01.1
  - **Enables**: WS-01.3 to WS-01.7, WS-02 to WS-22
- **Non-Goals**:
  - No runtime code execution checking
  - No automated code modification without PR review
- **Future Extension Notes**:
  - Pre-commit hook automation with CI/CD linter gates
  - Custom SonarQube quality profile rules
- **Deliverables**: Linter configuration file (`pyproject.toml`), coding standards guide.
- **Acceptance Criteria**: `ruff check src/` and `mypy --strict src/` pass with 0 errors.

---

### Mini Workstream WS-01.3: Base Exception Hierarchy & Global Error Handling Architecture
- **Objective**: Define the root exception `ACCRMCBaseException` and specialized domain exception classes.
- **Business Purpose**: Prevents unhandled raw tracebacks from exposing internal details to end users while standardizing REST API error payloads.
- **Dependencies**:
  - **Depends On**: WS-01.1, WS-01.2
  - **Blocked By**: WS-01.1, WS-01.2
  - **Enables**: WS-01.4, WS-03, WS-04, WS-05, WS-09, WS-15
- **Non-Goals**:
  - No DB error persistence
  - No automated alert notifications (PagerDuty/Slack)
- **Future Extension Notes**:
  - Automatic error code mapping to internationalization (i18n) error messages
  - Sentry exception tracking SDK integration
- **Deliverables**: Exception class tree, HTTP status code mapper, `ErrorResponse` schema.
- **Acceptance Criteria**: Every custom exception maps to a structured JSON error response containing `error_code`, `message`, and `correlation_id`.

---

### Mini Workstream WS-01.4: Structured Logging Infrastructure & Audit Context Propagation
- **Objective**: Implement JSON structured logging using `structlog` with thread-local correlation IDs (`request_id`, `plant_code`, `user_id`).
- **Business Purpose**: Guarantees log traceability across multi-plant dispatch and lab operations.
- **Dependencies**:
  - **Depends On**: WS-01.1, WS-01.2
  - **Blocked By**: WS-01.1, WS-01.2
  - **Enables**: WS-03, WS-04, WS-05, WS-08, WS-15, WS-22
- **Non-Goals**:
  - No database logging
  - No business events publishing
  - No audit log DB persistence
  - No external log shipping (Logstash/Fluentd)
  - No monitoring dashboard visualizers
- **Future Extension Notes**:
  - Direct log streaming to Elasticsearch / Grafana Loki
  - OpenTelemetry trace propagation and Jaeger distributed tracing integration
- **Deliverables**: Logging configuration module, log context middleware, log audit documentation.
- **Acceptance Criteria**: 100% of log entries contain valid ISO 8601 timestamps, log level, correlation ID, and module context.

---

### Mini Workstream WS-01.5: Multi-Environment Configuration & Settings Engine Architecture
- **Objective**: Build `pydantic-settings` configuration management for `Development`, `QA`, `Staging`, and `Production` environments.
- **Business Purpose**: Ensures strict environment isolation for database connection strings, secret keys, and feature flags.
- **Dependencies**:
  - **Depends On**: WS-01.1, WS-01.2, WS-01.4
  - **Blocked By**: WS-01.1, WS-01.2
  - **Enables**: WS-02, WS-03, WS-16, WS-22
- **Non-Goals**:
  - No dynamic database credential rotation
  - No external vault network calls during startup
- **Future Extension Notes**:
  - HashiCorp Vault / AWS Secrets Manager / Kubernetes Secrets SDK integration
  - Remote feature flag provider (LaunchDarkly/Unleash) fallback integration
- **Deliverables**: `Settings` model, environment loader, feature flag manager.
- **Acceptance Criteria**: Zero hardcoded credentials; successful startup validation across all 4 environments.

---

### Mini Workstream WS-01.6: Foundation Core Types, Constants & Enum Registries
- **Objective**: Freeze platform-wide enums and immutable physical constants matching the certified Canonical Data Dictionary.
- **Business Purpose**: Eliminates string typos and guarantees consistent domain terminology.
- **Dependencies**:
  - **Depends On**: WS-01.1, WS-01.2
  - **Blocked By**: WS-01.1
  - **Enables**: WS-03, WS-04, WS-11, WS-12, WS-16
- **Non-Goals**:
  - No dynamic runtime enum creation
  - No database lookup table synchronization
- **Future Extension Notes**:
  - Automated OpenAPI schema enum export generator
  - Proto3 gRPC enum definition mapping
- **Deliverables**: Enum registry modules, physical constants specification.
- **Acceptance Criteria**: All canonical dictionary enums defined with zero duplicate values.

---

### Mini Workstream WS-01.7: Testing Foundation, Quality Gates & Certification Framework
- **Objective**: Establish the reusable testing, quality gate, and production certification framework inherited by all future workstreams (WS-02 through WS-22).
- **Business Purpose**: Guarantees consistent quality gates, Definition of Done (DoD), and certification reports across all platform workstreams.
- **Dependencies**:
  - **Depends On**: WS-01.1 to WS-01.6
  - **Blocked By**: WS-01.1 to WS-01.6
  - **Enables**: Mandatory quality gate framework inherited by WS-02 through WS-22
- **Non-Goals**:
  - No end-to-end UI browser automation
  - No external load test execution
- **Future Extension Notes**:
  - Automated CI/CD GitHub Actions quality gate pipeline integration
  - Mutation testing with `mutmut`
- **Deliverables**: Reusable pytest harness, `conftest.py`, Certification Report Template (`Certification_Report_Template.md`), DoD Checklist Template.
- **Acceptance Criteria**: 100% reusable test harness operational with certification templates ready for inherited workstream deployment.
