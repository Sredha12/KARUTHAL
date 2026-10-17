from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_officer, enforce_district_scope, require_roles
from app.models import Assignment, Officer, Report
from app.routers.cases import find_report_by_case_id
from app.schemas import AssignmentRead, CaseAssignRequest
from app.services.history_service import record_history

router = APIRouter(prefix="/api", tags=["Assignments"])


def serialize_assignment(a: Assignment) -> dict:
    return {
        "id": a.id,
        "report_id": a.report_id,
        "assigned_to_id": a.assigned_to_id,
        "assigned_to_name": a.assigned_to.name if a.assigned_to else "Unknown",
        "assigned_by_id": a.assigned_by_id,
        "assigned_by_name": a.assigned_by.name if a.assigned_by else "Unknown",
        "notes": a.notes,
        "is_active": a.is_active,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }


@router.post("/cases/{case_id}/assign")
def assign_case(
    case_id: str,
    request: CaseAssignRequest,
    db: Session = Depends(get_db),
    officer: Officer = Depends(require_roles("dcpu_officer", "admin")),
):
    """
    Assign a child-protection case to an active field officer within the same district.
    Only DCPU officers and State Administrators may assign cases.
    Automatically transitions case status to 'Assigned' and records assignment history.
    """
    # 1. Lookup case
    report = find_report_by_case_id(case_id, db)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' not found.",
        )

    # 2. Assigner must have jurisdiction over the case district
    enforce_district_scope(officer, report.district)

    # 3. Lookup and validate target field officer
    target_officer = db.query(Officer).filter(Officer.id == request.field_officer_id).first()
    if not target_officer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Field officer with ID {request.field_officer_id} not found.",
        )

    if not target_officer.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot assign case to an inactive officer account.",
        )

    if target_officer.role != "field_officer":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Target officer role is '{target_officer.role}'. Only 'field_officer' can receive case assignments.",
        )

    # 4. Target officer must belong to the exact same district
    if target_officer.district != report.district:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"District mismatch: target officer belongs to '{target_officer.district}', "
                f"while case is located in '{report.district}'."
            ),
        )

    # 5. Deactivate prior active assignments for this case (keeps history)
    db.query(Assignment).filter(
        Assignment.report_id == report.id,
        Assignment.is_active.is_(True),
    ).update({"is_active": False})

    # 6. Create new assignment
    new_assignment = Assignment(
        report_id=report.id,
        assigned_to_id=target_officer.id,
        assigned_by_id=officer.id,
        notes=request.notes.strip(),
        is_active=True,
    )
    db.add(new_assignment)

    # 7. Update case status to 'Assigned'
    report.status = "Assigned"
    report.updated_at = datetime.now(timezone.utc)

    # 8. Audit trail entry
    record_history(
        db=db,
        entity_type="case",
        entity_id=report.id,
        action="Case Assigned",
        details=f"Assigned to {target_officer.name} ({target_officer.officer_code})",
        actor_officer_id=officer.id,
        report_id=report.id,
    )

    db.commit()
    db.refresh(new_assignment)

    return {
        "message": "Case assigned successfully",
        "assignment": serialize_assignment(new_assignment),
        "case_status": report.status,
    }


@router.get("/assignments")
def list_assignments(
    case_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    """List case assignments scoped by district or specific case."""
    query = db.query(Assignment).join(Report, Assignment.report_id == Report.id)

    if case_id:
        report = find_report_by_case_id(case_id, db)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case '{case_id}' not found.",
            )
        enforce_district_scope(officer, report.district)
        query = query.filter(Assignment.report_id == report.id)
    else:
        if officer.role != "admin":
            query = query.filter(Report.district == officer.district)

    assignments = query.order_by(Assignment.id.desc()).all()
    return {
        "count": len(assignments),
        "assignments": [serialize_assignment(a) for a in assignments],
    }
