import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_officer, get_optional_officer, enforce_district_scope
from app.models import District, EmergencyCall, Officer, Report
from app.routers.cases import find_report_by_case_id
from app.schemas import EmergencyCallCreate, EmergencyCallPatch, EmergencyCallRead
from app.seed_data import ALLOWED_EMERGENCY_STATUSES
from app.services.history_service import record_history

router = APIRouter(prefix="/api/emergency", tags=["Emergency Alerts"])

EMERGENCY_DISCLAIMER = (
    "Prototype record only. Recording an emergency event does NOT contact police, "
    "DCPU, 112, 1098, or emergency services. Human decision-makers must take independent action."
)


def generate_unique_call_ref(db: Session, max_retries: int = 10) -> str:
    """Generate unique 8-character uppercase hex call reference (CALL-XXXXXXXX)."""
    for _ in range(max_retries):
        hex_code = secrets.token_hex(4).upper()
        ref = f"CALL-{hex_code}"
        existing = db.query(EmergencyCall).filter(EmergencyCall.call_ref == ref).first()
        if not existing:
            return ref
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Could not generate unique emergency call reference.",
    )


def serialize_emergency_call(c: EmergencyCall) -> dict:
    return {
        "id": c.id,
        "call_id": c.call_ref,
        "call_ref": c.call_ref,
        "district": c.district,
        "category": c.category,
        "description": c.description,
        "status": c.status,
        "notes": c.notes,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        "related_report_id": c.related_report_id,
        "disclaimer": EMERGENCY_DISCLAIMER,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_emergency_event(
    call_in: EmergencyCallCreate,
    db: Session = Depends(get_db),
    officer: Officer | None = Depends(get_optional_officer),
):
    """
    Log an urgent emergency event.
    Public or authenticated.
    Clear legal notice: this does NOT contact emergency services or authorities.
    """
    # 1. Validate district
    district_obj = db.query(District).filter(District.name == call_in.district).first()
    if not district_obj:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"District '{call_in.district}' is not recognized.",
        )

    # 2. Check related case if provided
    related_report = None
    if call_in.related_case_id:
        related_report = find_report_by_case_id(call_in.related_case_id, db)
        if not related_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Related case '{call_in.related_case_id}' not found.",
            )

    call_ref = generate_unique_call_ref(db)

    call_obj = EmergencyCall(
        call_ref=call_ref,
        district=district_obj.name,
        category=call_in.category,
        description=call_in.description.strip(),
        related_report_id=related_report.id if related_report else None,
        status="Active",
        notes="",
        recorded_by=officer.id if officer else None,
    )
    db.add(call_obj)
    db.flush()

    if related_report:
        record_history(
            db=db,
            entity_type="emergency_call",
            entity_id=call_obj.id,
            action="Emergency Alert Linked",
            details=f"Alert ref {call_ref} linked to case",
            actor_officer_id=officer.id if officer else None,
            report_id=related_report.id,
        )

    db.commit()
    db.refresh(call_obj)

    return {
        "message": "Emergency alert recorded in prototype log. No external authority has been contacted.",
        "call": serialize_emergency_call(call_obj),
        "disclaimer": EMERGENCY_DISCLAIMER,
    }


@router.get("/{event_id}")
def get_emergency_event(
    event_id: str,
    db: Session = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    """Retrieve emergency alert record within officer's jurisdiction."""
    call = db.query(EmergencyCall).filter(EmergencyCall.call_ref == event_id).first()
    if not call and event_id.isdigit():
        call = db.query(EmergencyCall).filter(EmergencyCall.id == int(event_id)).first()

    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Emergency call '{event_id}' not found.",
        )

    enforce_district_scope(officer, call.district)
    return serialize_emergency_call(call)


@router.patch("/{id}")
def patch_emergency_event(
    id: int,
    patch_in: EmergencyCallPatch,
    db: Session = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    """
    Frontend contract endpoint: PATCH /api/emergency/{id} {status, notes?}
    {id} is numeric call database id.
    Allowed statuses: 'Acknowledged', 'Resolved'.
    409 Conflict if already 'Resolved'.
    """
    if patch_in.status not in ("Acknowledged", "Resolved"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid emergency status '{patch_in.status}'. Must be 'Acknowledged' or 'Resolved'.",
        )

    call = db.query(EmergencyCall).filter(EmergencyCall.id == id).first()
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Emergency call with ID {id} not found.",
        )

    enforce_district_scope(officer, call.district)

    if call.status == "Resolved":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot update emergency call: record is already Resolved.",
        )

    call.status = patch_in.status
    if patch_in.notes is not None:
        call.notes = patch_in.notes.strip()
    call.updated_at = datetime.now(timezone.utc)

    if call.related_report_id:
        record_history(
            db=db,
            entity_type="emergency_call",
            entity_id=call.id,
            action="Emergency Alert Updated",
            details=f"Status set to {patch_in.status}",
            actor_officer_id=officer.id,
            report_id=call.related_report_id,
        )

    db.commit()
    db.refresh(call)

    return serialize_emergency_call(call)
