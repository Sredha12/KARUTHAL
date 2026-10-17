def test_referral_lifecycle_and_dcpu_dashboard(
    client, demo_dcpu_tvm, dcpu_tvm_headers, demo_dcpu_kollam, dcpu_klm_headers
):
    # 1. Create a case in TVM
    rep = client.post(
        "/api/reports",
        json={
            "district": "Thiruvananthapuram",
            "panchayat": "Varkala",
            "category": "Neglect",
            "description": "Fictional case for referral testing.",
        },
    ).json()["report"]
    case_id = rep["case_id"]

    # 2. Create referral
    ref_payload = {
        "urgency": "Urgent",
        "concern_category": "Neglect",
        "next_action": "Initial family consultation",
        "service": "Child Welfare Committee (CWC)",
        "notes": "Referral for child support assessment.",
    }
    create_res = client.post(
        f"/api/cases/{case_id}/referrals",
        json=ref_payload,
        headers=dcpu_tvm_headers,
    )
    assert create_res.status_code == 201
    data = create_res.json()
    assert data["confirmed"] is False
    assert "disclaimer" in data
    referral = data["referral"]
    assert referral["caseRef"] == case_id
    assert referral["district"] == "Thiruvananthapuram"
    assert referral["status"] == "New"
    assert referral["serviceLinkage"]["service"] == "Child Welfare Committee (CWC)"
    assert referral["serviceLinkage"]["state"] == "Referred"
    assert isinstance(referral["history"], list)

    referral_id = referral["id"]

    # 3. Update referral via PATCH
    patch_res = client.patch(
        f"/api/referrals/{referral_id}",
        json={"status": "Under review", "service_state": "Engaged"},
        headers=dcpu_tvm_headers,
    )
    assert patch_res.status_code == 200
    patch_data = patch_res.json()
    assert patch_data["confirmed"] is False
    assert patch_data["referral"]["status"] == "Under review"
    assert patch_data["referral"]["serviceLinkage"]["state"] == "Engaged"

    # 4. Out of scope officer cannot update referral
    forbidden_res = client.patch(
        f"/api/referrals/{referral_id}",
        json={"status": "Closed"},
        headers=dcpu_klm_headers,
    )
    assert forbidden_res.status_code == 403
    assert "message" in forbidden_res.json()

    # 5. DCPU Dashboard retrieval
    dash_res = client.get("/api/dcpu/dashboard?district=Thiruvananthapuram", headers=dcpu_tvm_headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert "overview" in dash_data
    assert "referrals" in dash_data
    assert dash_data["overview"]["pendingReview"] >= 1
    assert len(dash_data["referrals"]) >= 1


def test_referral_validation_and_not_found(client, demo_dcpu_tvm, dcpu_tvm_headers):
    # 1. Non-existent referral -> 404
    res_404 = client.patch(
        "/api/referrals/99999",
        json={"status": "Closed"},
        headers=dcpu_tvm_headers,
    )
    assert res_404.status_code == 404
    assert "message" in res_404.json()

    # 2. Existing referral with invalid status -> 422
    rep = client.post(
        "/api/reports",
        json={
            "district": "Thiruvananthapuram",
            "panchayat": "Varkala",
            "category": "Neglect",
            "description": "Referral validation test case.",
        },
    ).json()["report"]

    ref_res = client.post(
        f"/api/cases/{rep['case_id']}/referrals",
        json={"urgency": "Standard", "service": "CWC"},
        headers=dcpu_tvm_headers,
    )
    ref_id = ref_res.json()["referral"]["id"]

    res_422 = client.patch(
        f"/api/referrals/{ref_id}",
        json={"status": "ArbitraryNonExistentStatus"},
        headers=dcpu_tvm_headers,
    )
    assert res_422.status_code == 422
    assert "Invalid referral status" in res_422.json()["message"]
