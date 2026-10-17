from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Report

# Kerala Geographical Bounding Box (Approximate statutory envelope)
KERALA_MIN_LAT = 8.10
KERALA_MAX_LAT = 12.90
KERALA_MIN_LNG = 74.80
KERALA_MAX_LNG = 77.50


def validate_kerala_coordinates(lat: float | None, lng: float | None) -> None:
    """
    Validate that geographic coordinates fall strictly within the Kerala bounding box.
    Rejects out-of-bounds coordinates with HTTP 422.
    """
    if lat is None and lng is None:
        return

    if lat is None or lng is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Both latitude and longitude must be provided together.",
        )

    if not (KERALA_MIN_LAT <= lat <= KERALA_MAX_LAT and KERALA_MIN_LNG <= lng <= KERALA_MAX_LNG):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Coordinates ({lat}, {lng}) are outside Kerala boundaries "
                f"(Lat {KERALA_MIN_LAT}-{KERALA_MAX_LAT}, Lng {KERALA_MIN_LNG}-{KERALA_MAX_LNG})."
            ),
        )


def apply_location_retention_policy(db: Session, retention_days: int | None = None) -> int:
    """
    Nulls stored coordinates for reports exceeding the statutory retention period.
    Default retention period is governed by settings.LOCATION_RETENTION_DAYS (90 days).
    """
    days = retention_days if retention_days is not None else settings.LOCATION_RETENTION_DAYS
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    reports_to_clean = (
        db.query(Report)
        .filter(
            Report.created_at <= cutoff,
            (Report.approx_lat.is_not(None)) | (Report.approx_lng.is_not(None)),
        )
        .all()
    )

    cleaned_count = len(reports_to_clean)
    for r in reports_to_clean:
        r.approx_lat = None
        r.approx_lng = None

    if cleaned_count > 0:
        db.commit()

    return cleaned_count
