import secrets
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from fastapi import WebSocket
from sqlalchemy.orm import Session

from app.config import settings
from app.models import CallSession
from app.services.history_service import record_history

# Short-lived, single-use WebSocket tickets: ticket -> {call_id, role, expires_at}
WS_TICKETS: dict[str, dict] = {}

# Active WebSocket peer connections per call_id: call_id -> set[WebSocket]
ACTIVE_ROOMS: dict[int, set[WebSocket]] = defaultdict(set)


def create_ws_ticket(call_id: int, role: str, expires_in: int = 60) -> str:
    """Generate a single-use, 60-second valid ticket for WebSocket signalling authentication."""
    ticket = secrets.token_urlsafe(32)
    WS_TICKETS[ticket] = {
        "call_id": call_id,
        "role": role,
        "expires_at": time.time() + expires_in,
    }
    return ticket


def validate_and_consume_ws_ticket(ticket: str, call_id: int) -> dict | None:
    """
    Validate and consume ticket.
    Strictly single-use: removed from memory upon consumption.
    Returns payload if valid and unexpired; None otherwise.
    """
    data = WS_TICKETS.pop(ticket, None)
    if not data:
        return None

    if data["call_id"] != call_id:
        return None

    if time.time() > data["expires_at"]:
        return None

    return data


def check_and_expire_ring_timeouts(
    db: Session,
    timeout_seconds: int | None = None,
) -> int:
    """
    Finds call sessions in 'ringing' status that have exceeded the timeout window
    and marks them as 'missed'.
    """
    timeout = timeout_seconds if timeout_seconds is not None else settings.VOIP_RING_TIMEOUT_SECONDS
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=timeout)

    stale_calls = (
        db.query(CallSession)
        .filter(
            CallSession.status == "ringing",
            CallSession.ringing_at.isnot(None),
        )
        .all()
    )

    expired = []
    now = datetime.now(timezone.utc)
    for c in stale_calls:
        r_at = c.ringing_at
        if r_at is not None:
            if r_at.tzinfo is None:
                r_at = r_at.replace(tzinfo=timezone.utc)
            if r_at <= cutoff:
                expired.append(c)

    expired_count = len(expired)
    for c in expired:
        c.status = "missed"
        c.ended_at = now
        c.end_reason = "missed"

        record_history(
            db=db,
            entity_type="call_session",
            entity_id=c.id,
            action="call_missed",
            details="Call ring timeout expired without answer",
            actor_officer_id=c.officer_id,
            report_id=c.case_id,
        )

    if expired_count > 0:
        db.commit()

    return expired_count
