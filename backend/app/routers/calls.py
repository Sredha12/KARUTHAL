from datetime import datetime, timedelta, timezone
from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import (
    enforce_district_scope,
    get_current_officer,
    get_optional_officer,
    verify_case_scope,
)
from app.models import CallSession, Officer, Report
from app.routers.cases import find_report_by_case_id
from app.schemas import (
    CallSessionRead,
    IceConfigResponse,
    OfficerStartCallRequest,
    WsTicketResponse,
)
from app.security import verify_password
from app.services.history_service import record_history
from app.services.voip_service import (
    ACTIVE_ROOMS,
    create_ws_ticket,
    validate_and_consume_ws_ticket,
)

router = APIRouter(tags=["VoIP Call Sessions"])

SIMULATED_NOTICE = "Simulated prototype call. No real helpline or authority is contacted."


def serialize_call_session(c: CallSession) -> dict:
    return {
        "id": c.id,
        "case_id": c.case_id,
        "report_id": c.report.report_id if c.report else f"CASE-{c.case_id}",
        "requested_by": c.requested_by,
        "officer_id": c.officer_id,
        "officer_name": c.officer.name if c.officer else None,
        "status": c.status,
        "created_at": c.created_at,
        "ringing_at": c.ringing_at,
        "connected_at": c.connected_at,
        "ended_at": c.ended_at,
        "end_reason": c.end_reason,
        "duration_seconds": c.duration_seconds,
        "mode": c.mode,
        "simulated": True,
        "notice": SIMULATED_NOTICE,
    }


def authenticate_participant(
    call: CallSession,
    officer: Officer | None,
    x_reporter_token: str | None,
    db: Session,
) -> str:
    """
    Authenticate whether caller is an authorized participant (either case officer or reporter).
    Returns 'officer' or 'reporter', or raises 401/403.
    """
    # 1. Try Officer authentication
    if officer:
        enforce_district_scope(officer, call.report.district)
        return "officer"

    # 2. Try Reporter token authentication
    if x_reporter_token:
        if call.report.reporter_token_hash and verify_password(x_reporter_token, call.report.reporter_token_hash):
            return "reporter"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid reporter token for this case.",
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide Bearer token (officer) or X-Reporter-Token header.",
    )


def check_daily_call_limit(case_id: int, db: Session) -> None:
    """Ensure the case has not exceeded the daily call rate limit."""
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(hours=24)
    recent_calls_count = (
        db.query(CallSession)
        .filter(CallSession.case_id == case_id, CallSession.created_at >= day_ago)
        .count()
    )
    if recent_calls_count >= settings.VOIP_MAX_CALLS_PER_CASE_PER_DAY:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Daily call limit reached for this case "
                f"({settings.VOIP_MAX_CALLS_PER_CASE_PER_DAY} calls/day max)."
            ),
        )


def check_no_active_call_session(case_id: int, db: Session) -> None:
    """Ensure only one active call session exists for a case at any time."""
    active_session = (
        db.query(CallSession)
        .filter(
            CallSession.case_id == case_id,
            CallSession.status.in_(["requested", "ringing", "connected"]),
        )
        .first()
    )
    if active_session:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An active call session ({active_session.status}) already exists for this case.",
        )


# --- Reporter Callback Request ---

@router.post("/api/reports/{report_id}/callback-request", status_code=status.HTTP_201_CREATED)
def request_callback(
    report_id: str,
    x_reporter_token: str | None = Header(default=None, alias="X-Reporter-Token"),
    db: Session = Depends(get_db),
):
    """
    Reporter requests a voice callback for their submitted report using their anonymous token.
    Rate-limited per case per day.
    """
    report = find_report_by_case_id(report_id, db)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_id}' not found.",
        )

    if not x_reporter_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Reporter-Token header.",
        )

    if not report.reporter_token_hash or not verify_password(x_reporter_token, report.reporter_token_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid reporter token for this report.",
        )

    if report.status == "Solved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot request callback on a resolved case.",
        )

    check_daily_call_limit(report.id, db)
    check_no_active_call_session(report.id, db)

    call = CallSession(
        case_id=report.id,
        requested_by="reporter",
        status="requested",
        mode=settings.VOIP_MODE,
        simulated=True,
    )
    db.add(call)
    db.flush()

    record_history(
        db=db,
        entity_type="call_session",
        entity_id=call.id,
        action="call_requested",
        details="Anonymous reporter requested voice callback",
        report_id=report.id,
    )
    db.commit()
    db.refresh(call)

    return {
        "call": serialize_call_session(call),
        "simulated": True,
        "notice": SIMULATED_NOTICE,
    }


# --- Officer Call Management ---

@router.get("/api/cases/{case_id}/calls")
def list_case_calls(
    case_id: str,
    db: Session = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    """List all voice call sessions for a case within officer's district jurisdiction."""
    report = find_report_by_case_id(case_id, db)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' not found.",
        )

    verify_case_scope(report, officer, db)

    calls = (
        db.query(CallSession)
        .filter(CallSession.case_id == report.id)
        .order_by(CallSession.id.desc())
        .all()
    )

    return {
        "count": len(calls),
        "calls": [serialize_call_session(c) for c in calls],
        "simulated": True,
        "notice": SIMULATED_NOTICE,
    }


@router.post("/api/cases/{case_id}/calls", status_code=status.HTTP_201_CREATED)
def start_case_call(
    case_id: str,
    req: OfficerStartCallRequest,
    db: Session = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    """
    Officer initiates or answers a voice call session with the reporter.
    Transitions session to 'ringing'.
    """
    report = find_report_by_case_id(case_id, db)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' not found.",
        )

    verify_case_scope(report, officer, db)

    if report.status == "Solved":
        if not req.override_solved:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Case is already Solved. Set override_solved=true to initiate call.",
            )
        record_history(
            db=db,
            entity_type="call_session",
            entity_id=report.id,
            action="call_override_logged",
            details="Officer overrode solved case status to initiate call",
            actor_officer_id=officer.id,
            report_id=report.id,
        )

    check_daily_call_limit(report.id, db)

    # Check for active session
    active_session = (
        db.query(CallSession)
        .filter(
            CallSession.case_id == report.id,
            CallSession.status.in_(["requested", "ringing", "connected"]),
        )
        .first()
    )

    now = datetime.now(timezone.utc)

    if active_session:
        # If there is an existing 'requested' session, officer's action starts ringing it
        if active_session.status == "requested":
            active_session.status = "ringing"
            active_session.officer_id = officer.id
            active_session.ringing_at = now
            record_history(
                db=db,
                entity_type="call_session",
                entity_id=active_session.id,
                action="call_started",
                details=f"Officer {officer.officer_code} initiated ringing for callback request",
                actor_officer_id=officer.id,
                report_id=report.id,
            )
            db.commit()
            db.refresh(active_session)
            return {
                "call": serialize_call_session(active_session),
                "simulated": True,
                "notice": SIMULATED_NOTICE,
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"An active call session ({active_session.status}) already exists for this case.",
            )

    # Otherwise create new ringing session
    call = CallSession(
        case_id=report.id,
        requested_by="officer",
        officer_id=officer.id,
        status="ringing",
        ringing_at=now,
        mode=settings.VOIP_MODE,
        simulated=True,
    )
    db.add(call)
    db.flush()

    record_history(
        db=db,
        entity_type="call_session",
        entity_id=call.id,
        action="call_started",
        details=f"Officer {officer.officer_code} initiated outbound call session",
        actor_officer_id=officer.id,
        report_id=report.id,
    )
    db.commit()
    db.refresh(call)

    return {
        "call": serialize_call_session(call),
        "simulated": True,
        "notice": SIMULATED_NOTICE,
    }


# --- Call Participant Lifecycle Actions ---

@router.get("/api/calls/ice-config", response_model=IceConfigResponse)
def get_ice_config(
    officer: Officer | None = Depends(get_optional_officer),
):
    """Retrieve STUN/TURN ICE server configuration."""
    return {
        "ice_servers": settings.VOIP_ICE_SERVERS,
        "mode": settings.VOIP_MODE,
        "simulated": True,
    }


@router.get("/api/calls/{call_id}")
def get_call_session(
    call_id: int,
    db: Session = Depends(get_db),
    officer: Officer | None = Depends(get_optional_officer),
    x_reporter_token: str | None = Header(default=None, alias="X-Reporter-Token"),
):
    """Retrieve call session status for authorized participants."""
    call = db.query(CallSession).filter(CallSession.id == call_id).first()
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call session {call_id} not found.",
        )

    authenticate_participant(call, officer, x_reporter_token, db)
    return {
        "call": serialize_call_session(call),
        "simulated": True,
        "notice": SIMULATED_NOTICE,
    }


@router.post("/api/calls/{call_id}/accept")
def accept_call(
    call_id: int,
    db: Session = Depends(get_db),
    officer: Officer | None = Depends(get_optional_officer),
    x_reporter_token: str | None = Header(default=None, alias="X-Reporter-Token"),
):
    """
    Accept an incoming call session.
    Transitions status to 'connected'.
    """
    call = db.query(CallSession).filter(CallSession.id == call_id).first()
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call session {call_id} not found.",
        )

    role = authenticate_participant(call, officer, x_reporter_token, db)

    if call.status == "connected":
        return {
            "call": serialize_call_session(call),
            "simulated": True,
            "notice": SIMULATED_NOTICE,
        }

    if call.status not in ("ringing", "requested"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Illegal call transition: cannot accept call in '{call.status}' state.",
        )

    now = datetime.now(timezone.utc)
    call.status = "connected"
    call.connected_at = now

    record_history(
        db=db,
        entity_type="call_session",
        entity_id=call.id,
        action="call_connected",
        details=f"Call connected by {role}",
        actor_officer_id=officer.id if officer else None,
        report_id=call.case_id,
    )
    db.commit()
    db.refresh(call)

    return {
        "call": serialize_call_session(call),
        "simulated": True,
        "notice": SIMULATED_NOTICE,
    }


@router.post("/api/calls/{call_id}/decline")
def decline_call(
    call_id: int,
    db: Session = Depends(get_db),
    officer: Officer | None = Depends(get_optional_officer),
    x_reporter_token: str | None = Header(default=None, alias="X-Reporter-Token"),
):
    """Decline an incoming call session."""
    call = db.query(CallSession).filter(CallSession.id == call_id).first()
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call session {call_id} not found.",
        )

    role = authenticate_participant(call, officer, x_reporter_token, db)

    if call.status not in ("requested", "ringing"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Illegal call transition: cannot decline call in '{call.status}' state.",
        )

    now = datetime.now(timezone.utc)
    call.status = "declined"
    call.ended_at = now
    call.end_reason = "declined"

    record_history(
        db=db,
        entity_type="call_session",
        entity_id=call.id,
        action="call_declined",
        details=f"Call declined by {role}",
        actor_officer_id=officer.id if officer else None,
        report_id=call.case_id,
    )
    db.commit()
    db.refresh(call)

    return {
        "call": serialize_call_session(call),
        "simulated": True,
        "notice": SIMULATED_NOTICE,
    }


@router.post("/api/calls/{call_id}/end")
def end_call(
    call_id: int,
    db: Session = Depends(get_db),
    officer: Officer | None = Depends(get_optional_officer),
    x_reporter_token: str | None = Header(default=None, alias="X-Reporter-Token"),
):
    """
    End an active or pending call session.
    Calculates duration in seconds if connected.
    """
    call = db.query(CallSession).filter(CallSession.id == call_id).first()
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call session {call_id} not found.",
        )

    role = authenticate_participant(call, officer, x_reporter_token, db)

    if call.status in ("ended", "declined", "missed", "cancelled"):
        return {
            "call": serialize_call_session(call),
            "simulated": True,
            "notice": SIMULATED_NOTICE,
        }

    now = datetime.now(timezone.utc)
    call.ended_at = now

    if call.status == "connected":
        call.status = "ended"
        call.end_reason = "normal"
        if call.connected_at:
            conn_at = call.connected_at
            if conn_at.tzinfo is None:
                conn_at = conn_at.replace(tzinfo=timezone.utc)
            duration = int((now - conn_at).total_seconds())
            call.duration_seconds = max(0, duration)
        action_name = "call_ended"
        action_desc = f"Call completed ({call.duration_seconds}s) ended by {role}"
    else:
        call.status = "cancelled"
        call.end_reason = "cancelled"
        action_name = "call_cancelled"
        action_desc = f"Call cancelled before connection by {role}"

    record_history(
        db=db,
        entity_type="call_session",
        entity_id=call.id,
        action=action_name,
        details=action_desc,
        actor_officer_id=officer.id if officer else None,
        report_id=call.case_id,
    )
    db.commit()
    db.refresh(call)

    return {
        "call": serialize_call_session(call),
        "simulated": True,
        "notice": SIMULATED_NOTICE,
    }


# --- WebRTC & Signalling Helpers ---



@router.post("/api/calls/{call_id}/ws-ticket", response_model=WsTicketResponse)
def get_ws_ticket(
    call_id: int,
    db: Session = Depends(get_db),
    officer: Officer | None = Depends(get_optional_officer),
    x_reporter_token: str | None = Header(default=None, alias="X-Reporter-Token"),
):
    """
    Generate a single-use ticket for authenticating the WebSocket signalling channel.
    Avoids putting sensitive JWT tokens into URL query strings. Ticket expires in 60 seconds.
    """
    call = db.query(CallSession).filter(CallSession.id == call_id).first()
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call session {call_id} not found.",
        )

    role = authenticate_participant(call, officer, x_reporter_token, db)
    ticket = create_ws_ticket(call_id=call.id, role=role, expires_in=60)

    return {
        "ticket": ticket,
        "expires_in": 60,
        "simulated": True,
    }


@router.websocket("/api/calls/{call_id}/signal")
async def websocket_signalling_relay(
    websocket: WebSocket,
    call_id: int,
    ticket: str = Query(..., description="Single-use ticket from /api/calls/{call_id}/ws-ticket"),
):
    """
    Relays WebRTC / simulated JSON signalling messages between the two call participants.
    Strict limits: maximum 2 participants per call room. Messages relayed strictly peer-to-peer.
    """
    ticket_data = validate_and_consume_ws_ticket(ticket, call_id)
    if not ticket_data:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()

    room = ACTIVE_ROOMS[call_id]
    if len(room) >= 2:
        await websocket.send_json({"error": "Room is full (max 2 participants)."})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    room.add(websocket)

    try:
        # Notify other peer that someone joined
        for peer in list(room):
            if peer != websocket:
                await peer.send_json({"type": "peer_joined", "role": ticket_data["role"]})

        while True:
            data = await websocket.receive_json()
            # Forward message untouched to the other participant
            for peer in list(room):
                if peer != websocket:
                    await peer.send_json(data)
    except WebSocketDisconnect:
        pass
    finally:
        room.discard(websocket)
        for peer in list(room):
            try:
                await peer.send_json({"type": "peer_disconnected", "role": ticket_data["role"]})
            except Exception:
                pass
        if not room:
            ACTIVE_ROOMS.pop(call_id, None)
