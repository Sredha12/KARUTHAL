from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_officer, verify_case_scope
from app.models import Assignment, FieldVisit, Officer, Report
from app.routers.cases import find_report_by_case_id
from app.schemas import FieldVisitCreate, FieldVisitRead
from app.seed_data import ALLOWED_VISIT_OUTCOMES
from app.services.history_service import record_history

router = APIRouter(prefix="/api/cases", tags=["Field Visits"])


def serialize_field_visit(v: FieldVisit) -> dict:
    return {
        "id": v.id,
        "report_id": v.report_id,
        "field_officer_id": v.field_officer_id,
        "field_officer_name": v.officer.name if v.officer else "Field Officer",
        "visit_at": v.visit_at.isoformat() if v.visit_at else None,
        "outcome": v.outcome,
        "notes": v.notes,
        "created_at": v.created_at.isoformat() if v.created_at else None,
    }


@router.post("/{case_id}/field-visits", status_code=status.HTTP_201_CREATED)
def record_field_visit(
    case_id: str,
    visit_in: FieldVisitCreate,
    db: Session = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    """
    Record an on-site assessment visit for an assigned case.
    Strict privacy rule: NO GPS, geolocation coordinates, or personal tracking data are captured.
    Only the currently assigned field officer (or admin) may record a visit.
    Transitions case status to 'Visit Recorded'.
    """
    # 1. Lookup case
    report = find_report_by_case_id(case_id, db)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' not found.",
        )

    # 2. Check that the officer is the currently assigned field officer (or admin)
    if officer.role != "admin":
        if officer.role != "field_officer":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only field officers assigned to the case may record field visits.",
            )

        is_assigned = (
            db.query(Assignment)
            .filter(
                Assignment.report_id == report.id,
                Assignment.assigned_to_id == officer.id,
                Assignment.is_active.is_(True),
            )
            .first()
        )
        if not is_assigned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You are not actively assigned to this case.",
            )

    # 3. Validate outcome against allowed classifications
    if visit_in.outcome not in ALLOWED_VISIT_OUTCOMES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid visit outcome '{visit_in.outcome}'. Allowed: {', '.join(ALLOWED_VISIT_OUTCOMES)}.",
        )

    # 4. Save field visit record
    visit_obj = FieldVisit(
        report_id=report.id,
        field_officer_id=officer.id,
        visit_at=visit_in.visit_at,
        outcome=visit_in.outcome,
        notes=visit_in.notes.strip(),
    )
    db.add(visit_obj)

    # 5. Advance case status
    report.status = "Visit Recorded"
    report.updated_at = datetime.now(timezone.utc)

    # 6. Audit trail entry
    record_history(
        db=db,
        entity_type="case",
        entity_id=report.id,
        action="Field Visit Recorded",
        details=f"Outcome: {visit_in.outcome}",
        actor_officer_id=officer.id,
        report_id=report.id,
    )

    db.commit()
    db.refresh(visit_obj)

    return {
        "message": "Field visit recorded successfully",
        "field_visit": serialize_field_visit(visit_obj),
        "case_status": report.status,
    }


@router.get("/{case_id}/field-visits")
def get_case_field_visits(
    case_id: str,
    db: Session = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    """Retrieve all logged field visits for a case within the officer's jurisdiction."""
    report = find_report_by_case_id(case_id, db)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' not found.",
        )

    verify_case_scope(report, officer, db)

    visits = (
        db.query(FieldVisit)
        .filter(FieldVisit.report_id == report.id)
        .order_by(FieldVisit.visit_at.desc())
        .all()
    )

    return {
        "count": len(visits),
        "field_visits": [serialize_field_visit(v) for v in visits],
    }
