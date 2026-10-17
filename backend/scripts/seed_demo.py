"""
Idempotent Demo Database Seeder for Karuthal Prototype.
Populates standard Kerala locations, fictional demo officer accounts,
sample child-protection reports in diverse workflow statuses, emergency calls,
referrals, field visits, and audit history.

NOTE: All data seeded by this script is strictly FICTIONAL / DEMO data.
No real children, individuals, addresses, or actual child-protection records are used.
"""

import os
import sys
from datetime import datetime, timedelta, timezone

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv

load_dotenv()

from app.database import Base, SessionLocal, engine
from app.init_db import init_locations
from app.models import (
    Assignment,
    CaseHistory,
    District,
    EmergencyCall,
    FieldVisit,
    Officer,
    Panchayat,
    Referral,
    Report,
)
from app.security import hash_password


def seed_demo_data():
    raw_password = os.getenv("DEMO_OFFICER_PASSWORD")
    if not raw_password or len(raw_password) < 12:
        print(
            "ERROR: DEMO_OFFICER_PASSWORD environment variable is missing or shorter than 12 characters.",
            file=sys.stderr,
        )
        sys.exit(1)

    print("--- Initializing Karuthal Database Tables ---")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("--- Seeding Kerala Districts and Sample Panchayats ---")
        init_locations(db)

        tvm_dist = db.query(District).filter(District.name == "Thiruvananthapuram").first()
        klm_dist = db.query(District).filter(District.name == "Kollam").first()
        ekm_dist = db.query(District).filter(District.name == "Ernakulam").first()
        kkd_dist = db.query(District).filter(District.name == "Kozhikode").first()

        varkala_panch = db.query(Panchayat).filter(Panchayat.name == "Varkala").first()
        chavara_panch = db.query(Panchayat).filter(Panchayat.name == "Chavara").first()
        aluva_panch = db.query(Panchayat).filter(Panchayat.name == "Aluva").first()

        hashed_pwd = hash_password(raw_password)

        print("--- Seeding Demo Officer Accounts ---")
        demo_officers = [
            # Thiruvananthapuram
            {
                "officer_code": "DCPU-TVM-01",
                "email": "dcpu.tvm@karuthal.demo",
                "name": "Anjali Nair",
                "role": "dcpu_officer",
                "district": "Thiruvananthapuram",
            },
            {
                "officer_code": "FO-TVM-01",
                "email": "fo.tvm@karuthal.demo",
                "name": "Rahul Varma",
                "role": "field_officer",
                "district": "Thiruvananthapuram",
            },
            # Kollam
            {
                "officer_code": "DCPU-KLM-01",
                "email": "dcpu.klm@karuthal.demo",
                "name": "Suresh Kumar",
                "role": "dcpu_officer",
                "district": "Kollam",
            },
            {
                "officer_code": "FO-KLM-01",
                "email": "fo.klm@karuthal.demo",
                "name": "Deepa Menon",
                "role": "field_officer",
                "district": "Kollam",
            },
            # Ernakulam
            {
                "officer_code": "DCPU-EKM-01",
                "email": "dcpu.ekm@karuthal.demo",
                "name": "Mathew George",
                "role": "dcpu_officer",
                "district": "Ernakulam",
            },
            {
                "officer_code": "FO-EKM-01",
                "email": "fo.ekm@karuthal.demo",
                "name": "Pooja Pillai",
                "role": "field_officer",
                "district": "Ernakulam",
            },
            # Kozhikode
            {
                "officer_code": "DCPU-KKD-01",
                "email": "dcpu.kkd@karuthal.demo",
                "name": "Faizal Rahman",
                "role": "dcpu_officer",
                "district": "Kozhikode",
            },
            {
                "officer_code": "FO-KKD-01",
                "email": "fo.kkd@karuthal.demo",
                "name": "Aiswarya Rajan",
                "role": "field_officer",
                "district": "Kozhikode",
            },
            # State Admin
            {
                "officer_code": "ADMIN-01",
                "email": "admin@karuthal.demo",
                "name": "State Administrator",
                "role": "admin",
                "district": "Thiruvananthapuram",
            },
        ]

        officer_map = {}
        for off_data in demo_officers:
            existing = db.query(Officer).filter(Officer.officer_code == off_data["officer_code"]).first()
            if not existing:
                off_obj = Officer(
                    officer_code=off_data["officer_code"],
                    email=off_data["email"],
                    name=off_data["name"],
                    password_hash=hashed_pwd,
                    role=off_data["role"],
                    district=off_data["district"],
                    is_active=True,
                )
                db.add(off_obj)
                db.flush()
                officer_map[off_data["officer_code"]] = off_obj
            else:
                existing.password_hash = hashed_pwd
                existing.name = off_data["name"]
                officer_map[off_data["officer_code"]] = existing

        dcpu_tvm = officer_map["DCPU-TVM-01"]
        fo_tvm = officer_map["FO-TVM-01"]

        print("--- Seeding Demo Reports & Cases ---")
        now = datetime.now(timezone.utc)
        sample_reports = [
            {
                "report_id": "KAR-10000001",
                "district": "Thiruvananthapuram",
                "district_id": tvm_dist.id if tvm_dist else None,
                "panchayat": "Varkala",
                "panchayat_id": varkala_panch.id if varkala_panch else None,
                "category": "Neglect",
                "description": "Fictional case: child reported unattended during daytime hours near marketplace.",
                "status": "Submitted",
                "is_urgent": False,
                "created_at": now - timedelta(days=5),
            },
            {
                "report_id": "KAR-10000002",
                "district": "Thiruvananthapuram",
                "district_id": tvm_dist.id if tvm_dist else None,
                "panchayat": "Varkala",
                "panchayat_id": varkala_panch.id if varkala_panch else None,
                "category": "Child labour",
                "description": "Fictional case: minor observed working in commercial workshop during school hours.",
                "status": "Assigned",
                "is_urgent": True,
                "created_at": now - timedelta(days=4),
            },
            {
                "report_id": "KAR-10000003",
                "district": "Thiruvananthapuram",
                "district_id": tvm_dist.id if tvm_dist else None,
                "panchayat": "Nedumangad",
                "category": "Physical abuse",
                "description": "Fictional case: repeated loud disturbances and distress reported by neighbours.",
                "status": "Visit Recorded",
                "is_urgent": True,
                "created_at": now - timedelta(days=3),
            },
            {
                "report_id": "KAR-10000004",
                "district": "Thiruvananthapuram",
                "district_id": tvm_dist.id if tvm_dist else None,
                "panchayat": "Kattakada",
                "category": "Emotional abuse",
                "description": "Fictional case: child facing severe psychological distress in residential home.",
                "status": "Referred",
                "is_urgent": False,
                "created_at": now - timedelta(days=2),
            },
            {
                "report_id": "KAR-10000005",
                "district": "Thiruvananthapuram",
                "district_id": tvm_dist.id if tvm_dist else None,
                "panchayat": "Varkala",
                "panchayat_id": varkala_panch.id if varkala_panch else None,
                "category": "Neglect",
                "description": "Fictional case: family support provided and schooling verified by welfare officer.",
                "status": "Solved",
                "is_urgent": False,
                "created_at": now - timedelta(days=10),
                "solved_at": now - timedelta(days=1),
                "solved_by": dcpu_tvm.id,
            },
            {
                "report_id": "KAR-20000001",
                "district": "Kollam",
                "district_id": klm_dist.id if klm_dist else None,
                "panchayat": "Chavara",
                "panchayat_id": chavara_panch.id if chavara_panch else None,
                "category": "Child marriage",
                "description": "Fictional case: early marriage concern reported anonymously in community area.",
                "status": "Under Review",
                "is_urgent": True,
                "created_at": now - timedelta(days=1),
            },
        ]

        report_objects = {}
        for rep in sample_reports:
            existing = db.query(Report).filter(Report.report_id == rep["report_id"]).first()
            if not existing:
                r_obj = Report(
                    report_id=rep["report_id"],
                    district=rep["district"],
                    district_id=rep.get("district_id"),
                    panchayat=rep["panchayat"],
                    panchayat_id=rep.get("panchayat_id"),
                    category=rep["category"],
                    description=rep["description"],
                    status=rep["status"],
                    is_urgent=rep["is_urgent"],
                    created_at=rep["created_at"],
                    updated_at=rep["created_at"],
                    solved_at=rep.get("solved_at"),
                    solved_by=rep.get("solved_by"),
                )
                db.add(r_obj)
                db.flush()
                report_objects[rep["report_id"]] = r_obj

                # Initial history
                db.add(
                    CaseHistory(
                        entity_type="report",
                        entity_id=r_obj.id,
                        report_id=r_obj.id,
                        action="Report Submitted",
                        details="Initial report received via community portal",
                        created_at=rep["created_at"],
                    )
                )
            else:
                report_objects[rep["report_id"]] = existing

        # Assign KAR-10000002 to FO-TVM-01
        rep_assigned = report_objects.get("KAR-10000002")
        if rep_assigned:
            existing_ass = db.query(Assignment).filter(Assignment.report_id == rep_assigned.id).first()
            if not existing_ass:
                ass_obj = Assignment(
                    report_id=rep_assigned.id,
                    assigned_to_id=fo_tvm.id,
                    assigned_by_id=dcpu_tvm.id,
                    notes="Investigate workplace premises during working hours.",
                    is_active=True,
                    created_at=now - timedelta(days=3),
                )
                db.add(ass_obj)
                db.add(
                    CaseHistory(
                        entity_type="case",
                        entity_id=rep_assigned.id,
                        report_id=rep_assigned.id,
                        action="Case Assigned",
                        details=f"Assigned to field officer {fo_tvm.officer_code}",
                        actor_officer_id=dcpu_tvm.id,
                        created_at=now - timedelta(days=3),
                    )
                )

        # Field visit for KAR-10000003
        rep_visit = report_objects.get("KAR-10000003")
        if rep_visit:
            existing_visit = db.query(FieldVisit).filter(FieldVisit.report_id == rep_visit.id).first()
            if not existing_visit:
                fv_obj = FieldVisit(
                    report_id=rep_visit.id,
                    field_officer_id=fo_tvm.id,
                    visit_at=now - timedelta(days=2),
                    outcome="Needs support services",
                    notes="Conducted assessment. Caregivers agreed to counseling and support sessions.",
                    created_at=now - timedelta(days=2),
                )
                db.add(fv_obj)
                db.add(
                    CaseHistory(
                        entity_type="case",
                        entity_id=rep_visit.id,
                        report_id=rep_visit.id,
                        action="Field Visit Recorded",
                        details="Outcome: Needs support services",
                        actor_officer_id=fo_tvm.id,
                        created_at=now - timedelta(days=2),
                    )
                )

        # Referral for KAR-10000004
        rep_referral = report_objects.get("KAR-10000004")
        if rep_referral:
            existing_ref = db.query(Referral).filter(Referral.report_id == rep_referral.id).first()
            if not existing_ref:
                ref_obj = Referral(
                    report_id=rep_referral.id,
                    district="Thiruvananthapuram",
                    concern_category="Emotional abuse",
                    urgency="Standard",
                    status="Pending review",
                    next_action="Schedule preliminary consultation session",
                    follow_up_due=now + timedelta(days=7),
                    service="Child Guidance Clinic",
                    service_state="Referred",
                    notes="Fictional referral initiated for adolescent counseling.",
                    created_by_id=dcpu_tvm.id,
                    created_at=now - timedelta(days=1),
                )
                db.add(ref_obj)
                db.add(
                    CaseHistory(
                        entity_type="referral",
                        entity_id=rep_referral.id,
                        report_id=rep_referral.id,
                        action="Referral Created",
                        details="Referred to Child Guidance Clinic",
                        actor_officer_id=dcpu_tvm.id,
                        created_at=now - timedelta(days=1),
                    )
                )

        print("--- Seeding Demo Emergency Calls ---")
        sample_calls = [
            {
                "call_ref": "CALL-10000001",
                "district": "Thiruvananthapuram",
                "category": "Immediate child protection alert",
                "description": "Fictional alert: distressed child reported in bus station area.",
                "status": "Active",
                "notes": "Desk dispatched notification to local standby worker.",
                "created_at": now - timedelta(hours=3),
            },
            {
                "call_ref": "CALL-10000002",
                "district": "Thiruvananthapuram",
                "category": "Runaway assistance",
                "description": "Fictional alert: unaccompanied teenager seeking shelter.",
                "status": "Acknowledged",
                "notes": "Officer acknowledged and coordinated safe temporary accommodation.",
                "created_at": now - timedelta(hours=8),
            },
            {
                "call_ref": "CALL-10000003",
                "district": "Thiruvananthapuram",
                "category": "Medical assistance requirement",
                "description": "Fictional alert: child needing urgent clinic checkup.",
                "status": "Resolved",
                "notes": "Medical examination completed at district hospital.",
                "created_at": now - timedelta(days=2),
            },
        ]

        for call in sample_calls:
            existing_call = db.query(EmergencyCall).filter(EmergencyCall.call_ref == call["call_ref"]).first()
            if not existing_call:
                c_obj = EmergencyCall(
                    call_ref=call["call_ref"],
                    district=call["district"],
                    category=call["category"],
                    description=call["description"],
                    status=call["status"],
                    notes=call["notes"],
                    created_at=call["created_at"],
                    updated_at=call["created_at"],
                    recorded_by=dcpu_tvm.id,
                )
                db.add(c_obj)

        db.commit()
        print("--- Demo Seeding Completed Successfully! ---")
        print("Officer accounts seeded for TVM, KLM, EKM, KKD + Admin.")
    except Exception as e:
        db.rollback()
        print(f"ERROR: Seeding failed with error: {e}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
