from app.models import Officer
from app.security import hash_password


def test_assign_case_success(client, demo_dcpu_tvm, dcpu_tvm_headers, demo_field_tvm):
    # Create report in Thiruvananthapuram
    rep = client.post(
        "/api/reports",
        json={
            "district": "Thiruvananthapuram",
            "panchayat": "Varkala",
            "category": "Neglect",
            "description": "Fictional case for assignment verification.",
        },
    ).json()["report"]

    case_id = rep["case_id"]

    # Assign to Rahul Varma (FO-TVM-01)
    payload = {
        "field_officer_id": demo_field_tvm.id,
        "notes": "Verify child safety and family condition.",
    }
    res = client.post(f"/api/cases/{case_id}/assign", json=payload, headers=dcpu_tvm_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["message"] == "Case assigned successfully"
    assert data["case_status"] == "Assigned"
    assert data["assignment"]["assigned_to_id"] == demo_field_tvm.id
    assert data["assignment"]["is_active"] is True


def test_assign_case_district_mismatch(client, demo_dcpu_tvm, dcpu_tvm_headers, db_session):
    # Create a field officer in Kollam
    fo_klm = Officer(
        officer_code="FO-KLM-TEST",
        email="fo.klm.test@karuthal.demo",
        name="Kollam Officer",
        password_hash=hash_password("DemoTestPass123"),
        role="field_officer",
        district="Kollam",
        is_active=True,
    )
    db_session.add(fo_klm)
    db_session.commit()
    db_session.refresh(fo_klm)

    # Create TVM report
    rep = client.post(
        "/api/reports",
        json={
            "district": "Thiruvananthapuram",
            "panchayat": "Varkala",
            "category": "Neglect",
            "description": "TVM case attempting cross-district assignment.",
        },
    ).json()["report"]

    # Attempt assignment to Kollam officer
    res = client.post(
        f"/api/cases/{rep['case_id']}/assign",
        json={"field_officer_id": fo_klm.id},
        headers=dcpu_tvm_headers,
    )
    assert res.status_code == 400
    assert "District mismatch" in res.json()["message"]


def test_field_officer_cannot_assign(client, demo_field_tvm, field_tvm_headers):
    # Field officer attempting to assign -> 403
    res = client.post(
        "/api/cases/KAR-NONEXIST/assign",
        json={"field_officer_id": demo_field_tvm.id},
        headers=field_tvm_headers,
    )
    assert res.status_code == 403
    assert "Action restricted" in res.json()["message"]


def test_reassignment_keeps_history_and_updates_active(client, demo_dcpu_tvm, dcpu_tvm_headers, demo_field_tvm, db_session):
    # Second field officer in TVM
    fo_tvm_2 = Officer(
        officer_code="FO-TVM-02",
        email="fo.tvm2@karuthal.demo",
        name="Second TVM Officer",
        password_hash=hash_password("DemoTestPass123"),
        role="field_officer",
        district="Thiruvananthapuram",
        is_active=True,
    )
    db_session.add(fo_tvm_2)
    db_session.commit()
    db_session.refresh(fo_tvm_2)

    rep = client.post(
        "/api/reports",
        json={
            "district": "Thiruvananthapuram",
            "panchayat": "Varkala",
            "category": "Neglect",
            "description": "Reassignment case flow.",
        },
    ).json()["report"]
    case_id = rep["case_id"]

    # First assignment to demo_field_tvm
    client.post(f"/api/cases/{case_id}/assign", json={"field_officer_id": demo_field_tvm.id}, headers=dcpu_tvm_headers)

    # Second assignment to fo_tvm_2
    res2 = client.post(f"/api/cases/{case_id}/assign", json={"field_officer_id": fo_tvm_2.id}, headers=dcpu_tvm_headers)
    assert res2.status_code == 200

    # Check assignments list
    list_res = client.get(f"/api/assignments?case_id={case_id}", headers=dcpu_tvm_headers)
    assert list_res.status_code == 200
    assignments = list_res.json()["assignments"]
    assert len(assignments) == 2
    # Only 1 is active
    active_assignments = [a for a in assignments if a["is_active"]]
    assert len(active_assignments) == 1
    assert active_assignments[0]["assigned_to_id"] == fo_tvm_2.id
