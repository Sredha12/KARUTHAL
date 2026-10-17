from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_officer, verify_case_scope
from app.models import CaseHistory, Officer, Report
from app.routers.cases import find_report_by_case_id

router = APIRouter(prefix="/api/cases", tags=["Case History"])


@router.get("/{case_id}/history")
def get_case_history(
    case_id: str,
    db: Session = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    """
    Retrieve chronological audit trail of all operational events for a case.
    Strict privacy rule: audit logs contain non-sensitive event identifiers only.
    No descriptions, child names, or confidential notes are exposed in history logs.
    """
    report = find_report_by_case_id(case_id, db)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' not found.",
        )

    verify_case_scope(report, officer, db)

    history_records = (
        db.query(CaseHistory)
        .filter(CaseHistory.report_id == report.id)
        .order_by(CaseHistory.id.asc())
        .all()
    )

    result = []
    for h in history_records:
        actor_name = None
        if h.actor_officer_id:
            actor = db.query(Officer).filter(Officer.id == h.actor_officer_id).first()
            if actor:
                actor_name = f"{actor.name} ({actor.role})"

        result.append({
            "id": h.id,
            "entity_type": h.entity_type,
            "entity_id": h.entity_id,
            "action": h.action,
            "details": h.details,
            "actor_officer_id": h.actor_officer_id,
            "actor_name": actor_name,
            "created_at": h.created_at.isoformat() if h.created_at else None,
        })

    return {
        "case_id": report.report_id,
        "count": len(result),
        "history": result,
    }
