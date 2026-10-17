def test_emergency_call_lifecycle_and_conflict(
    client, demo_dcpu_tvm, dcpu_tvm_headers, demo_dcpu_kollam, dcpu_klm_headers
):
    # 1. Create a case
    rep = client.post(
        "/api/reports",
        json={
            "district": "Thiruvananthapuram",
            "panchayat": "Varkala",
            "category": "Neglect",
            "description": "Fictional case for emergency linking.",
        },
    ).json()["report"]
    case_id = rep["case_id"]

    # 2. Post emergency call linked to case
    call_payload = {
        "category": "Immediate child protection alert",
        "description": "Child observed unattended in high risk setting.",
        "district": "Thiruvananthapuram",
        "related_case_id": case_id,
    }
    create_res = client.post("/api/emergency", json=call_payload, headers=dcpu_tvm_headers)
    assert create_res.status_code == 201
    data = create_res.json()
    assert "disclaimer" in data
    call = data["call"]
    assert call["call_ref"].startswith("CALL-")
    assert call["status"] == "Active"
    call_id = call["id"]

    # 3. Patch to Acknowledged
    ack_res = client.patch(
        f"/api/emergency/{call_id}",
        json={"status": "Acknowledged", "notes": "Local team informed."},
        headers=dcpu_tvm_headers,
    )
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "Acknowledged"

    # 4. Out of scope officer cannot patch emergency
    forbidden_res = client.patch(
        f"/api/emergency/{call_id}",
        json={"status": "Resolved"},
        headers=dcpu_klm_headers,
    )
    assert forbidden_res.status_code == 403
    assert "message" in forbidden_res.json()

    # 5. Patch to Resolved
    res_res = client.patch(
        f"/api/emergency/{call_id}",
        json={"status": "Resolved", "notes": "Situation stabilized."},
        headers=dcpu_tvm_headers,
    )
    assert res_res.status_code == 200
    assert res_res.json()["status"] == "Resolved"

    # 6. Attempting to update an already Resolved call -> 409 Conflict
    conflict_res = client.patch(
        f"/api/emergency/{call_id}",
        json={"status": "Acknowledged"},
        headers=dcpu_tvm_headers,
    )
    assert conflict_res.status_code == 409
    assert "message" in conflict_res.json()
    assert "already Resolved" in conflict_res.json()["message"]


def test_case_history_audit_trail(client, demo_dcpu_tvm, dcpu_tvm_headers, demo_field_tvm, field_tvm_headers):
    # 1. Report Submitted
    rep = client.post(
        "/api/reports",
        json={
            "district": "Thiruvananthapuram",
            "panchayat": "Varkala",
            "category": "Neglect",
            "description": "Sensitive description that must never appear in history details.",
        },
    ).json()["report"]
    case_id = rep["case_id"]

    # 2. Case Assigned
    client.post(
        f"/api/cases/{case_id}/assign",
        json={"field_officer_id": demo_field_tvm.id},
        headers=dcpu_tvm_headers,
    )

    # 3. Field Visit Recorded
    client.post(
        f"/api/cases/{case_id}/field-visits",
        json={
            "visit_at": "2026-10-17T10:00:00Z",
            "outcome": "Needs support services",
            "notes": "Assessment completed.",
        },
        headers=field_tvm_headers,
    )

    # 4. Referral Created
    client.post(
        f"/api/cases/{case_id}/referrals",
        json={"service": "Child Guidance Clinic", "urgency": "Standard"},
        headers=dcpu_tvm_headers,
    )

    # 5. Emergency Alert Linked
    client.post(
        "/api/emergency",
        json={
            "category": "Alert",
            "district": "Thiruvananthapuram",
            "related_case_id": case_id,
        },
        headers=dcpu_tvm_headers,
    )

    # 6. Retrieve History
    hist_res = client.get(f"/api/cases/{case_id}/history", headers=dcpu_tvm_headers)
    assert hist_res.status_code == 200
    data = hist_res.json()
    assert data["case_id"] == case_id
    assert data["count"] >= 5

    actions = [h["action"] for h in data["history"]]
    assert "Report Submitted" in actions
    assert "Case Assigned" in actions
    assert "Field Visit Recorded" in actions
    assert "Referral Created" in actions
    assert "Emergency Alert Linked" in actions

    # Strict Privacy check: raw description text must NOT be in any history details
    for h in data["history"]:
        assert "Sensitive description" not in h["details"]
