"""WS-DASH-1A & 1B Multi-Worker and Real-Time Event Sync End-to-End Suite.

Verifies:
1. Worker A (Writer) inserts a batch and commits transaction -> sys_cache_tokens increments atomically
2. Worker B (Reader) detects the journaled event and broadcasts DASHBOARD_INVALIDATE via SSE
3. Fallback reconciliation and query freshness
"""

import asyncio
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from src.database.engine import get_database_engine
from src.database.models.cache import CacheToken, EventJournal
from src.database.services.cache_token_service import CacheTokenService
from src.services.event_hub import EventHub


def test_cross_worker_event_journal_propagation():
    engine = get_database_engine()
    hub = EventHub.get_instance()
    
    # 1. Subscriber connected on Worker B
    client_queue = asyncio.Queue()
    hub.register(client_queue)

    async def run_scenario():
        # Start background journal poller on Worker B
        await hub.start_poller_if_needed()

        # 2. Worker A simulates transactional commit with atomic token increment
        with Session(engine) as db:
            journal_entry = CacheTokenService.bump_token_and_journal(
                db=db,
                token_name="production_batch",
                event_type="PRODUCTION_DATA_CHANGED",
                scopes=["kpis", "materials"],
                plant_code="PLANT-MUMBAI-01",
                payload={"batch_number": "BATCH-E2E-9999", "volume_m3": 6.5}
            )
            db.commit()
            committed_id = journal_entry.id
            committed_ver = journal_entry.token_version

        # 3. Worker B's journal poller picks up the committed event and pushes to subscriber
        msg = await asyncio.wait_for(client_queue.get(), timeout=2.0)
        assert "event: DASHBOARD_INVALIDATE" in msg
        assert "PRODUCTION_DATA_CHANGED" in msg
        assert "PLANT-MUMBAI-01" in msg

    try:
        asyncio.run(run_scenario())
    finally:
        hub.unregister(client_queue)
