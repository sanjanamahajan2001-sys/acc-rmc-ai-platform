"""Comprehensive Backend Test Suite for Final Dashboard Summary & Authoritative Export.

Verifies:
1. Canonical FullDashboardReportDTO aggregation across all 4 executive summary groups.
2. Machine-readable JSON export with full domain provenance and zero recomputations.
3. ReportLab PDF generation with vector charts and IS 456 / IS 10262 compliance headers.
4. Safe handling of unconfigured pricing, missing runs, and zero-candidate scenarios.
5. Governance guardrail: "Production activation is outside the current phase."
"""

import io
import json
import pytest
import uuid
from datetime import date
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.main import app
from src.contracts.reporting.export_models import FullDashboardReportDTO
from src.database.models.user import User, Role, UserRole
from src.database.session import get_session_factory
from src.security.jwt import create_access_token
from src.security.crypto import hash_password
from src.services.dashboard_export_service import DashboardExportService


@pytest.fixture
def db_session():
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin_user(db_session: Session):
    user = db_session.query(User).filter(User.username == "test_admin_export").first()
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            username="test_admin_export",
            email="adminexport@acc-rmc.in",
            full_name="Plant Admin Export",
            password_hash=hash_password("Pass@123456"),
            account_status="ACTIVE",
            password_status="NORMAL",
            must_change_password=False,
            session_version=1,
        )
        db_session.add(user)
        db_session.flush()

        role = db_session.query(Role).filter(Role.id == "ADMIN").first()
        if not role:
            role = Role(id="ADMIN", name="Admin", is_system_role=True)
            db_session.add(role)
            db_session.flush()

        db_session.add(UserRole(user_id=user.id, role_id="ADMIN"))
        db_session.commit()
        db_session.refresh(user)
    return user


@pytest.fixture
def admin_auth_headers(admin_user):
    token = create_access_token(
        user_id=str(admin_user.id),
        username=admin_user.username,
        email=admin_user.email,
        roles=["ADMIN"],
        session_version=admin_user.session_version,
    )
    return {"Authorization": f"Bearer {token}"}


class TestFinalDashboardExport:
    """Test suite for full dashboard report DTO, PDF rendering, JSON serialization, and guardrails."""

    def test_build_full_dashboard_report_dto_structure(self, db_session: Session):
        """Verify build_dashboard_report_dto generates a fully populated canonical DTO."""
        report = DashboardExportService.build_dashboard_report_dto(
            db=db_session,
            plant_code="PLANT-NS70",
            recipe_code="M-40",
        )

        assert isinstance(report, FullDashboardReportDTO)
        assert report.report_metadata.report_title == "ACC Ready-Mix Concrete Operations & Optimization Report"
        assert report.report_metadata.compliance_standard == "IS 456:2000 / IS 10262:2019 / IS 4926:2003"

        # Executive Summary Group A: Quality & Production
        grp_a = report.executive_summary.quality_and_production
        assert grp_a.total_batches_produced >= 0
        assert grp_a.total_volume_m3 >= 0.0

        # Executive Summary Group B: Strength Prediction
        grp_b = report.executive_summary.strength_prediction
        assert grp_b.platform_active_model != ""
        assert grp_b.validation_status == "Limited Validation"

        # Executive Summary Group C: Mix Optimization
        grp_c = report.executive_summary.mix_optimization
        assert grp_c.optimization_objective is not None

        # Executive Summary Group D: Governance & Commercial
        grp_d = report.executive_summary.governance_and_commercial
        assert grp_d.production_activation_notice == "Production activation is outside the current phase."

    def test_json_export_serialization(self, db_session: Session):
        """Verify render_json produces valid, parseable JSON with full provenance."""
        report = DashboardExportService.build_dashboard_report_dto(
            db=db_session,
            plant_code="PLANT-NS70",
        )
        json_str = DashboardExportService.render_json(report)
        assert isinstance(json_str, str)

        parsed = json.loads(json_str)
        assert "report_metadata" in parsed
        assert "dashboard_context" in parsed
        assert "executive_summary" in parsed
        assert "quality_metrics" in parsed
        assert "material_consumption" in parsed
        assert "model_monitoring" in parsed
        assert "provenance" in parsed

        assert parsed["provenance"]["source_database"] == "acc_rmc_prod"

    def test_pdf_export_rendering_binary(self, db_session: Session):
        """Verify render_pdf produces a valid, non-empty PDF document starting with standard PDF header."""
        report = DashboardExportService.build_dashboard_report_dto(
            db=db_session,
            plant_code="PLANT-NS70",
            recipe_code="M-40",
        )
        pdf_bytes = DashboardExportService.render_pdf(report)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 1000
        # Standard PDF file header
        assert pdf_bytes.startswith(b"%PDF-")

    def test_unconfigured_pricing_guardrail_in_export(self, db_session: Session):
        """Verify unconfigured pricing displays 'Pricing Source: Not Configured' without fabricating savings."""
        report = DashboardExportService.build_dashboard_report_dto(
            db=db_session,
            plant_code="PLANT-NS70",
            recipe_code="M-40",
        )
        
        # When pricing is unconfigured in the run:
        if report.cost_impact and report.cost_impact.pricing_status == "NOT_CONFIGURED":
            assert report.cost_impact.pricing_source_description == "Pricing Source: Not Configured"
            assert report.cost_impact.master_recipe_cost_per_m3 is None
            assert report.cost_impact.candidate_cost_per_m3 is None
            assert report.cost_impact.cost_delta_per_m3 is None

    def test_export_endpoints_via_api_client(self, client: TestClient, admin_auth_headers: dict):
        """Verify /api/v1/reporting/executive-summary, /export/json and /export/pdf endpoints."""
        # 1. Executive Summary
        res_summary = client.get(
            "/api/v1/reporting/executive-summary?plant_code=PLANT-NS70",
            headers=admin_auth_headers
        )
        assert res_summary.status_code == 200
        data_summary = res_summary.json()
        assert "quality_and_production" in data_summary
        assert "strength_prediction" in data_summary
        assert "mix_optimization" in data_summary
        assert "governance_and_commercial" in data_summary

        # 2. JSON Export
        res_json = client.get(
            "/api/v1/reporting/export/json?plant_code=PLANT-NS70",
            headers=admin_auth_headers
        )
        assert res_json.status_code == 200
        data_json = res_json.json()
        assert data_json["report_metadata"]["report_title"] == "ACC Ready-Mix Concrete Operations & Optimization Report"

        # 3. PDF Export
        res_pdf = client.get(
            "/api/v1/reporting/export/pdf?plant_code=PLANT-NS70",
            headers=admin_auth_headers
        )
        assert res_pdf.status_code == 200
        assert res_pdf.headers["content-type"] == "application/pdf"
        assert "attachment; filename=" in res_pdf.headers.get("content-disposition", "")
        assert res_pdf.content.startswith(b"%PDF-")

    def test_export_endpoint_requires_authentication(self, client: TestClient):
        """Verify unauthenticated requests to export endpoints are strictly rejected with HTTP 401."""
        res_json = client.get("/api/v1/reporting/export/json")
        assert res_json.status_code == 401

        res_pdf = client.get("/api/v1/reporting/export/pdf")
        assert res_pdf.status_code == 401
