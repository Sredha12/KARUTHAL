from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import enforce_district_scope, require_roles
from app.models import Assignment, CaseHistory, EmergencyCall, FieldVisit, Officer, Referral, Report
from app.routers.cases import find_report_by_case_id
from app.schemas import AiSummaryResponse, RelatedCaseHint, TimelineEvent
from app.services.history_service import record_history

router = APIRouter(prefix="/api/cases", tags=["AI Case Assistance"])

AI_DISCLAIMER = (
    "AI-assisted prototype summary for authorized human decision-making only. "
    "All reported information consists of unverified allegations. This system does NOT "
    "determine abuse, guilt, or risk, does NOT contact external agencies, and CANNOT "
    "automatically close, reject, or escalate cases."
)


@router.post("/{case_id}/ai-summary", response_model=AiSummaryResponse)
def generate_ai_summary(
    case_id: str,
    db: Session = Depends(get_db),
    officer: Officer = Depends(require_roles("dcpu_officer", "admin")),
):
    """
    Generate a deterministic, rule-based case summary to support authorized human decision-making.
    Strict safety and privacy invariants:
    - Zero external API calls: completely local, self-contained, deterministic logic.
    - Never declares abuse occurred, never assigns risk scores, guilt, or liability.
    - Never modifies case status or automates decisions.
    - Labels all input as 'reported, unverified'.
    - Aggregates related hints using strictly count metrics, never leaking content or identities.
    """
    report = find_report_by_case_id(case_id, db)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' not found.",
        )

    enforce_district_scope(officer, report.district)

    # 1. Compile deterministic structured summary
    structured_summary = (
        f"[Reported, Unverified Intake] A child-protection concern regarding '{report.category}' "
        f"was registered under reference {report.report_id} in {report.district} ({report.panchayat}). "
        f"Current operational status is '{report.status}'. "
        f"Reported description indicates concerns requiring authorized officer investigation. "
        f"This document is a human-support aid and does not constitute a legal or factual finding."
    )

    # 2. Compile missing information checklist
    missing_info = [
        "Formal verification of child identity and age documentation",
        "Direct assessment interview conducted by authorized child-protection officer",
        "Independent collateral statements from caregivers or community witnesses",
        "School attendance and educational continuity verification",
    ]
    if report.category in ("Physical abuse", "Sexual abuse"):
        missing_info.append("Authorized medical evaluation report from government medical officer")
    if not report.panchayat_id:
        missing_info.append("Precise administrative jurisdiction and local body verification")

    # 3. Compile tentative operational timeline
    timeline_events = []
    if report.created_at:
        timeline_events.append(
            TimelineEvent(
                timestamp=report.created_at.strftime("%Y-%m-%d %H:%M UTC"),
                event="Initial concern reported (unverified intake)",
            )
        )

    # Add assignments
    assignments = (
        db.query(Assignment)
        .filter(Assignment.report_id == report.id)
        .order_by(Assignment.created_at.asc())
        .all()
    )
    for a in assignments:
        officer_label = a.assigned_to.officer_code if a.assigned_to else "Field Officer"
        timeline_events.append(
            TimelineEvent(
                timestamp=a.created_at.strftime("%Y-%m-%d %H:%M UTC") if a.created_at else "",
                event=f"Case assigned to {officer_label} for field assessment",
            )
        )

    # Add field visits
    visits = (
        db.query(FieldVisit)
        .filter(FieldVisit.report_id == report.id)
        .order_by(FieldVisit.created_at.asc())
        .all()
    )
    for v in visits:
        timeline_events.append(
            TimelineEvent(
                timestamp=v.created_at.strftime("%Y-%m-%d %H:%M UTC") if v.created_at else "",
                event=f"Field visit recorded (Reported outcome: {v.outcome})",
            )
        )

    # Add referrals
    referrals = (
        db.query(Referral)
        .filter(Referral.report_id == report.id)
        .order_by(Referral.created_at.asc())
        .all()
    )
    for r in referrals:
        timeline_events.append(
            TimelineEvent(
                timestamp=r.created_at.strftime("%Y-%m-%d %H:%M UTC") if r.created_at else "",
                event=f"Referral initiated for {r.service} ({r.service_state})",
            )
        )

    # 4. Compile related case hints (AGGREGATE COUNTS ONLY, NO CASE CONTENT OR IDENTITY)
    similar_cases_count = (
        db.query(Report)
        .filter(
            Report.district == report.district,
            Report.category == report.category,
            Report.id != report.id,
        )
        .count()
    )

    related_hints = [
        RelatedCaseHint(
            category=report.category,
            district=report.district,
            similar_cases_count=similar_cases_count,
            note=(
                "Statistical count of historical reports in the same district and concern category. "
                "No narrative content, case identifiers, or identities are linked or exposed."
            ),
        )
    ]

    # 5. Record history of AI summary generation
    record_history(
        db=db,
        entity_type="case",
        entity_id=report.id,
        action="AI Summary Generated",
        details="Rule-based decision support summary created for authorized officer review",
        actor_officer_id=officer.id,
        report_id=report.id,
    )
    db.commit()

    return AiSummaryResponse(
        ai_generated=True,
        verified=False,
        human_review_required=True,
        disclaimer=AI_DISCLAIMER,
        case_id=report.report_id,
        structured_summary=structured_summary,
        missing_information=missing_info,
        tentative_timeline=timeline_events,
        related_case_hints=related_hints,
    )
