from sqlalchemy.orm import Session
from app.models import CaseHistory


def record_history(
    db: Session,
    entity_type: str,
    entity_id: int,
    action: str,
    details: str = "",
    actor_officer_id: int | None = None,
    report_id: int | None = None,
) -> CaseHistory:
    """
    Record an immutable event in the audit trail.
    Strict privacy rule: never store descriptions, child names, phone numbers,
    or sensitive details. Only non-sensitive operational identifiers and action metadata.
    """
    history_entry = CaseHistory(
        entity_type=entity_type,
        entity_id=entity_id,
        report_id=report_id or (entity_id if entity_type in ("report", "case") else None),
        action=action,
        details=details,
        actor_officer_id=actor_officer_id,
    )
    db.add(history_entry)
    db.flush()
    return history_entry
