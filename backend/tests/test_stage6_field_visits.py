from datetime import datetime, timezone


def test_field_visit_lifecycle(client, demo_dcpu_tvm, dcpu_tvm_headers, demo_field_tvm, field_tvm_headers):
    # 1. Create report in TVM
    rep = client.post(
        "/api/reports",
        json={
            "district": "Thiruvananthapuram",
            "panchayat": "Varkala",
            "category": "Neglect",
            "description": "Fictional field visit verification case.",
        },
    ).json()["report"]
    case_id = rep["case_id"]

    # 2. Before assignment, field officer cannot record visit (403)
    res_unassigned = client.post(
        f"/api/cases/{case_id}/field-visits",
        json={
            "visit_at": datetime.now(timezone.utc).isoformat(),
            "outcome": "Safe with family",
            "notes": "Preliminary check.",
        },
        headers=field_tvm_headers,
    )
    assert res_unassigned.status_code == 403
    assert "not actively assigned" in res_unassigned.json()["message"]

    # 3. DCPU officer assigns case to demo_field_tvm
    client.post(
        f"/api/cases/{case_id}/assign",
        json={"field_officer_id": demo_field_tvm.id},
        headers=dcpu_tvm_headers,
    )

    # 4. Now assigned field officer can record visit (201)
    res_success = client.post(
        f"/api/cases/{case_id}/field-visits",
        json={
            "visit_at": datetime.now(timezone.utc).isoformat(),
            "outcome": "Needs support services",
            "notes": "Home visit conducted. Support services recommended.",
        },
        headers=field_tvm_headers,
    )
    assert res_success.status_code == 201
    visit_data = res_success.json()
    assert visit_data["message"] == "Field visit recorded successfully"
    assert visit_data["case_status"] == "Visit Recorded"
    assert visit_data["field_visit"]["outcome"] == "Needs support services"

    # 5. Case status is now 'Visit Recorded'
    case_detail = client.get(f"/api/cases/{case_id}", headers=dcpu_tvm_headers).json()
    assert case_detail["status"] == "Visit Recorded"

    # 6. Retrieve field visits list
    visits_list = client.get(f"/api/cases/{case_id}/field-visits", headers=dcpu_tvm_headers).json()
    assert visits_list["count"] == 1
    assert visits_list["field_visits"][0]["outcome"] == "Needs support services"


def test_field_visit_validation(client, demo_dcpu_tvm, dcpu_tvm_headers, demo_field_tvm, field_tvm_headers):
    rep = client.post(
        "/api/reports",
        json={
            "district": "Thiruvananthapuram",
            "panchayat": "Varkala",
            "category": "Neglect",
            "description": "Fictional case for validation testing.",
        },
    ).json()["report"]
    case_id = rep["case_id"]

    client.post(
        f"/api/cases/{case_id}/assign",
        json={"field_officer_id": demo_field_tvm.id},
        headers=dcpu_tvm_headers,
    )

    # Invalid outcome -> 422
    res_bad_outcome = client.post(
        f"/api/cases/{case_id}/field-visits",
        json={
            "visit_at": datetime.now(timezone.utc).isoformat(),
            "outcome": "Nonexistent Outcome",
            "notes": "Notes here.",
        },
        headers=field_tvm_headers,
    )
    assert res_bad_outcome.status_code == 422
    assert "Invalid visit outcome" in res_bad_outcome.json()["message"]
