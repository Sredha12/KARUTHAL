import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_optional_officer, enforce_district_scope
from app.models import District, Officer, Panchayat, Report
from app.schemas import ReportCreate
from app.security import hash_password
from app.seed_data import ALLOWED_CATEGORIES
from app.services.history_service import record_history
from app.services.location_service import validate_kerala_coordinates

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


def serialize_report(r: Report, is_minimal: bool = False) -> dict:
    if is_minimal:
        return {
            "case_id": r.report_id,
            "report_id": r.report_id,
            "district": r.district,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "privacy_notice": "Public view restricted to status verification only. No personal details are stored or disclosed.",
        }

    has_loc = bool(
        (r.approx_lat is not None and r.approx_lng is not None)
        or (r.location_text and r.location_text.strip())
        or (r.ward and r.ward.strip())
    )

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
        "has_location": has_loc,
        "routed_district": r.routed_district or r.district,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        "solved_at": r.solved_at.isoformat() if r.solved_at else None,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_report(report_in: ReportCreate, db: Session = Depends(get_db)):
    # 1. Validate Category against allowed classifications
    if report_in.category not in ALLOWED_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid category '{report_in.category}'. Allowed categories: {', '.join(ALLOWED_CATEGORIES)}.",
        )

    # 2. Validate District
    district_obj = db.query(District).filter(District.name == report_in.district).first()
    if not district_obj:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"District '{report_in.district}' is not recognized. Must be one of Kerala's 14 revenue districts.",
        )

    # 3. Validate Panchayat exists and belongs to the specified District
    panchayat_obj = (
        db.query(Panchayat)
        .filter(
            Panchayat.district_id == district_obj.id,
            Panchayat.name == report_in.panchayat,
        )
        .first()
    )
    if not panchayat_obj:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Panchayat '{report_in.panchayat}' does not belong to district '{report_in.district}'.",
        )

    # 4. Validate geographic coordinates against Kerala boundaries
    validate_kerala_coordinates(report_in.approx_lat, report_in.approx_lng)

    # Privacy rule: coordinates stored ONLY if explicit consent granted, rounded to 2 decimal places (~1 km)
    stored_lat: float | None = None
    stored_lng: float | None = None
    if report_in.location_consent and report_in.approx_lat is not None and report_in.approx_lng is not None:
        stored_lat = round(float(report_in.approx_lat), 2)
        stored_lng = round(float(report_in.approx_lng), 2)

    # 5. Generate unique Case ID with collision retry
    case_id = generate_unique_report_id(db)

    # 6. Generate anonymous reporter callback token (Stage 12)
    reporter_token = secrets.token_urlsafe(24)
    reporter_token_hash = hash_password(reporter_token)

    # 7. Safe atomic creation
    try:
        report_db = Report(
            report_id=case_id,
            district_id=district_obj.id,
            panchayat_id=panchayat_obj.id,
            district=district_obj.name,
            panchayat=panchayat_obj.name,
            category=report_in.category,
            description=report_in.description,
            status="Submitted",
            is_urgent=report_in.is_urgent,
            location_text=report_in.location_text.strip() if report_in.location_text else None,
            ward=report_in.ward.strip() if report_in.ward else None,
            approx_lat=stored_lat,
            approx_lng=stored_lng,
            location_consent=report_in.location_consent,
            location_source=report_in.location_source,
            routed_district=district_obj.name,
            reporter_token_hash=reporter_token_hash,
        )
        db.add(report_db)
        db.flush()

        # Record audit history for creation
        record_history(
            db=db,
            entity_type="report",
            entity_id=report_db.id,
            action="Report Submitted",
            details="Public report received via portal",
            report_id=report_db.id,
        )

        db.commit()
        db.refresh(report_db)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit report. Database transaction rolled back safely.",
        )

    serialized = serialize_report(report_db, is_minimal=False)
    return {
        "message": "Demo report submitted successfully",
        "report": serialized,
        "reporter_token": reporter_token,
    }


@router.get("")
def list_reports(db: Session = Depends(get_db)):
    reports = db.query(Report).order_by(Report.id.desc()).all()
    return {
        "count": len(reports),
        "reports": [serialize_report(r, is_minimal=False) for r in reports],
    }


@router.get("/{case_id}")
def get_report(
    case_id: str,
    db: Session = Depends(get_db),
    officer: Officer | None = Depends(get_optional_officer),
):
    """
    Public case status lookup.
    Returns a minimal privacy-preserving view for unauthenticated public requests.
    Authorized officers in scope receive full case details.
    """
    report_db = db.query(Report).filter(Report.report_id == case_id).first()
    if not report_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    if officer:
        # Officer is authenticated: verify district scope
        enforce_district_scope(officer, report_db.district)
        return serialize_report(report_db, is_minimal=False)

    # Public unauthenticated view: minimal sanitized status only
    return serialize_report(report_db, is_minimal=True)
