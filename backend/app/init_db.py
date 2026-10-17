from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from app.models import District, Panchayat
from app.seed_data import KERALA_DISTRICTS, SAMPLE_PANCHAYATS_BY_DISTRICT


def ensure_schema_migrations(engine: Engine) -> None:
    """
    Ensure newly added columns exist in existing tables (additive, non-destructive migrations).
    Safely adds Stage 11 and Stage 12 columns to existing tables in development SQLite or Postgres.
    """
    with engine.connect() as conn:
        dialect_name = engine.dialect.name
        if dialect_name == "sqlite":
            columns_res = conn.execute(text("PRAGMA table_info(reports)"))
            existing_cols = {row[1] for row in columns_res.fetchall()}

            new_columns = [
                ("location_text", "VARCHAR(200)"),
                ("ward", "VARCHAR(50)"),
                ("approx_lat", "FLOAT"),
                ("approx_lng", "FLOAT"),
                ("location_consent", "BOOLEAN DEFAULT 0"),
                ("location_source", "VARCHAR(20) DEFAULT 'typed'"),
                ("routed_district", "VARCHAR(100)"),
                ("reporter_token_hash", "VARCHAR(255)"),
            ]
            for col_name, col_type in new_columns:
                if col_name not in existing_cols:
                    conn.execute(text(f"ALTER TABLE reports ADD COLUMN {col_name} {col_type}"))
            conn.commit()


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
