"""Real-Time SSE Events API Router.

Provides secure Server-Sent Events stream for immediate dashboard invalidation signals.
"""

import asyncio
import json
import secrets
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from src.database.models.user import User
from src.database.session import get_session_factory
from src.security.dependencies import get_current_user, get_db
from src.security.jwt import decode_and_validate_token
from src.services.event_hub import EventHub

router = APIRouter(prefix="/api/v1/events", tags=["Real-Time Events & SSE"])

# Short-lived in-memory ticket store: ticket -> (user_id, expires_at)
_SSE_TICKETS: Dict[str, tuple[str, float]] = {}


@router.post("/ticket")
def generate_sse_ticket(
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Generate a single-use 60-second SSE ticket for browser EventSource authentication."""
    ticket = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc).timestamp()
    _SSE_TICKETS[ticket] = (current_user.id, now + 60.0)
    
    # Purge expired tickets
    expired = [k for k, v in _SSE_TICKETS.items() if v[1] < now]
    for k in expired:
        _SSE_TICKETS.pop(k, None)

    return {"ticket": ticket, "expires_in_seconds": "60"}


def _authenticate_sse_client(ticket: Optional[str], token: Optional[str]) -> str:
    """Validate SSE connection via ticket or direct JWT token."""
    now = datetime.now(timezone.utc).timestamp()
    if ticket:
        record = _SSE_TICKETS.pop(ticket, None)
        if record and record[1] >= now:
            return record[0]  # user_id
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired SSE ticket.",
        )

    if token:
        try:
            payload = decode_and_validate_token(token, require_full_access=False)
            user_id = payload.get("sub")
            if user_id:
                return user_id
        except Exception:
            pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required for SSE stream. Provide a valid ticket or token.",
    )


@router.get("/stream")
async def sse_event_stream(
    request: Request,
    ticket: Optional[str] = Query(None),
    token: Optional[str] = Query(None),
):
    """Server-Sent Events endpoint streaming real-time dashboard invalidation signals."""
    user_id = _authenticate_sse_client(ticket, token)

    hub = EventHub.get_instance()
    await hub.start_poller_if_needed()

    client_queue: asyncio.Queue = asyncio.Queue(maxsize=50)
    hub.register(client_queue)

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            # Send initial connected handshake frame
            handshake = {
                "event_type": "CONNECTED",
                "message": "SSE Stream Connected",
                "connected_at": datetime.now(timezone.utc).isoformat(),
            }
            yield f"event: CONNECTED\ndata: {json.dumps(handshake)}\n\n"

            while True:
                # Disconnect if client disconnected
                if await request.is_disconnected():
                    break

                try:
                    # Wait for message with 15s timeout for keepalive heartbeat
                    msg = await asyncio.wait_for(client_queue.get(), timeout=15.0)
                    yield msg
                except asyncio.TimeoutError:
                    # Send keepalive ping comment
                    yield f": keepalive {datetime.now(timezone.utc).isoformat()}\n\n"
        finally:
            hub.unregister(client_queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
