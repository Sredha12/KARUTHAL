from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_officer, enforce_district_scope, verify_case_scope, require_roles
from app.models import Assignment, CaseHistory, District, Officer, Referral, Report
from app.routers.cases import find_report_by_case_id
from app.schemas import (
    DcpuDashboardResponse,
    ReferralCreate,
    ReferralMutationResponse,
    ReferralUpdate,
)
from app.seed_data import ALLOWED_REFERRAL_STATUSES
from app.services.history_service import record_history

router = APIRouter(prefix="/api", tags=["Referrals & DCPU Dashboard"])

PROTOTYPE_DISCLAIMER = (
    "Prototype record only. Creating or updating this referral does NOT contact external "
    "agencies, CWC, police, or service providers. Authorized human follow-up is required."
)


def serialize_referral_dcpu(ref: Referral, db: Session) -> dict:
    """Format referral object to match the DcpuDashboard.jsx contract."""
    # Build history timeline from CaseHistory
    case_histories = (
        db.query(CaseHistory)
        .filter(CaseHistory.report_id == ref.report_id)
        .order_by(CaseHistory.id.asc())
        .all()
    )

    history_items = []
    for h in case_histories:
        actor_role = "System"
        if h.actor_officer_id:
            actor = db.query(Officer).filter(Officer.id == h.actor_officer_id).first()
            if actor:
                actor_role = actor.role.replace("_", " ").title()
        history_items.append({
            "at": h.created_at.strftime("%d %b %Y, %I:%M %p") if h.created_at else "",
            "role": actor_role,
            "event": f"{h.action}: {h.details}" if h.details else h.action,
        })

    return {
        "id": ref.id,
        "caseRef": ref.report.report_id if ref.report else f"REF-{ref.id}",
        "district": ref.district,
        "concernCategory": ref.concern_category,
        "receivedAt": ref.created_at.strftime("%d %b %Y") if ref.created_at else "",
        "urgency": ref.urgency,
        "status": ref.status,
        "nextAction": ref.next_action,
        "followUpDue": ref.follow_up_due.strftime("%d %b %Y") if ref.follow_up_due else None,
        "serviceLinkage": {
            "service": ref.service,
            "state": ref.service_state,
        },
        "history": history_items,
    }


@router.post("/cases/{case_id}/referrals", response_model=ReferralMutationResponse, status_code=status.HTTP_201_CREATED)
def create_referral(
    case_id: str,
    referral_in: ReferralCreate,
    db: Session = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    """
    Create a multi-agency service referral for a child-protection case.
    Authorized: DCPU officers, Admin, or the actively assigned field officer.
    Does NOT initiate external agency communication automatically.
    """
    report = find_report_by_case_id(case_id, db)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' not found.",
        )

    verify_case_scope(report, officer, db)

    ref_obj = Referral(
        report_id=report.id,
        district=report.district,
        concern_category=referral_in.concern_category,
        urgency=referral_in.urgency,
        status="New",
        next_action=referral_in.next_action,
        follow_up_due=referral_in.follow_up_due,
        service=referral_in.service,
        service_state="Referred",
        notes=referral_in.notes.strip(),
        created_by_id=officer.id,
    )
    db.add(ref_obj)

    # Advance case status if earlier in workflow
    if report.status in ("Submitted", "Under Review", "Assigned", "Visit Recorded"):
        report.status = "Referred"
        report.updated_at = datetime.now(timezone.utc)

    record_history(
        db=db,
        entity_type="referral",
        entity_id=report.id,
        action="Referral Created",
        details=f"Service: {referral_in.service} (Urgency: {referral_in.urgency})",
        actor_officer_id=officer.id,
        report_id=report.id,
    )

    db.commit()
    db.refresh(ref_obj)

    return {
        "referral": serialize_referral_dcpu(ref_obj, db),
        "confirmed": False,
        "disclaimer": PROTOTYPE_DISCLAIMER,
    }


@router.get("/cases/{case_id}/referrals")
def get_case_referrals(
    case_id: str,
    db: Session = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    """List all referrals linked to a case."""
    report = find_report_by_case_id(case_id, db)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' not found.",
        )

    verify_case_scope(report, officer, db)

    referrals = (
        db.query(Referral)
        .filter(Referral.report_id == report.id)
        .order_by(Referral.id.desc())
        .all()
    )

    return {
        "count": len(referrals),
        "referrals": [serialize_referral_dcpu(r, db) for r in referrals],
    }


@router.patch("/referrals/{referral_id}", response_model=ReferralMutationResponse)
def update_referral(
    referral_id: int,
    patch_in: ReferralUpdate,
    db: Session = Depends(get_db),
    officer: Officer = Depends(require_roles("dcpu_officer", "admin")),
):
    """
    Update referral status, linkage, or follow-up schedule.
    Restricted to DCPU Officers and Admin in jurisdiction.
    """
    ref_obj = db.query(Referral).filter(Referral.id == referral_id).first()
    if not ref_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Referral with ID {referral_id} not found.",
        )

    enforce_district_scope(officer, ref_obj.district)

    if patch_in.status is not None:
        if patch_in.status not in ALLOWED_REFERRAL_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid referral status '{patch_in.status}'. Allowed: {', '.join(ALLOWED_REFERRAL_STATUSES)}.",
            )
        ref_obj.status = patch_in.status

    if patch_in.urgency is not None:
        ref_obj.urgency = patch_in.urgency

    if patch_in.next_action is not None:
        ref_obj.next_action = patch_in.next_action

    if patch_in.follow_up_due is not None:
        ref_obj.follow_up_due = patch_in.follow_up_due

    if patch_in.service is not None:
        ref_obj.service = patch_in.service

    if patch_in.service_state is not None:
        ref_obj.service_state = patch_in.service_state

    if patch_in.notes is not None:
        ref_obj.notes = patch_in.notes.strip()

    ref_obj.updated_at = datetime.now(timezone.utc)

    record_history(
        db=db,
        entity_type="referral",
        entity_id=ref_obj.report_id,
        action="Referral Updated",
        details=f"Status: {ref_obj.status}, Service: {ref_obj.service}",
        actor_officer_id=officer.id,
        report_id=ref_obj.report_id,
    )

    db.commit()
    db.refresh(ref_obj)

    return {
        "referral": serialize_referral_dcpu(ref_obj, db),
        "confirmed": False,
        "disclaimer": PROTOTYPE_DISCLAIMER,
    }


@router.get("/dcpu/dashboard", response_model=DcpuDashboardResponse)
def get_dcpu_dashboard(
    district: str = Query(..., description="District jurisdiction"),
    db: Session = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    """
    Proposed DCPU Referral Dashboard API.
    Provides referral caseload overview and active service linkages.
    """
    district_obj = db.query(District).filter(District.name == district).first()
    if not district_obj:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported district '{district}'.",
        )

    enforce_district_scope(officer, district)

    now = datetime.now(timezone.utc)

    # Compute overview metrics
    new_referrals = (
        db.query(Referral)
        .filter(Referral.district == district, Referral.status == "New")
        .count()
    )
    pending_review = (
        db.query(Referral)
        .filter(Referral.district == district, Referral.status.in_(["Pending review", "Under review"]))
        .count()
    )
    urgent_cases = (
        db.query(Referral)
        .filter(Referral.district == district, Referral.urgency == "Urgent", Referral.status != "Closed")
        .count()
    )
    follow_up_due = (
        db.query(Referral)
        .filter(
            Referral.district == district,
            Referral.status != "Closed",
            (Referral.status == "Follow-up due") | (Referral.follow_up_due <= now),
        )
        .count()
    )

    referrals = (
        db.query(Referral)
        .filter(Referral.district == district)
        .order_by(Referral.id.desc())
        .limit(100)
        .all()
    )

    return {
        "overview": {
            "newReferrals": new_referrals,
            "pendingReview": pending_review,
            "urgentCases": urgent_cases,
            "followUpDue": follow_up_due,
        },
        "referrals": [serialize_referral_dcpu(r, db) for r in referrals],
    }
