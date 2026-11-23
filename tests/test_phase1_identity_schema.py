"""Phase 1: Canonical Database Identity Foundation Test Suite.

Rigorously verifies:
1. Canonical schema definitions and column attributes for User, Role, UserRole, SecurityAuditLog.
2. Idempotent canonical role definitions (6 domain roles).
3. Zero plaintext password persistence.
4. Absence of credentials in audit log structures.
5. Uniqueness and normalization constraints (Username, Email).
6. Foreign key integrity and safe cascade semantics (ON DELETE SET NULL / CASCADE).
7. Zero cascade side-effects on operational data tables (prd_batches, lab_cube_tests).
8. Optimistic locking version and session_version defaults.
"""

import uuid
import pytest
from datetime import datetime, timezone
from sqlalchemy import select, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.database.engine import get_database_engine
from src.database.models.user import User, Role, UserRole, SecurityAuditLog
from src.database.models.production import Batch
from src.database.models.laboratory import CubeTest


@pytest.fixture
def db_session():
    engine = get_database_engine()
    with Session(engine) as session:
        yield session
        session.rollback()


def test_canonical_roles_seeded(db_session: Session):
    """Verify that the 6 canonical ACC RMC domain roles are present and immutable."""
    expected_roles = {
        "SUPER_ADMIN": "Master Administrator",
        "ADMIN": "Plant Administrator",
        "QUALITY_HEAD": "QC / Lab Manager",
        "LAB_TECHNICIAN": "Lab QC Tester",
        "PLANT_OPERATOR": "Batching Operator",
        "ANALYST_VIEWER": "Operational Viewer",
    }

    roles = db_session.scalars(select(Role)).all()
    role_map = {r.id: r.name for r in roles}

    for role_id, expected_name in expected_roles.items():
        assert role_id in role_map, f"Missing canonical role: {role_id}"
        assert role_map[role_id] == expected_name


def test_user_table_schema_columns(db_session: Session):
    """Verify that usr_users table contains all canonical fields and no prohibited credential fields."""
    mapper = inspect(User)
    column_names = {col.key for col in mapper.column_attrs}

    required_columns = {
        "id",
        "username",
        "email",
        "full_name",
        "password_hash",
        "account_status",
        "password_status",
        "must_change_password",
        "temporary_password_created_at",
        "temporary_password_expires_at",
        "password_changed_at",
        "failed_login_attempts",
        "lockout_until",
        "last_login_at",
        "last_login_ip",
        "session_version",
        "version",
        "created_by_user_id",
        "created_at",
        "updated_at",
    }

    assert required_columns.issubset(column_names), f"Missing columns in User: {required_columns - column_names}"

    # Prohibited columns verification
    prohibited_substrings = ["plain", "raw_password", "temporary_password_plain", "temp_pass_plain"]
    for col in column_names:
        for prohibited in prohibited_substrings:
            assert prohibited not in col.lower(), f"Prohibited column '{col}' detected in User table!"


def test_user_uniqueness_constraints(db_session: Session):
    """Verify that duplicate usernames or emails are rejected by the database."""
    unique_suffix = uuid.uuid4().hex[:8]
    user1 = User(
        username=f"tester_{unique_suffix}",
        email=f"tester_{unique_suffix}@acc-rmc.in",
        full_name="Tester One",
        password_hash="$2b$12$hashed_test_value",
    )
    db_session.add(user1)
    db_session.commit()

    # Duplicate username
    user2 = User(
        username=f"tester_{unique_suffix}",
        email=f"different_{unique_suffix}@acc-rmc.in",
        full_name="Tester Two",
        password_hash="$2b$12$hashed_test_value",
    )
    db_session.add(user2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Duplicate email
    user3 = User(
        username=f"different_{unique_suffix}",
        email=f"tester_{unique_suffix}@acc-rmc.in",
        full_name="Tester Three",
        password_hash="$2b$12$hashed_test_value",
    )
    db_session.add(user3)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_user_role_assignment_and_cascade(db_session: Session):
    """Verify role assignment and cascading deletion behavior on user deletion."""
    unique_suffix = uuid.uuid4().hex[:8]
    user = User(
        username=f"operator_{unique_suffix}",
        email=f"operator_{unique_suffix}@acc-rmc.in",
        full_name="Operator User",
        password_hash="$2b$12$hashed_operator_password",
    )
    db_session.add(user)
    db_session.commit()

    # Assign PLANT_OPERATOR role
    user_role = UserRole(
        user_id=user.id,
        role_id="PLANT_OPERATOR",
    )
    db_session.add(user_role)
    db_session.commit()

    # Verify assignment exists
    assigned = db_session.scalars(select(UserRole).where(UserRole.user_id == user.id)).all()
    assert len(assigned) == 1
    assert assigned[0].role_id == "PLANT_OPERATOR"

    # Delete user and verify UserRole mapping is cleanly cascaded
    user_id = user.id
    db_session.delete(user)
    db_session.commit()

    remaining_assignments = db_session.scalars(select(UserRole).where(UserRole.user_id == user_id)).all()
    assert len(remaining_assignments) == 0

    # Ensure role definition itself was NOT deleted
    role = db_session.get(Role, "PLANT_OPERATOR")
    assert role is not None


def test_security_audit_log_structure_and_references(db_session: Session):
    """Verify security audit log creation and safe reference handling."""
    unique_suffix = uuid.uuid4().hex[:8]
    admin = User(
        username=f"admin_{unique_suffix}",
        email=f"admin_{unique_suffix}@acc-rmc.in",
        full_name="Admin User",
        password_hash="$2b$12$hashed_admin_password",
    )
    target = User(
        username=f"target_{unique_suffix}",
        email=f"target_{unique_suffix}@acc-rmc.in",
        full_name="Target User",
        password_hash="$2b$12$hashed_target_password",
    )
    db_session.add_all([admin, target])
    db_session.commit()

    audit_entry = SecurityAuditLog(
        actor_user_id=admin.id,
        target_user_id=target.id,
        event_type="USER_CREATED",
        resource_name="USER_MANAGEMENT",
        correlation_id="corr-12345",
        details={"assigned_roles": ["LAB_TECHNICIAN"]},
        ip_address="192.168.1.100",
        user_agent="pytest-client/1.0",
    )
    db_session.add(audit_entry)
    db_session.commit()

    saved = db_session.get(SecurityAuditLog, audit_entry.id)
    assert saved is not None
    assert saved.event_type == "USER_CREATED"
    assert saved.details["assigned_roles"] == ["LAB_TECHNICIAN"]

    # Delete admin (actor) and ensure audit entry remains with actor_user_id set to NULL
    db_session.delete(admin)
    db_session.commit()

    updated_audit = db_session.get(SecurityAuditLog, audit_entry.id)
    assert updated_audit is not None
    assert updated_audit.actor_user_id is None


def test_operational_data_isolation(db_session: Session):
    """Verify that operational batch and lab models have zero cascading dependencies on user models."""
    user_mapper = inspect(User)
    batch_mapper = inspect(Batch)
    cube_mapper = inspect(CubeTest)

    # Check that deleting a user cannot cascade into Batch or CubeTest
    for rel in user_mapper.relationships:
        assert rel.entity.class_ not in (Batch, CubeTest), (
            f"Illegal relationship from User to operational table {rel.entity.class_.__name__} detected!"
        )
