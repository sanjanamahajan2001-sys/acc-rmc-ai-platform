"""Enterprise Engineering & Calculation Calibre Settings Service.

Provides database-persisted access to concrete design standards (IS 456, ACI 318, BS EN 206),
statistical confidence multiplier (Z-score), IS 456 Table 5 durability constraints,
air volume entrapment, and SCM substitution bounds.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.database.models.engineering_settings import EngineeringSettingsModel
from src.database.models.user import SecurityAuditLog
from src.logging import get_logger

logger = get_logger("src.services.engineering_settings_service", component="engineering_settings")

# Default IS 456 / IS 10262 Standard Configuration
DEFAULT_IS_456_SETTINGS: Dict[str, Any] = {
    "standard_code": "IS_456_IS_10262",
    "standard_name": "IS 456:2000 & IS 10262:2019 (Indian Standards)",
    "confidence_multiplier_z": 1.65,
    "target_strength_formula": "f_ck_prime = fck + Z * sigma",
    "air_volume_fraction": 0.010,  # 1.0% entrapped air per IS 10262 Table 3 for 20mm MSA
    "exposure_constraints_json": {
        "MILD": {"min_cement_kg_m3": 300.0, "max_wb_ratio": 0.55, "min_grade": "M20"},
        "MODERATE": {"min_cement_kg_m3": 300.0, "max_wb_ratio": 0.50, "min_grade": "M25"},
        "SEVERE": {"min_cement_kg_m3": 320.0, "max_wb_ratio": 0.45, "min_grade": "M30"},
        "VERY_SEVERE": {"min_cement_kg_m3": 340.0, "max_wb_ratio": 0.45, "min_grade": "M35"},
        "EXTREME": {"min_cement_kg_m3": 360.0, "max_wb_ratio": 0.40, "min_grade": "M40"},
    },
    "scm_substitution_bounds_json": {
        "FLY_ASH": {"max_replacement_percent": 35.0, "min_replacement_percent": 0.0},
        "GGBS": {"max_replacement_percent": 50.0, "min_replacement_percent": 0.0},
        "MICRO_SILICA": {"max_replacement_percent": 10.0, "min_replacement_percent": 0.0},
    },
    "specific_gravities_json": {
        "CEMENT": 3.15,
        "FLY_ASH": 2.20,
        "GGBS": 2.90,
        "MICRO_SILICA": 2.20,
        "WATER": 1.00,
        "COARSE_AGGREGATE": 2.70,
        "FINE_AGGREGATE": 2.65,
        "ADMIXTURE": 1.15,
    },
}

AVAILABLE_DESIGN_STANDARDS = [
    {
        "code": "IS_456_IS_10262",
        "name": "IS 456:2000 & IS 10262:2019",
        "jurisdiction": "India (BIS)",
        "formula": "f_ck_prime = fck + Z * sigma",
        "default_z": 1.65,
        "description": "Standard code of practice for plain and reinforced concrete with concrete mix proportioning guidelines.",
    },
    {
        "code": "ACI_318_211",
        "name": "ACI 318-19 & ACI 211.1",
        "jurisdiction": "USA / International (ACI)",
        "formula": "f_cr = f_c_prime + Z * s",
        "default_z": 1.34,
        "description": "Building code requirements for structural concrete and standard practice for selecting proportions for normal weight concrete.",
    },
    {
        "code": "BS_EN_206",
        "name": "BS EN 206 & Eurocode 2",
        "jurisdiction": "Europe / UK (CEN)",
        "formula": "f_cm = f_ck + Z * sigma",
        "default_z": 1.64,
        "description": "European Standard for concrete specification, performance, production, and conformity.",
    },
]


class UpdateEngineeringSettingsDTO(BaseModel):
    standard_code: str = Field(..., description="Selected design standard code")
    standard_name: str = Field(..., description="Human readable design standard name")
    confidence_multiplier_z: float = Field(..., ge=1.00, le=3.00, description="Z-score statistical multiplier (e.g. 1.28 for 90%, 1.65 for 95%, 2.33 for 99%)")
    target_strength_formula: str = Field(default="f_ck_prime = fck + Z * sigma")
    air_volume_fraction: float = Field(..., ge=0.001, le=0.080, description="Entrapped air volume fraction (e.g. 0.010 = 1.0%)")
    exposure_constraints_json: Dict[str, Any] = Field(..., description="Exposure condition durability limits")
    scm_substitution_bounds_json: Dict[str, Any] = Field(..., description="SCM replacement boundaries")
    specific_gravities_json: Optional[Dict[str, Any]] = None


class EngineeringSettingsService:
    """Service layer managing database retrieval and updates for engineering calculation parameters."""

    _CACHED_SETTINGS: Optional[Dict[str, Any]] = None

    @classmethod
    def get_active_settings(cls, db: Optional[Session] = None) -> Dict[str, Any]:
        """Fetch active engineering settings from DB, with auto-initialization and fallback."""
        try:
            if db is None:
                if cls._CACHED_SETTINGS:
                    return cls._CACHED_SETTINGS
                from src.database.session import get_session_factory
                factory = get_session_factory()
                with factory() as temp_db:
                    return cls.get_active_settings(temp_db)

            settings_rec = (
                db.query(EngineeringSettingsModel)
                .filter(EngineeringSettingsModel.is_active == True)
                .order_by(EngineeringSettingsModel.created_at.desc())
                .first()
            )

            if not settings_rec:
                # Initialize default record in DB
                new_rec = EngineeringSettingsModel(
                    id=str(uuid.uuid4()),
                    standard_code=DEFAULT_IS_456_SETTINGS["standard_code"],
                    standard_name=DEFAULT_IS_456_SETTINGS["standard_name"],
                    confidence_multiplier_z=DEFAULT_IS_456_SETTINGS["confidence_multiplier_z"],
                    target_strength_formula=DEFAULT_IS_456_SETTINGS["target_strength_formula"],
                    air_volume_fraction=DEFAULT_IS_456_SETTINGS["air_volume_fraction"],
                    exposure_constraints_json=DEFAULT_IS_456_SETTINGS["exposure_constraints_json"],
                    scm_substitution_bounds_json=DEFAULT_IS_456_SETTINGS["scm_substitution_bounds_json"],
                    specific_gravities_json=DEFAULT_IS_456_SETTINGS["specific_gravities_json"],
                    is_active=True,
                    updated_by_username="SYSTEM_INIT",
                )
                db.add(new_rec)
                db.commit()
                settings_rec = new_rec

            result = {
                "id": str(settings_rec.id),
                "standard_code": settings_rec.standard_code,
                "standard_name": settings_rec.standard_name,
                "confidence_multiplier_z": float(settings_rec.confidence_multiplier_z),
                "target_strength_formula": settings_rec.target_strength_formula,
                "air_volume_fraction": float(settings_rec.air_volume_fraction),
                "air_volume_percent": round(float(settings_rec.air_volume_fraction) * 100.0, 2),
                "exposure_constraints_json": settings_rec.exposure_constraints_json,
                "scm_substitution_bounds_json": settings_rec.scm_substitution_bounds_json,
                "specific_gravities_json": settings_rec.specific_gravities_json or DEFAULT_IS_456_SETTINGS["specific_gravities_json"],
                "is_active": settings_rec.is_active,
                "updated_by_username": settings_rec.updated_by_username,
                "updated_at": settings_rec.updated_at.isoformat() if settings_rec.updated_at else None,
                "available_standards": AVAILABLE_DESIGN_STANDARDS,
            }
            cls._CACHED_SETTINGS = result
            return result
        except Exception as e:
            logger.warning(f"Failed to query sys_engineering_settings from DB: {e}. Falling back to default IS 456 config.")
            if cls._CACHED_SETTINGS:
                return cls._CACHED_SETTINGS
            fallback = dict(DEFAULT_IS_456_SETTINGS)
            fallback["id"] = "DEFAULT-IS-456"
            fallback["air_volume_percent"] = 1.0
            fallback["updated_by_username"] = "DEFAULT_FALLBACK"
            fallback["updated_at"] = datetime.now(timezone.utc).isoformat()
            fallback["available_standards"] = AVAILABLE_DESIGN_STANDARDS
            return fallback

    @classmethod
    def update_settings(cls, db: Session, payload: UpdateEngineeringSettingsDTO, username: str) -> Dict[str, Any]:
        """Update and persist engineering calculation settings in database."""
        # Deactivate previous active records
        db.query(EngineeringSettingsModel).filter(EngineeringSettingsModel.is_active == True).update({"is_active": False})

        new_rec = EngineeringSettingsModel(
            id=str(uuid.uuid4()),
            standard_code=payload.standard_code,
            standard_name=payload.standard_name,
            confidence_multiplier_z=payload.confidence_multiplier_z,
            target_strength_formula=payload.target_strength_formula,
            air_volume_fraction=payload.air_volume_fraction,
            exposure_constraints_json=payload.exposure_constraints_json,
            scm_substitution_bounds_json=payload.scm_substitution_bounds_json,
            specific_gravities_json=payload.specific_gravities_json or DEFAULT_IS_456_SETTINGS["specific_gravities_json"],
            is_active=True,
            updated_by_username=username,
        )
        db.add(new_rec)

        # Log governance audit event
        try:
            db.add(
                SecurityAuditLog(
                    event_type="SETTINGS_UPDATED",
                    resource_name="SETTINGS",
                    details={
                        "action": "UPDATE_ENGINEERING_CALIBRE",
                        "standard_code": payload.standard_code,
                        "confidence_multiplier_z": payload.confidence_multiplier_z,
                        "air_volume_fraction": payload.air_volume_fraction,
                        "exposure_constraints": payload.exposure_constraints_json,
                        "scm_bounds": payload.scm_substitution_bounds_json,
                        "specific_gravities": payload.specific_gravities_json,
                        "updated_by": username,
                    },
                )
            )
        except Exception as err:
            logger.warning(f"Could not record SecurityAuditLog for settings update: {err}")

        db.commit()

        cls._CACHED_SETTINGS = None
        return cls.get_active_settings(db)

    @classmethod
    def reset_to_defaults(cls, db: Session, username: str) -> Dict[str, Any]:
        """Reset calculation settings to official IS 456 / IS 10262 factory defaults."""
        db.query(EngineeringSettingsModel).filter(EngineeringSettingsModel.is_active == True).update({"is_active": False})

        new_rec = EngineeringSettingsModel(
            id=str(uuid.uuid4()),
            standard_code=DEFAULT_IS_456_SETTINGS["standard_code"],
            standard_name=DEFAULT_IS_456_SETTINGS["standard_name"],
            confidence_multiplier_z=DEFAULT_IS_456_SETTINGS["confidence_multiplier_z"],
            target_strength_formula=DEFAULT_IS_456_SETTINGS["target_strength_formula"],
            air_volume_fraction=DEFAULT_IS_456_SETTINGS["air_volume_fraction"],
            exposure_constraints_json=DEFAULT_IS_456_SETTINGS["exposure_constraints_json"],
            scm_substitution_bounds_json=DEFAULT_IS_456_SETTINGS["scm_substitution_bounds_json"],
            specific_gravities_json=DEFAULT_IS_456_SETTINGS["specific_gravities_json"],
            is_active=True,
            updated_by_username=f"{username} (RESET_TO_DEFAULTS)",
        )
        db.add(new_rec)

        # Log governance audit event
        try:
            db.add(
                SecurityAuditLog(
                    event_type="SETTINGS_RESET_DEFAULTS",
                    resource_name="SETTINGS",
                    details={
                        "action": "RESET_ENGINEERING_CALIBRE_DEFAULTS",
                        "standard_code": DEFAULT_IS_456_SETTINGS["standard_code"],
                        "confidence_multiplier_z": DEFAULT_IS_456_SETTINGS["confidence_multiplier_z"],
                        "reset_by": username,
                    },
                )
            )
        except Exception as err:
            logger.warning(f"Could not record SecurityAuditLog for settings reset: {err}")

        db.commit()

        cls._CACHED_SETTINGS = None
        return cls.get_active_settings(db)
