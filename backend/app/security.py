from datetime import datetime, timedelta, timezone
from collections import defaultdict
import bcrypt
import jwt
from fastapi import HTTPException, status

from app.config import settings

ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 8

# In-memory login rate limiter (Prototype Limitation)
# Maps normalized login string -> list of failure timestamps
FAILED_LOGIN_ATTEMPTS: dict[str, list[datetime]] = defaultdict(list)
MAX_LOGIN_FAILURES = 5
LOCKOUT_WINDOW_MINUTES = 15


def hash_password(password: str) -> str:
    """Hash a plain text password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(officer_data: dict) -> str:
    """Create a PyJWT access token with an 8-hour expiry."""
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": str(officer_data["id"]),
        "officer_code": officer_data["officer_code"],
        "email": officer_data["email"],
        "name": officer_data["name"],
        "role": officer_data["role"],
        "district": officer_data["district"],
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)
    return token


def decode_access_token(token: str) -> dict:
    """Decode and validate a PyJWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token has expired. Please log in again.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )


def check_login_rate_limit(login_identifier: str) -> None:
    """Check if the login identifier has exceeded allowed failed attempts."""
    key = login_identifier.strip().lower()
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=LOCKOUT_WINDOW_MINUTES)

    # Filter out timestamps older than the lockout window
    recent_failures = [t for t in FAILED_LOGIN_ATTEMPTS[key] if t > cutoff]
    FAILED_LOGIN_ATTEMPTS[key] = recent_failures

    if len(recent_failures) >= MAX_LOGIN_FAILURES:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Account temporarily locked for 15 minutes (prototype rate limitation).",
        )


def record_login_failure(login_identifier: str) -> None:
    """Record a failed login attempt for the given identifier."""
    key = login_identifier.strip().lower()
    FAILED_LOGIN_ATTEMPTS[key].append(datetime.now(timezone.utc))


def clear_login_failures(login_identifier: str) -> None:
    """Reset the failure counter upon successful authentication."""
    key = login_identifier.strip().lower()
    if key in FAILED_LOGIN_ATTEMPTS:
        del FAILED_LOGIN_ATTEMPTS[key]
