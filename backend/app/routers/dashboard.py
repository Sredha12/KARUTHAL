from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_officer, enforce_district_scope
from app.models import District, EmergencyCall, Officer, Report
from app.schemas import CaseStatusUpdate, OfficerDashboardResponse
from app.seed_data import ALLOWED_STATUSES
from app.services.history_service import record_history

router = APIRouter(prefix="/api", tags=["Officer Dashboard"])


def serialize_report_for_ui(r: Report) -> dict:
    """Exact field format expected by ReportsTable.jsx and OfficerDashboard.jsx."""
    return {
        "id": r.id,
        "case_id": r.report_id,
        "report_id": r.report_id,
        "status": r.status,
        "category": r.category,
        "abuse_type": r.category,
        "panchayat": r.panchayat,
        "location": r.panchayat,
        "district": r.district,
        "description": r.description,
        "is_urgent": r.is_urgent,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        "solved_at": r.solved_at.isoformat() if r.solved_at else None,
    }


def serialize_call_for_ui(c: EmergencyCall) -> dict:
    """Exact field format expected by EmergencyAlertCard.jsx and OfficerDashboard.jsx."""
    return {
        "id": c.id,
        "call_id": c.call_ref,
        "call_ref": c.call_ref,
        "status": c.status,
        "category": c.category,
        "district": c.district,
        "description": c.description,
        "notes": c.notes,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        "related_report_id": c.related_report_id,
    }


@router.get("/dashboard", response_model=OfficerDashboardResponse)
def get_officer_dashboard(
    district: str = Query(..., description="District jurisdiction name"),
    db: Session = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    """
    Officer dashboard endpoint polled by frontend every 3 seconds.
    Computes real-time statistics and loads recent reports and emergency calls.
    """
    # 1. Validate that the district is a recognized Kerala district
    district_obj = db.query(District).filter(District.name == district).first()
    if not district_obj:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported district '{district}'. Must be one of Kerala's 14 districts.",
        )

    # 2. Scope enforcement: 403 if outside officer's district
    enforce_district_scope(officer, district)

    # 3. Efficient count queries
    total_count = db.query(Report).filter(Report.district == district).count()
    solved_count = db.query(Report).filter(Report.district == district, Report.status == "Solved").count()
    pending_count = db.query(Report).filter(Report.district == district, Report.status != "Solved").count()
    urgent_count = (
        db.query(Report)
        .filter(Report.district == district, Report.is_urgent.is_(True), Report.status != "Solved")
        .count()
    )

    # 4. Fetch reports and emergency calls
    reports = (
        db.query(Report)
        .filter(Report.district == district)
        .order_by(Report.id.desc())
        .limit(100)
        .all()
    )

    calls = (
        db.query(EmergencyCall)
        .filter(EmergencyCall.district == district)
        .order_by(EmergencyCall.id.desc())
        .limit(50)
        .all()
    )

    return {
        "total": total_count,
        "solved": solved_count,
        "pending": pending_count,
        "urgent": urgent_count,
        "reports": [serialize_report_for_ui(r) for r in reports],
        "calls": [serialize_call_for_ui(c) for c in calls],
    }


@router.patch("/report/{report_db_id}")
def patch_report_status(
    report_db_id: int,
    status_update: CaseStatusUpdate,
    db: Session = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    """
    Frontend contract endpoint: PATCH /api/report/{id} {"status":"Solved"}
    Updates report by numeric database id.
    """
    if status_update.status not in ALLOWED_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status '{status_update.status}'. Allowed statuses: {', '.join(ALLOWED_STATUSES)}.",
        )

    report = db.query(Report).filter(Report.id == report_db_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_db_id} not found.",
        )

    # Enforce district scope
    enforce_district_scope(officer, report.district)

    old_status = report.status
    report.status = status_update.status
    report.updated_at = datetime.now(timezone.utc)

    if status_update.status == "Solved":
        report.solved_at = datetime.now(timezone.utc)
        report.solved_by = officer.id

    record_history(
        db=db,
        entity_type="report",
        entity_id=report.id,
        action="Status Updated",
        details=f"Status updated from '{old_status}' to '{status_update.status}' via officer dashboard",
        actor_officer_id=officer.id,
        report_id=report.id,
    )

    db.commit()
    db.refresh(report)

    return serialize_report_for_ui(report)
