"""Enterprise ML Model Registry, Activation & Rollback Engine (Phase 13D).

Certified Rules:
- Zero Hardcoded Production Data Invariant.
- Strict Lifecycle State Machine: CANDIDATE -> ACTIVE -> RETIRED (or ARCHIVED).
- Zero Automatic Activation: Newly trained models are recorded strictly as CANDIDATE.
- Pre-Activation Verification: Artifact existence, SHA-256 checksum matching, feature schema matching, and deserialization reload test.
- Single-Active Invariant: Exactly ONE model can be ACTIVE per model name/purpose (atomically enforced in database transaction).
- Safe Rollback: Prior active model is retired (never deleted) and can be atomically reactivated with checksum verification.
- Audit Governance: All activations and rollbacks record actor ID, correlation ID, old/new model versions, timestamps, and zero secret leaks.
"""

import os
import hashlib
import logging
import joblib
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, update

from src.database.models.ai import ModelRegistry
from src.database.models.user import SecurityAuditLog

logger = logging.getLogger("acc_rmc.ml.registry")


class ModelRegistryError(Exception):
    """Base exception for model registry lifecycle violations."""
    pass


class ModelValidationError(ModelRegistryError):
    """Raised when candidate model artifact or metadata fails pre-activation checks."""
    pass


class ModelActivationError(ModelRegistryError):
    """Raised when model activation or rollback transaction fails."""
    pass


class ModelRegistryService:
    """Authoritative management engine for model registry lifecycle, activation, and rollback."""

    @staticmethod
    def get_active_model(db: Session, model_name: str = "acc_concrete_28d_strength") -> Optional[ModelRegistry]:
        """Fetch the currently active model entity for a given model contract."""
        return db.scalar(
            select(ModelRegistry).where(
                and_(
                    ModelRegistry.model_name == model_name,
                    ModelRegistry.deployment_status == "ACTIVE",
                    ModelRegistry.is_deleted == False,
                )
            )
        )

    @staticmethod
    def list_models(db: Session, model_name: str = "acc_concrete_28d_strength") -> List[ModelRegistry]:
        """List all registered models for a given model name ordered by creation timestamp."""
        return list(
            db.scalars(
                select(ModelRegistry)
                .where(
                    and_(
                        ModelRegistry.model_name == model_name,
                        ModelRegistry.is_deleted == False,
                    )
                )
                .order_by(ModelRegistry.created_at.desc())
            ).all()
        )

    @staticmethod
    def validate_candidate_artifact(model: ModelRegistry, expected_schema_version: str = "1.0.0") -> Tuple[bool, str]:
        """Verify candidate artifact integrity: file existence, SHA-256 checksum, schema compatibility, and reloadability."""
        if not model.artifact_location:
            raise ModelValidationError("Model record has no artifact_location specified.")

        if not os.path.exists(model.artifact_location):
            raise ModelValidationError(f"Model artifact file '{model.artifact_location}' does not exist on disk.")

        # 1. Compute and verify SHA-256 Checksum
        with open(model.artifact_location, "rb") as f:
            calculated_checksum = hashlib.sha256(f.read()).hexdigest()

        if model.checksum and calculated_checksum != model.checksum:
            raise ModelValidationError(
                f"Artifact checksum mismatch! Expected '{model.checksum}', got '{calculated_checksum}'."
            )

        # 2. Schema compatibility check
        if model.feature_schema_version != expected_schema_version:
            raise ModelValidationError(
                f"Feature schema version '{model.feature_schema_version}' is incompatible with engine version '{expected_schema_version}'."
            )

        # 3. Reload deserialization verification
        try:
            bundle = joblib.load(model.artifact_location)
            if not isinstance(bundle, dict) or "model" not in bundle or "pipeline" not in bundle:
                raise ModelValidationError("Artifact bundle missing required 'model' or 'pipeline' payload.")
            if not getattr(bundle["pipeline"], "fitted", False):
                raise ModelValidationError("Artifact FeaturePipeline was not properly fitted.")
        except Exception as ex:
            raise ModelValidationError(f"Failed to deserialize candidate model artifact: {ex}")

        return True, calculated_checksum

    @staticmethod
    def activate_model(
        db: Session,
        model_id: str,
        actor_user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Tuple[ModelRegistry, Optional[ModelRegistry]]:
        """Atomically promote a CANDIDATE or RETIRED model to ACTIVE, retiring the previous active model."""
        target_model = db.get(ModelRegistry, model_id)
        if not target_model:
            raise ModelActivationError(f"Model '{model_id}' not found in registry.")

        if target_model.deployment_status == "ACTIVE":
            logger.info(f"Model '{target_model.model_version}' is already ACTIVE. Returning current instance.")
            return target_model, None

        # 1. Rigorous Artifact Validation before touching active state
        ModelRegistryService.validate_candidate_artifact(target_model)

        # 2. Identify and retire current ACTIVE model atomically
        now = datetime.now(timezone.utc)
        current_active = ModelRegistryService.get_active_model(db, target_model.model_name)
        old_version = current_active.model_version if current_active else "NONE"

        if current_active and current_active.id != target_model.id:
            current_active.deployment_status = "RETIRED"
            current_active.updated_at = now
            logger.info(f"Retiring previously active model '{current_active.model_version}' (ID: {current_active.id}).")

        # 3. Promote target model to ACTIVE
        target_model.deployment_status = "ACTIVE"
        target_model.deployment_timestamp = now
        target_model.updated_at = now

        # 4. Audit Log Persistence
        audit_entry = SecurityAuditLog(
            actor_user_id=actor_user_id,
            target_user_id=None,
            event_type="MODEL_ACTIVATED",
            resource_name="ML_MODEL_REGISTRY",
            correlation_id=correlation_id,
            details={
                "model_name": target_model.model_name,
                "new_active_model_id": str(target_model.id),
                "new_active_version": target_model.model_version,
                "previous_active_version": old_version,
                "algorithm": target_model.algorithm,
                "checksum": target_model.checksum,
                "activation_reason": reason or "Explicit administrator model promotion",
            },
            ip_address="internal-api",
            user_agent="ModelRegistryService/1.0",
            created_at=now,
        )
        db.add(audit_entry)

        try:
            db.commit()
            db.refresh(target_model)
            if current_active:
                db.refresh(current_active)
        except Exception as ex:
            db.rollback()
            logger.error(f"Transaction failure during model activation: {ex}")
            raise ModelActivationError(f"Database transaction error during activation: {ex}")

        
        # Invalidate in-memory inference model cache
        try:
            from src.ml.inference.inference_service import MLInferenceService
            MLInferenceService.invalidate_cache()
        except Exception:
            pass
        logger.info(f"Successfully activated model '{target_model.model_version}'.")
        return target_model, current_active

    @staticmethod
    def rollback_model(
        db: Session,
        target_model_id: Optional[str] = None,
        model_name: str = "acc_concrete_28d_strength",
        actor_user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Tuple[ModelRegistry, ModelRegistry]:
        """Rollback active model to a previous verified candidate/retired model artifact."""
        current_active = ModelRegistryService.get_active_model(db, model_name)
        if not current_active:
            raise ModelActivationError(f"No currently ACTIVE model exists for '{model_name}' to rollback from.")

        # Determine rollback target
        if target_model_id:
            target_model = db.get(ModelRegistry, target_model_id)
            if not target_model or target_model.model_name != model_name:
                raise ModelActivationError(f"Target rollback model '{target_model_id}' not found for '{model_name}'.")
        else:
            # Pick most recent RETIRED model
            target_model = db.scalar(
                select(ModelRegistry)
                .where(
                    and_(
                        ModelRegistry.model_name == model_name,
                        ModelRegistry.deployment_status == "RETIRED",
                        ModelRegistry.id != current_active.id,
                        ModelRegistry.is_deleted == False,
                    )
                )
                .order_by(ModelRegistry.updated_at.desc())
            )
            if not target_model:
                raise ModelActivationError(f"No prior RETIRED model found for rollback on '{model_name}'.")

        # 1. Pre-validation of rollback target artifact
        ModelRegistryService.validate_candidate_artifact(target_model)

        now = datetime.now(timezone.utc)
        current_active.deployment_status = "RETIRED"
        current_active.updated_at = now

        target_model.deployment_status = "ACTIVE"
        target_model.deployment_timestamp = now
        target_model.updated_at = now

        # 2. Audit Trail for Rollback
        audit_entry = SecurityAuditLog(
            actor_user_id=actor_user_id,
            target_user_id=None,
            event_type="MODEL_ROLLBACK",
            resource_name="ML_MODEL_REGISTRY",
            correlation_id=correlation_id,
            details={
                "model_name": model_name,
                "reverted_from_version": current_active.model_version,
                "restored_active_version": target_model.model_version,
                "restored_model_id": str(target_model.id),
                "rollback_reason": reason or "Emergency operational model rollback",
            },
            ip_address="internal-api",
            user_agent="ModelRegistryService/1.0",
            created_at=now,
        )
        db.add(audit_entry)

        try:
            db.commit()
            db.refresh(target_model)
            db.refresh(current_active)
        except Exception as ex:
            db.rollback()
            raise ModelActivationError(f"Rollback transaction failed: {ex}")

        logger.info(f"Successfully rolled back from '{current_active.model_version}' to '{target_model.model_version}'.")
        return target_model, current_active
