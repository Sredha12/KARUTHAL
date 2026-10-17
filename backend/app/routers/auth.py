from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_officer
from app.models import Officer
from app.schemas import LoginRequest, LoginResponse, OfficerProfile
from app.security import (
    check_login_rate_limit,
    clear_login_failures,
    create_access_token,
    record_login_failure,
    verify_password,
)

router = APIRouter(prefix="/api", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate an authorized officer via email or officer_code.
    Returns PyJWT token, officer name, and district.
    Subject to in-memory rate limiting (5 failed attempts per 15 min).
    """
    login_id = request.login.strip()

    # Check login throttle
    check_login_rate_limit(login_id)

    # Lookup officer by email or officer_code
    officer = (
        db.query(Officer)
        .filter(
            (Officer.email.ilike(login_id)) | (Officer.officer_code.ilike(login_id))
        )
        .first()
    )

    if not officer or not officer.is_active or not verify_password(request.password, officer.password_hash):
        record_login_failure(login_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please verify your officer code/email and password.",
        )

    # Clear prior failed attempts
    clear_login_failures(login_id)

    token = create_access_token({
        "id": officer.id,
        "officer_code": officer.officer_code,
        "email": officer.email,
        "name": officer.name,
        "role": officer.role,
        "district": officer.district,
    })

    return {
        "token": token,
        "name": officer.name,
        "district": officer.district,
    }


@router.get("/auth/me", response_model=OfficerProfile)
def get_current_officer_profile(officer: Officer = Depends(get_current_officer)):
    """Retrieve profile and assigned jurisdiction of authenticated officer."""
    return officer
