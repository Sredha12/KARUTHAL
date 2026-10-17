from sqlalchemy.orm import Session
from app.models import District, Panchayat
from app.seed_data import KERALA_DISTRICTS, SAMPLE_PANCHAYATS_BY_DISTRICT


def init_locations(db: Session) -> None:
    """
    Ensure the 14 official Kerala districts and fictional/sample panchayats exist.
    Idempotent: does not duplicate if already present.
    """
    existing_districts = {d.name: d for d in db.query(District).all()}

    for dist_info in KERALA_DISTRICTS:
        name = dist_info["name"]
        code = dist_info["code"]
        if name not in existing_districts:
            district_obj = District(name=name, code=code)
            db.add(district_obj)
            db.flush()
            existing_districts[name] = district_obj
        else:
            district_obj = existing_districts[name]

        # Seed sample panchayats for this district
        existing_panchayats = {
            p.name for p in db.query(Panchayat).filter(Panchayat.district_id == district_obj.id).all()
        }
        for panch_name in SAMPLE_PANCHAYATS_BY_DISTRICT.get(name, []):
            if panch_name not in existing_panchayats:
                panch_obj = Panchayat(
                    district_id=district_obj.id,
                    name=panch_name,
                    is_sample=True,
                )
                db.add(panch_obj)

    db.commit()
