"""Settings Administrative API Router for DB Preview, SQL Export, and Engineering Calibre."""

from typing import Any, Dict
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from src.contracts.settings.database_preview_models import (
    DatabasePreviewResponseDTO,
    SqlExportResponseDTO,
)
from src.database.models.user import User
from src.security.dependencies import get_current_user, get_db, require_roles
from src.services.database_preview_service import DatabasePreviewService
from src.services.engineering_settings_service import (
    EngineeringSettingsService,
    UpdateEngineeringSettingsDTO,
)

router = APIRouter(
    prefix="/api/v1/settings",
    tags=["Settings - Platform Administration & Engineering Calibre"],
)


# --- Database Schema Introspection & Export ---

@router.get(
    "/database/preview",
    response_model=DatabasePreviewResponseDTO,
    summary="Retrieve live PostgreSQL database schema introspection metadata",
)
def get_database_preview(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("SUPER_ADMIN", "ADMIN", "QUALITY_HEAD")
    ),
) -> DatabasePreviewResponseDTO:
    """Fetch live table definitions, columns, primary keys, and foreign keys."""
    return DatabasePreviewService.get_database_preview(db=db)


@router.get(
    "/database/export/sql",
    response_model=SqlExportResponseDTO,
    summary="Retrieve generated SQL DDL statements for all public tables",
)
def get_sql_ddl_export(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("SUPER_ADMIN", "ADMIN", "QUALITY_HEAD")
    ),
) -> SqlExportResponseDTO:
    """Generate and return clean PostgreSQL DDL schema export."""
    return DatabasePreviewService.generate_sql_ddl_export(db=db)


@router.get(
    "/database/export/sql/download",
    summary="Download generated PostgreSQL DDL schema export as a .sql file",
)
def download_sql_ddl_export(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("SUPER_ADMIN", "ADMIN", "QUALITY_HEAD")
    ),
):
    """Download database DDL schema file directly with safe headers."""
    export_dto = DatabasePreviewService.generate_sql_ddl_export(db=db)
    sql_bytes = export_dto.sql_ddl.encode("utf-8")

    return Response(
        content=sql_bytes,
        media_type="application/sql",
        headers={
            "Content-Disposition": f'attachment; filename="{export_dto.filename}"',
            "Content-Type": "application/sql",
            "Content-Length": str(len(sql_bytes)),
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


# --- Engineering & Calculation Calibre Administration ---

@router.get(
    "/engineering-calibre",
    summary="Retrieve active engineering standards, statistical Z-factor, durability limits, and SCM bounds",
)
def get_engineering_calibre_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("SUPER_ADMIN", "ADMIN", "QUALITY_HEAD", "PLANT_OPERATOR")
    ),
) -> Dict[str, Any]:
    """Fetch active database-persisted engineering calculation configuration."""
    return EngineeringSettingsService.get_active_settings(db=db)


@router.put(
    "/engineering-calibre",
    summary="Update and persist engineering calculation calibre, design codes, and durability limits",
)
def update_engineering_calibre_settings(
    payload: UpdateEngineeringSettingsDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("SUPER_ADMIN", "ADMIN", "QUALITY_HEAD")
    ),
) -> Dict[str, Any]:
    """Persist modified engineering calculation parameters with audit trail."""
    username = getattr(current_user, "username", None) or getattr(current_user, "email", "admin")
    return EngineeringSettingsService.update_settings(db=db, payload=payload, username=username)


@router.post(
    "/engineering-calibre/reset",
    summary="Reset engineering calculation parameters to official IS 456 / IS 10262 factory defaults",
)
def reset_engineering_calibre_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("SUPER_ADMIN", "ADMIN", "QUALITY_HEAD")
    ),
) -> Dict[str, Any]:
    """Restore official Indian Standard defaults in the database."""
    username = getattr(current_user, "username", None) or getattr(current_user, "email", "admin")
    return EngineeringSettingsService.reset_to_defaults(db=db, username=username)
