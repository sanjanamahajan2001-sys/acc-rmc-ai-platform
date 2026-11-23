from src.api.settings_router import router as settings_router
from src.api.ml_training_router import router as ml_training_router
from src.api.optimization_router import router as optimization_router
"""FastAPI Production Server Entrypoint for ACC Ready-Mix Concrete Platform."""

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm.exc import StaleDataError

from src.master_data.service import router as master_data_router
from src.api.ingestion_router import router as ingestion_router
from src.api.auth_router import router as auth_router
from src.api.admin_users_router import router as admin_users_router
from src.api.manual_entry_router import router as manual_entry_router
from src.api.reporting_router import router as reporting_router
from src.api.events_router import router as events_router
from src.api.audit_router import router as audit_router
from src.services.ingestion_persistence_service import ConcurrencyConflictException

app = FastAPI(
    title="ACC Ready-Mix Concrete AI Platform REST API",
    description="Production REST API for Master Data Management, Excel Ingestion, Identity & Admin Governance",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ConcurrencyConflictException)
def concurrency_conflict_exception_handler(request: Request, exc: ConcurrencyConflictException):
    return JSONResponse(
        status_code=409,
        content={
            "detail": {
                "error": "CONCURRENCY_CONFLICT",
                "message": exc.message,
                "resource_id": exc.resource_id,
                "expected_version": exc.expected_version,
                "current_version": exc.current_version,
            }
        },
    )


@app.exception_handler(StaleDataError)
def stale_data_exception_handler(request: Request, exc: StaleDataError):
    return JSONResponse(
        status_code=409,
        content={
            "detail": {
                "error": "CONCURRENCY_CONFLICT",
                "message": "Resource modification conflict detected. Stale version update rejected.",
                "details": str(exc),
            }
        },
    )


@app.on_event("startup")
def initialize_system_defaults():
    """Ensure canonical roles and default administrative user exist on startup."""
    try:
        from src.database.session import get_session_factory
        from src.database.models.user import User, Role, UserRole
        from src.security.crypto import hash_password, verify_password

        session = get_session_factory()()

        # 1. Canonical Roles
        default_roles = [
            ("SUPER_ADMIN", "Master Administrator"),
            ("ADMIN", "Plant System Administrator"),
            ("QUALITY_HEAD", "Quality Assurance Head"),
            ("LAB_TECHNICIAN", "Senior QC Lab Technician"),
            ("PLANT_OPERATOR", "Batching Plant Operator"),
            ("ANALYST_VIEWER", "Analytics & Operations Viewer"),
        ]
        for r_id, r_name in default_roles:
            if not session.query(Role).filter(Role.id == r_id).first():
                session.add(Role(id=r_id, name=r_name, description=f"{r_name} role", is_system_role=True))
        session.flush()

        # 2. Canonical admin user
        admin_user = session.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                email="admin@acc-rmc.in",
                full_name="System Administrator",
                password_hash=hash_password("Admin@123456"),
                account_status="ACTIVE",
                password_status="NORMAL",
                must_change_password=False,
                session_version=1,
            )
            session.add(admin_user)
            session.flush()
        else:
            # Ensure admin password is reset if needed and active
            if not verify_password("Admin@123456", admin_user.password_hash) or admin_user.account_status != "ACTIVE":
                admin_user.password_hash = hash_password("Admin@123456")
                admin_user.account_status = "ACTIVE"
                admin_user.password_status = "NORMAL"
                admin_user.must_change_password = False
                admin_user.failed_login_attempts = 0
                admin_user.lockout_until = None

        # Ensure SUPER_ADMIN and ADMIN roles assigned
        for r_id in ["SUPER_ADMIN", "ADMIN"]:
            if not session.query(UserRole).filter(UserRole.user_id == admin_user.id, UserRole.role_id == r_id).first():
                session.add(UserRole(user_id=admin_user.id, role_id=r_id))

        session.commit()
        session.close()
    except Exception as e:
        print(f"[!] System startup initialization notice: {e}")


# Register canonical routers
app.include_router(auth_router)
app.include_router(admin_users_router)
app.include_router(master_data_router)
app.include_router(ingestion_router)
app.include_router(manual_entry_router)
app.include_router(reporting_router)
app.include_router(events_router)
app.include_router(audit_router)
app.include_router(ml_training_router)
app.include_router(optimization_router)
app.include_router(settings_router)


@app.get("/health")
def health_check():
    return {"status": "HEALTHY", "platform": "ACC Ready-Mix Concrete AI Platform"}


if __name__ == "__main__":
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8005, reload=False)
