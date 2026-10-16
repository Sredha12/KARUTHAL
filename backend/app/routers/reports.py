import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Report
from app.schemas import ReportCreate

router = APIRouter(prefix="/api/reports", tags=["Reports"])


def generate_unique_report_id(db: Session, max_retries: int = 10) -> str:
    """Generate unique 8-character uppercase hex case_id (KAR-XXXXXXXX) with collision retry."""
    for _ in range(max_retries):
        hex_code = secrets.token_hex(4).upper()
        case_id = f"KAR-{hex_code}"
        existing = db.query(Report).filter(Report.report_id == case_id).first()
        if not existing:
            return case_id
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Could not generate unique case ID. Please retry.",
    )


def serialize_report(r: Report) -> dict:
    return {
        "case_id": r.report_id,
        "report_id": r.report_id,
        "id": r.id,
        "district": r.district,
        "panchayat": r.panchayat,
        "location": r.panchayat,
        "category": r.category,
        "abuse_type": r.category,
        "description": r.description,
        "status": r.status,
        "is_urgent": r.is_urgent,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        "solved_at": r.solved_at.isoformat() if r.solved_at else None,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_report(report_in: ReportCreate, db: Session = Depends(get_db)):
    case_id = generate_unique_report_id(db)

    report_db = Report(
        report_id=case_id,
        district=report_in.district,
        panchayat=report_in.panchayat,
        category=report_in.category,
        description=report_in.description,
        status="Submitted",
        is_urgent=report_in.is_urgent,
    )
    db.add(report_db)
    db.commit()
    db.refresh(report_db)

    serialized = serialize_report(report_db)
    return {
        "message": "Demo report submitted successfully",
        "report": serialized,
    }


@router.get("")
def list_reports(db: Session = Depends(get_db)):
    reports = db.query(Report).order_by(Report.id.desc()).all()
    return {
        "count": len(reports),
        "reports": [serialize_report(r) for r in reports],
    }


@router.get("/{case_id}")
def get_report(case_id: str, db: Session = Depends(get_db)):
    report_db = db.query(Report).filter(Report.report_id == case_id).first()
    if not report_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    return serialize_report(report_db)
