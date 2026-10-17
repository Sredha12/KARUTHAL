def test_ai_summary_invariants_and_safety(
    client, demo_dcpu_tvm, dcpu_tvm_headers, demo_field_tvm, field_tvm_headers, demo_dcpu_kollam, dcpu_klm_headers
):
    # 1. Create a case
    rep = client.post(
        "/api/reports",
        json={
            "district": "Thiruvananthapuram",
            "panchayat": "Varkala",
            "category": "Physical abuse",
            "description": "Allegation of physical harm reported.",
        },
    ).json()["report"]
    case_id = rep["case_id"]
    original_status = rep["status"]

    # 2. DCPU officer generates AI summary
    res = client.post(f"/api/cases/{case_id}/ai-summary", headers=dcpu_tvm_headers)
    assert res.status_code == 200
    data = res.json()

    # Safety Invariant Checks
    assert data["ai_generated"] is True
    assert data["verified"] is False
    assert data["human_review_required"] is True
    assert "disclaimer" in data
    assert "human decision-making" in data["disclaimer"]
    assert "NOT determine abuse" in data["disclaimer"]

    # Check missing info
    assert len(data["missing_information"]) >= 3
    # Check related hints
    assert len(data["related_case_hints"]) >= 1
    hint = data["related_case_hints"][0]
    assert "similar_cases_count" in hint
    assert "No narrative content" in hint["note"]

    # Case status must remain completely UNCHANGED
    case_after = client.get(f"/api/cases/{case_id}", headers=dcpu_tvm_headers).json()
    assert case_after["status"] == original_status

    # Audit history must have logged AI Summary Generation
    hist = client.get(f"/api/cases/{case_id}/history", headers=dcpu_tvm_headers).json()
    actions = [h["action"] for h in hist["history"]]
    assert "AI Summary Generated" in actions

    # 3. Field officer cannot request AI summary -> 403
    res_fo = client.post(f"/api/cases/{case_id}/ai-summary", headers=field_tvm_headers)
    assert res_fo.status_code == 403
    assert "Action restricted" in res_fo.json()["message"]

    # 4. Out of scope DCPU officer cannot request AI summary -> 403
    res_klm = client.post(f"/api/cases/{case_id}/ai-summary", headers=dcpu_klm_headers)
    assert res_klm.status_code == 403
    assert "district scope" in res_klm.json()["message"]
