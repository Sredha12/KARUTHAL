from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Assignment, Officer, Report
from app.security import decode_access_token

security_bearer = HTTPBearer(auto_error=False)


def get_current_officer(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_bearer),
    db: Session = Depends(get_db),
) -> Officer:
    """
    Authenticate the current officer via Bearer token.
    Returns the Officer model if valid, or raises 401 Unauthorized.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
        )

    payload = decode_access_token(credentials.credentials)
    officer_id_str = payload.get("sub")
    if not officer_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token payload.",
        )

    try:
        officer_id = int(officer_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed officer identity in token.",
        )

    officer = db.query(Officer).filter(Officer.id == officer_id).first()
    if not officer or not officer.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Officer account not found or has been deactivated.",
        )

    return officer


def get_optional_officer(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_bearer),
    db: Session = Depends(get_db),
) -> Officer | None:
    """Optionally authenticate officer without rejecting unauthenticated requests."""
    if not credentials or not credentials.credentials:
        return None
    try:
        return get_current_officer(credentials=credentials, db=db)
    except HTTPException:
        return None


def enforce_district_scope(officer: Officer, target_district: str) -> None:
    """
    Verify that an officer has permission to view or mutate records in target_district.
    Admin can access any district.
    When ENFORCE_DISTRICT_SCOPE is true, other officers can only access their own district.
    """
    if not settings.ENFORCE_DISTRICT_SCOPE or officer.role == "admin":
        return

    if officer.district != target_district:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Case or resource is outside your assigned district scope.",
        )


def verify_case_scope(report: Report, officer: Officer, db: Session) -> None:
    """
    Verify that an officer has permission to access a specific case:
    1. District boundary enforcement (unless admin)
    2. Field officers can only access cases actively assigned to them
    """
    enforce_district_scope(officer, report.district)

    if officer.role == "field_officer":
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
                detail="Access restricted. Field officers may only access cases assigned to them.",
            )


def require_roles(*allowed_roles: str):
    """Dependency factory ensuring current officer possesses at least one of the specified roles."""
    def role_checker(officer: Officer = Depends(get_current_officer)) -> Officer:
        if officer.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action restricted. Required role(s): {', '.join(allowed_roles)}.",
            )
        return officer
    return role_checker
