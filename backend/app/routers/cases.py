from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_officer, verify_case_scope, enforce_district_scope
from app.models import Assignment, CaseHistory, Officer, Report
from app.schemas import CaseStatusUpdate
from app.seed_data import ALLOWED_STATUSES
from app.services.history_service import record_history

router = APIRouter(prefix="/api/cases", tags=["Cases"])


def serialize_case(r: Report) -> dict:
    return {
        "id": r.id,
        "case_id": r.report_id,
        "report_id": r.report_id,
        "district": r.district,
        "district_id": r.district_id,
        "panchayat": r.panchayat,
        "panchayat_id": r.panchayat_id,
        "location": r.panchayat,
        "category": r.category,
        "abuse_type": r.category,
        "description": r.description,
        "status": r.status,
        "is_urgent": r.is_urgent,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        "solved_at": r.solved_at.isoformat() if r.solved_at else None,
        "solved_by": r.solved_by,
    }


def find_report_by_case_id(case_id_or_id: str, db: Session) -> Report | None:
    """Lookup report by public report_id (e.g. KAR-XXXXXXXX) or numeric database id."""
    report = db.query(Report).filter(Report.report_id == case_id_or_id).first()
    if not report and case_id_or_id.isdigit():
        report = db.query(Report).filter(Report.id == int(case_id_or_id)).first()
    return report


@router.get("")
def list_cases(
    district: str | None = Query(default=None),
    panchayat_id: int | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    assigned_to_me: bool = Query(default=False),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    """
    List child-protection cases with role-based and district-scoped access.
    DCPU officers view cases within their district.
    Field officers view only cases assigned to them.
    State administrators can view statewide cases.
    """
    query = db.query(Report)

    if officer.role == "admin":
        if district:
            query = query.filter(Report.district == district)
    elif officer.role == "dcpu_officer":
        enforce_district_scope(officer, officer.district)
        query = query.filter(Report.district == officer.district)
    elif officer.role == "field_officer":
        # Field officer restricted strictly to assigned cases
        assigned_report_ids = [
            a.report_id
            for a in db.query(Assignment.report_id)
            .filter(
                Assignment.assigned_to_id == officer.id,
                Assignment.is_active.is_(True),
            )
            .all()
        ]
        query = query.filter(Report.id.in_(assigned_report_ids))

    if assigned_to_me and officer.role != "field_officer":
        assigned_ids = [
            a.report_id
            for a in db.query(Assignment.report_id)
            .filter(
                Assignment.assigned_to_id == officer.id,
                Assignment.is_active.is_(True),
            )
            .all()
        ]
        query = query.filter(Report.id.in_(assigned_ids))

    if panchayat_id is not None:
        query = query.filter(Report.panchayat_id == panchayat_id)

    if status_filter:
        query = query.filter(Report.status == status_filter)

    total_count = query.count()
    cases = query.order_by(Report.id.desc()).offset(skip).limit(limit).all()

    return {
        "total": total_count,
        "cases": [serialize_case(c) for c in cases],
    }


@router.get("/{case_id}")
def get_case_detail(
    case_id: str,
    db: Session = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    """Retrieve full operational details for a case within the officer's scope."""
    report = find_report_by_case_id(case_id, db)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' not found.",
        )

    verify_case_scope(report, officer, db)
    return serialize_case(report)


@router.patch("/{case_id}/status")
def update_case_status(
    case_id: str,
    status_update: CaseStatusUpdate,
    db: Session = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    """
    Update workflow status of a case.
    Statuses: Submitted, Under Review, Assigned, Visit Recorded, Referred, Solved.
    """
    if status_update.status not in ALLOWED_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status '{status_update.status}'. Allowed statuses: {', '.join(ALLOWED_STATUSES)}.",
        )

    report = find_report_by_case_id(case_id, db)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' not found.",
        )

    verify_case_scope(report, officer, db)

    old_status = report.status
    report.status = status_update.status
    report.updated_at = datetime.now(timezone.utc)

    if status_update.status == "Solved":
        report.solved_at = datetime.now(timezone.utc)
        report.solved_by = officer.id

    record_history(
        db=db,
        entity_type="case",
        entity_id=report.id,
        action="Status Updated",
        details=f"Status transitioned from '{old_status}' to '{status_update.status}'",
        actor_officer_id=officer.id,
        report_id=report.id,
    )

    db.commit()
    db.refresh(report)

    return serialize_case(report)
