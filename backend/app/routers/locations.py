from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import District, Panchayat
from app.schemas import DistrictRead, PanchayatRead

router = APIRouter(prefix="/api/locations", tags=["Locations"])


@router.get("/districts", response_model=list[DistrictRead])
def get_districts(db: Session = Depends(get_db)):
    """Return all 14 official revenue districts of Kerala."""
    districts = db.query(District).order_by(District.name.asc()).all()
    return districts


@router.get("/panchayats", response_model=list[PanchayatRead])
def get_panchayats(
    district_id: int | None = Query(default=None, description="Filter panchayats by district ID"),
    db: Session = Depends(get_db),
):
    """
    Return administrative panchayats.
    Panchayats returned are labelled sample/fictional records for demonstration.
    """
    query = db.query(Panchayat)
    if district_id is not None:
        district_exists = db.query(District).filter(District.id == district_id).first()
        if not district_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"District with ID {district_id} does not exist.",
            )
        query = query.filter(Panchayat.district_id == district_id)

    return query.order_by(Panchayat.name.asc()).all()
