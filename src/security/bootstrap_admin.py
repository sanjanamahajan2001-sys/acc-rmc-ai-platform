"""Secure Super Administrator Bootstrapping Service & CLI.

Initializes the canonical initial SUPER_ADMIN account securely without
hardcoding credentials into source code, migrations, or Git.
"""

import os
import sys
from typing import Any, Dict, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.engine import get_database_engine
from src.database.models.user import User, Role, UserRole, SecurityAuditLog
from src.security.crypto import hash_password, validate_password_policy


def bootstrap_super_admin(
    session: Session,
    username: str = "acc.admin",
    email: str = "admin@acc-rmc.in",
    full_name: str = "ACC Master Administrator",
    password: Optional[str] = None,
    overwrite_existing: bool = False,
) -> Dict[str, Any]:
    """Bootstrap the canonical Super Administrator account.

    Args:
        session: Active SQLAlchemy database session.
        username: Administrator username (normalized to lowercase).
        email: Administrator email (normalized to lowercase).
        full_name: Administrator display name.
        password: Plaintext password (if None, reads from ACC_RMC_ADMIN_BOOTSTRAP_PASSWORD env var).
        overwrite_existing: Whether to reset password if admin account already exists.

    Returns:
        Status summary dictionary.

    Raises:
        ValueError: If password is missing or violates password policy.
    """
    clean_username = username.strip().lower()
    clean_email = email.strip().lower()

    # Obtain password from parameter or environment
    raw_password = password or os.getenv("ACC_RMC_ADMIN_BOOTSTRAP_PASSWORD")
    if not raw_password:
        raise ValueError(
            "Bootstrap password is required. Set 'ACC_RMC_ADMIN_BOOTSTRAP_PASSWORD' "
            "environment variable or provide explicit password parameter."
        )

    # Validate against policy
    is_valid, errors = validate_password_policy(raw_password)
    if not is_valid:
        raise ValueError(f"Bootstrap password does not meet security policy: {', '.join(errors)}")

    # Ensure SUPER_ADMIN role exists
    super_admin_role = session.get(Role, "SUPER_ADMIN")
    if not super_admin_role:
        super_admin_role = Role(
            id="SUPER_ADMIN",
            name="Master Administrator",
            description="Full platform authority, database maintenance, user governance, API key management.",
            is_system_role=True,
        )
        session.add(super_admin_role)
        session.flush()

    # Check for existing user by username or email
    existing_user = session.scalars(
        select(User).where((User.username == clean_username) | (User.email == clean_email))
    ).first()

    hashed_pw = hash_password(raw_password)

    if existing_user:
        if not overwrite_existing:
            return {
                "status": "ALREADY_EXISTS",
                "message": f"Super admin user '{existing_user.username}' already exists. Skipping overwrite.",
                "user_id": existing_user.id,
            }

        # Update existing user safely
        existing_user.password_hash = hashed_pw
        existing_user.account_status = "ACTIVE"
        existing_user.password_status = "NORMAL"
        existing_user.must_change_password = False
        existing_user.session_version += 1
        admin_user = existing_user
        event_type = "SUPER_ADMIN_PASSWORD_RESET"
    else:
        # Create brand new super admin
        admin_user = User(
            username=clean_username,
            email=clean_email,
            full_name=full_name,
            password_hash=hashed_pw,
            account_status="ACTIVE",
            password_status="NORMAL",
            must_change_password=False,
            session_version=1,
        )
        session.add(admin_user)
        session.flush()
        event_type = "SUPER_ADMIN_BOOTSTRAPPED"

    # Ensure SUPER_ADMIN role assignment
    existing_assignment = session.scalars(
        select(UserRole).where(
            (UserRole.user_id == admin_user.id) & (UserRole.role_id == "SUPER_ADMIN")
        )
    ).first()

    if not existing_assignment:
        session.add(UserRole(user_id=admin_user.id, role_id="SUPER_ADMIN"))

    # Record security audit log
    audit_entry = SecurityAuditLog(
        actor_user_id=admin_user.id,
        target_user_id=admin_user.id,
        event_type=event_type,
        resource_name="USER_MANAGEMENT",
        details={
            "action": "BOOTSTRAP_ADMIN",
            "username": admin_user.username,
            "roles": ["SUPER_ADMIN"],
        },
    )
    session.add(audit_entry)
    session.commit()

    return {
        "status": "SUCCESS",
        "message": f"Super Administrator '{admin_user.username}' successfully provisioned.",
        "user_id": admin_user.id,
        "event_type": event_type,
    }


def main():
    """CLI Entrypoint for Super Admin bootstrap."""
    engine = get_database_engine()
    with Session(engine) as session:
        try:
            result = bootstrap_super_admin(session)
            print(f"[+] Bootstrap Result: {result['status']} — {result['message']}")
            sys.exit(0)
        except Exception as e:
            print(f"[-] Bootstrap Failed: {str(e)}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
