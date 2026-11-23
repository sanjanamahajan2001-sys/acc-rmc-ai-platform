"""Cache Versioning and Real-Time Event Journal ORM Models.

This module provides database-persisted entities for multi-worker cache token versioning
and authoritative event journaling supporting real-time SSE broadcasts.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import BigInteger, DateTime, JSON, String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from src.database.base import BaseModel


class CacheToken(BaseModel):
    """Authoritative cache invalidation token per domain."""

    __tablename__ = "sys_cache_tokens"

    token_name: Mapped[str] = mapped_column(String(64), primary_key=True)
    token_version: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    last_invalidated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class EventJournal(BaseModel):
    """Durable cross-worker domain event journal for real-time SSE stream."""

    __tablename__ = "sys_event_journal"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    scopes: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    plant_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    payload_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    token_version: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
