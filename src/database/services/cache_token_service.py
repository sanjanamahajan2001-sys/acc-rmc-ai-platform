"""Cache Token Versioning & Atomic Event Journaling Service.

Provides database-authoritative cache token incrementing and event logging within
the same ACID transaction as operational data changes.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from src.database.models.cache import CacheToken, EventJournal


class CacheTokenService:
    DEFAULT_TOKENS = ["production_batch", "ingestion_session", "active_model", "lab_quality"]

    @classmethod
    def initialize_tokens_if_needed(cls, db: Session) -> None:
        """Ensure default domain tokens exist in sys_cache_tokens."""
        for token_name in cls.DEFAULT_TOKENS:
            existing = db.get(CacheToken, token_name)
            if not existing:
                db.add(CacheToken(token_name=token_name, token_version=1))
        db.commit()

    @classmethod
    def get_token_version(cls, token_name: str, db: Session) -> int:
        """Read authoritative token version from database."""
        token = db.get(CacheToken, token_name)
        if not token:
            token = CacheToken(token_name=token_name, token_version=1)
            db.add(token)
            db.commit()
            return 1
        return token.token_version

    @classmethod
    def bump_token_and_journal(
        cls,
        db: Session,
        token_name: str,
        event_type: str,
        scopes: List[str],
        plant_code: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> EventJournal:
        """Atomically increment cache token and append journal entry in current transaction.
        
        Must be called BEFORE db.commit() to ensure atomicity.
        """
        token = db.get(CacheToken, token_name)
        if not token:
            token = CacheToken(token_name=token_name, token_version=1)
            db.add(token)
            db.flush()

        token.token_version += 1
        token.last_invalidated_at = datetime.now(timezone.utc)
        
        journal_entry = EventJournal(
            event_type=event_type,
            scopes=scopes,
            plant_code=plant_code,
            payload_json=payload or {},
            token_version=token.token_version,
            occurred_at=datetime.now(timezone.utc),
        )
        db.add(journal_entry)
        db.flush()
        return journal_entry
