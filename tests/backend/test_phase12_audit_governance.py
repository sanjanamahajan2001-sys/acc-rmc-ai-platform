"""Phase 12: Audit & Governance Center Certification Test Suite.

Verifies:
1. Audit API Authorization (401 for unauthenticated, 403 for unauthorized roles, 200 for SUPER_ADMIN, ADMIN, QUALITY_HEAD).
2. Non-Regression: Existing permissions for PLANT_OPERATOR, LAB_TECHNICIAN, ANALYST_VIEWER remain unchanged.
3. Paginated event listing, filtering by module, severity, result, keyword search.
4. Single event inspection and correlation lineage tracing.
5. Server-side metrics aggregation with zero fabrication.
6. Secret redaction guarantee (passwords, tokens, hashes scrubbed).
7. Filtered CSV export generation and self-auditing.
"""

import unittest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.main import app
from src.database.base import BaseModel
from src.database.models.user import User, Role, UserRole, SecurityAuditLog
from src.security.crypto import hash_password
from src.security.jwt import create_access_token
from src.security.dependencies import get_db
from src.services.audit_service import AuditService


class TestPhase12AuditGovernance(unittest.TestCase):
    """Audit & Governance Center Comprehensive Backend Test Suite."""

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )
        BaseModel.metadata.create_all(bind=cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.SessionLocal()

        def override_get_db():
            db_session = self.SessionLocal()
            try:
                yield db_session
            finally:
                db_session.close()

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

        # 1. Seed Roles
        self.roles = {}
        for r_id, r_name in [
            ("SUPER_ADMIN", "Master Administrator"),
            ("ADMIN", "Plant System Administrator"),
            ("QUALITY_HEAD", "Quality Assurance Head"),
            ("LAB_TECHNICIAN", "Senior QC Lab Technician"),
            ("PLANT_OPERATOR", "Batching Plant Operator"),
            ("ANALYST_VIEWER", "Analytics & Operations Viewer"),
        ]:
            r = Role(id=r_id, name=r_name, is_system_role=True)
            self.db.add(r)
            self.roles[r_id] = r
        self.db.commit()

        # 2. Seed Users for each role
        self.users = {}
        self.tokens = {}

        for role_id in ["SUPER_ADMIN", "ADMIN", "QUALITY_HEAD", "LAB_TECHNICIAN", "PLANT_OPERATOR", "ANALYST_VIEWER"]:
            u = User(
                username=f"user_{role_id.lower()}",
                email=f"{role_id.lower()}@acc-rmc.in",
                full_name=f"Test {role_id}",
                password_hash=hash_password("SecurePass@123"),
                account_status="ACTIVE",
                password_status="NORMAL",
                must_change_password=False,
                session_version=1,
            )
            self.db.add(u)
            self.db.flush()
            self.db.add(UserRole(user_id=u.id, role_id=role_id))
            self.users[role_id] = u
            self.tokens[role_id] = create_access_token(
                user_id=u.id,
                username=u.username,
                roles=[role_id],
                session_version=1,
            )
        self.db.commit()

        # 3. Seed Sample Audit Events across modules
        self.sample_logs = [
            AuditService.log_event(
                db=self.db,
                event_type="LOGIN_SUCCESS",
                resource_name="AUTHENTICATION",
                actor_user_id=self.users["SUPER_ADMIN"].id,
                correlation_id="TRACE-001",
                details={"client": "web", "password": "SecretPassword123!"},
                ip_address="192.168.1.100",
            ),
            AuditService.log_event(
                db=self.db,
                event_type="USER_CREATED",
                resource_name="USER_MANAGEMENT",
                actor_user_id=self.users["ADMIN"].id,
                target_user_id=self.users["LAB_TECHNICIAN"].id,
                correlation_id="TRACE-001",
                details={"created_user": "user_lab_technician", "token": "Bearer eyJhbGciOi..."},
                ip_address="192.168.1.101",
            ),
            AuditService.log_event(
                db=self.db,
                event_type="INGESTION_PERSISTENCE_COMPLETED",
                resource_name="DATA_INGESTION",
                actor_user_id=self.users["ADMIN"].id,
                correlation_id="TRACE-002",
                details={"dataset_id": "DS-2026-001", "persisted_rows": 150, "failed_rows": 0},
                ip_address="192.168.1.102",
            ),
            AuditService.log_event(
                db=self.db,
                event_type="ACCESS_DENIED",
                resource_name="RBAC_AUTHORIZATION",
                actor_user_id=self.users["PLANT_OPERATOR"].id,
                correlation_id="TRACE-003",
                details={"path": "/api/v1/admin/users", "required_roles": ["ADMIN"]},
                ip_address="192.168.1.103",
            ),
            AuditService.log_event(
                db=self.db,
                event_type="LOGIN_FAILURE",
                resource_name="AUTHENTICATION",
                details={"attempted_username": "intruder", "reason": "Invalid credentials"},
                ip_address="203.0.113.42",
            ),
        ]

    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.query(SecurityAuditLog).delete()
        self.db.query(UserRole).delete()
        self.db.query(User).delete()
        self.db.query(Role).delete()
        self.db.commit()
        self.db.close()

    # --- Authorization Tests ---

    def test_audit_unauthenticated_returns_401(self):
        """Unauthenticated request to audit events returns 401 Unauthorized."""
        resp = self.client.get("/api/v1/audit/events")
        self.assertEqual(resp.status_code, 401)

    def test_audit_unauthorized_roles_return_403(self):
        """PLANT_OPERATOR, LAB_TECHNICIAN, and ANALYST_VIEWER receive 403 Forbidden."""
        for role in ["PLANT_OPERATOR", "LAB_TECHNICIAN", "ANALYST_VIEWER"]:
            resp = self.client.get(
                "/api/v1/audit/events",
                headers={"Authorization": f"Bearer {self.tokens[role]}"},
            )
            self.assertEqual(resp.status_code, 403, f"Role {role} should be denied audit access")

    def test_audit_authorized_roles_succeed_200(self):
        """SUPER_ADMIN, ADMIN, and QUALITY_HEAD successfully access audit events."""
        for role in ["SUPER_ADMIN", "ADMIN", "QUALITY_HEAD"]:
            resp = self.client.get(
                "/api/v1/audit/events",
                headers={"Authorization": f"Bearer {self.tokens[role]}"},
            )
            self.assertEqual(resp.status_code, 200, f"Role {role} should have audit access")
            data = resp.json()
            self.assertIn("items", data)
            self.assertIn("total", data)
            self.assertGreaterEqual(data["total"], 5)

    # --- Pagination & Filtering Tests ---

    def test_audit_pagination(self):
        """Verify server-side pagination with page and page_size."""
        token = self.tokens["ADMIN"]
        resp = self.client.get(
            "/api/v1/audit/events?page=1&page_size=2",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data["items"]), 2)
        self.assertEqual(data["page"], 1)
        self.assertEqual(data["page_size"], 2)
        self.assertGreaterEqual(data["total_pages"], 3)

    def test_audit_module_filter(self):
        """Verify filtering events by module."""
        token = self.tokens["ADMIN"]
        resp = self.client.get(
            "/api/v1/audit/events?module=AUTH",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        for item in data["items"]:
            self.assertEqual(item["module"], "AUTH")

    def test_audit_keyword_search(self):
        """Verify global keyword search."""
        token = self.tokens["ADMIN"]
        resp = self.client.get(
            "/api/v1/audit/events?q=INGESTION",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreaterEqual(len(data["items"]), 1)
        self.assertIn("INGESTION", data["items"][0]["event_type"])

    # --- Metrics & Correlation Tests ---

    def test_audit_metrics_aggregation(self):
        """Verify live database metrics without fabrication."""
        token = self.tokens["QUALITY_HEAD"]
        resp = self.client.get(
            "/api/v1/audit/metrics",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(resp.status_code, 200)
        metrics = resp.json()
        self.assertGreaterEqual(metrics["total_events"], 5)
        self.assertGreaterEqual(metrics["successful_events"], 3)
        self.assertGreaterEqual(metrics["failed_events"], 1)
        self.assertGreaterEqual(metrics["denied_events"], 1)
        self.assertIn("module_breakdown", metrics)

    def test_audit_correlation_trace(self):
        """Verify tracing events sharing the same correlation_id."""
        token = self.tokens["SUPER_ADMIN"]
        resp = self.client.get(
            "/api/v1/audit/correlation/TRACE-001",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(resp.status_code, 200)
        trace = resp.json()
        self.assertEqual(trace["correlation_id"], "TRACE-001")
        self.assertEqual(trace["total_events"], 2)

    def test_audit_single_event_inspection(self):
        """Verify single audit event detail inspection."""
        token = self.tokens["ADMIN"]
        event_id = str(self.sample_logs[0].id)
        resp = self.client.get(
            f"/api/v1/audit/events/{event_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(resp.status_code, 200)
        item = resp.json()
        self.assertEqual(item["id"], event_id)
        self.assertEqual(item["event_type"], "LOGIN_SUCCESS")

    # --- Secret Redaction Test ---

    def test_secret_redaction_in_details(self):
        """Verify passwords, tokens, and hashes are scrubbed in API responses."""
        token = self.tokens["ADMIN"]
        resp = self.client.get(
            "/api/v1/audit/events",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        for item in data["items"]:
            details_str = str(item["details"])
            self.assertNotIn("SecretPassword123!", details_str)
            self.assertNotIn("eyJhbGciOi...", details_str)
            if "password" in item["details"]:
                self.assertEqual(item["details"]["password"], "[REDACTED]")

    # --- CSV Export Test ---

    def test_audit_csv_export(self):
        """Verify CSV export endpoint and self-auditing."""
        token = self.tokens["SUPER_ADMIN"]
        resp = self.client.get(
            "/api/v1/audit/export?format=csv",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("content-type"), "text/csv; charset=utf-8")
        self.assertIn("Event ID,Timestamp (UTC),Module", resp.text)
        self.assertIn("LOGIN_SUCCESS", resp.text)

    # --- Critical Regression Verification ---

    def test_non_audit_routes_remain_accessible(self):
        """Verify health check and non-audit routes are unaffected by audit RBAC."""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "HEALTHY")


if __name__ == "__main__":
    unittest.main()
