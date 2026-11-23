"""Asynchronous Event Hub for Real-Time SSE Streaming.

Provides multi-client subscriber queues, keepalive heartbeats, and cross-worker
journal synchronization using sys_event_journal.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, List, Optional, Set
from sqlalchemy.orm import Session
from src.database.engine import get_database_engine
from src.database.models.cache import EventJournal

logger = logging.getLogger(__name__)


class EventHub:
    _instance: Optional["EventHub"] = None

    def __init__(self):
        self._subscribers: Set[asyncio.Queue] = set()
        self._last_polled_id: int = 0
        self._poller_task: Optional[asyncio.Task] = None
        self._initialized = False

    @classmethod
    def get_instance(cls) -> "EventHub":
        if cls._instance is None:
            cls._instance = EventHub()
        return cls._instance

    def register(self, queue: asyncio.Queue) -> None:
        self._subscribers.add(queue)
        logger.debug("Registered SSE client. Total subscribers: %d", len(self._subscribers))

    def unregister(self, queue: asyncio.Queue) -> None:
        self._subscribers.discard(queue)
        logger.debug("Unregistered SSE client. Total subscribers: %d", len(self._subscribers))

    async def broadcast_local(self, event_data: Dict) -> None:
        """Broadcast event directly to local connected subscriber queues."""
        msg = f"event: DASHBOARD_INVALIDATE\ndata: {json.dumps(event_data)}\n\n"
        for q in list(self._subscribers):
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                pass

    async def start_poller_if_needed(self) -> None:
        """Start background task to poll sys_event_journal for cross-worker events."""
        if self._poller_task is None or self._poller_task.done():
            # Initialize last_polled_id to max existing id
            try:
                engine = get_database_engine()
                with Session(engine) as db:
                    latest = db.query(EventJournal.id).order_by(EventJournal.id.desc()).first()
                    self._last_polled_id = latest[0] if latest else 0
            except Exception as e:
                logger.warning("Could not initialize EventHub poller watermark: %s", e)
                self._last_polled_id = 0

            self._poller_task = asyncio.create_task(self._poll_journal_loop())

    async def _poll_journal_loop(self) -> None:
        """Poll sys_event_journal every 250ms for events committed by other workers."""
        engine = get_database_engine()
        while True:
            try:
                await asyncio.sleep(1.0)
                if not self._subscribers:
                    continue

                with Session(engine) as db:
                    new_events = (
                        db.query(EventJournal)
                        .filter(EventJournal.id > self._last_polled_id)
                        .order_by(EventJournal.id.asc())
                        .all()
                    )
                    for evt in new_events:
                        self._last_polled_id = evt.id
                        event_data = {
                            "event_id": f"evt_{evt.id}",
                            "event_type": evt.event_type,
                            "scopes": evt.scopes,
                            "plant_code": evt.plant_code,
                            "payload": evt.payload_json,
                            "token_version": evt.token_version,
                            "occurred_at": evt.occurred_at.isoformat() if evt.occurred_at else None,
                        }
                        await self.broadcast_local(event_data)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug("EventHub polling error: %s", e)
                await asyncio.sleep(1.0)
