def test_dashboard_endpoint_success(client, demo_dcpu_tvm, dcpu_tvm_headers):
    # Create two reports in Thiruvananthapuram: one urgent pending, one standard
    rep1 = client.post(
        "/api/reports",
        json={
            "district": "Thiruvananthapuram",
            "panchayat": "Varkala",
            "category": "Neglect",
            "description": "Fictional child protection report 1.",
            "is_urgent": True,
        },
    ).json()["report"]

    rep2 = client.post(
        "/api/reports",
        json={
            "district": "Thiruvananthapuram",
            "panchayat": "Nedumangad",
            "category": "Emotional abuse",
            "description": "Fictional child protection report 2.",
            "is_urgent": False,
        },
    ).json()["report"]

    res = client.get("/api/dashboard?district=Thiruvananthapuram", headers=dcpu_tvm_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["total"] >= 2
    assert data["pending"] >= 2
    assert data["urgent"] >= 1
    assert isinstance(data["reports"], list)
    assert isinstance(data["calls"], list)

    # Validate exact field names needed by ReportsTable.jsx
    first_report = data["reports"][0]
    for key in ("id", "case_id", "report_id", "status", "category", "abuse_type", "panchayat", "location", "district", "is_urgent", "created_at"):
        assert key in first_report, f"Missing report field '{key}'"


def test_dashboard_auth_and_scope_checks(client, dcpu_tvm_headers):
    # 1. No token -> 401
    res_no_token = client.get("/api/dashboard?district=Thiruvananthapuram")
    assert res_no_token.status_code == 401
    assert "message" in res_no_token.json()

    # 2. Unsupported district -> 400
    res_bad_dist = client.get("/api/dashboard?district=NonexistentDistrict", headers=dcpu_tvm_headers)
    assert res_bad_dist.status_code == 400
    assert "message" in res_bad_dist.json()

    # 3. Officer out of district scope -> 403
    res_out_of_scope = client.get("/api/dashboard?district=Kollam", headers=dcpu_tvm_headers)
    assert res_out_of_scope.status_code == 403
    assert "message" in res_out_of_scope.json()


def test_patch_report_by_numeric_id(client, demo_dcpu_tvm, dcpu_tvm_headers, demo_dcpu_kollam, dcpu_klm_headers):
    # Create report in Thiruvananthapuram
    rep_res = client.post(
        "/api/reports",
        json={
            "district": "Thiruvananthapuram",
            "panchayat": "Varkala",
            "category": "Physical abuse",
            "description": "Child protection concern requiring resolution.",
        },
    )
    rep_id = rep_res.json()["report"]["id"]

    # 1. Successful patch to 'Solved' by TVM officer
    patch_res = client.patch(
        f"/api/report/{rep_id}",
        json={"status": "Solved"},
        headers=dcpu_tvm_headers,
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["status"] == "Solved"
    assert data["solved_at"] is not None

    # 2. Patching non-existent report -> 404
    res_404 = client.patch(
        "/api/report/99999",
        json={"status": "Solved"},
        headers=dcpu_tvm_headers,
    )
    assert res_404.status_code == 404
    assert "message" in res_404.json()

    # 3. Invalid status -> 422
    res_422 = client.patch(
        f"/api/report/{rep_id}",
        json={"status": "InvalidStatus"},
        headers=dcpu_tvm_headers,
    )
    assert res_422.status_code == 422
    assert "message" in res_422.json()

    # 4. Out of scope officer -> 403
    res_403 = client.patch(
        f"/api/report/{rep_id}",
        json={"status": "Solved"},
        headers=dcpu_klm_headers,
    )
    assert res_403.status_code == 403
    assert "message" in res_403.json()


def test_cases_list_and_detail(client, demo_dcpu_tvm, dcpu_tvm_headers, demo_field_tvm, field_tvm_headers):
    # List cases in TVM
    res = client.get("/api/cases", headers=dcpu_tvm_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "cases" in data

    if data["cases"]:
        target_case = data["cases"][0]
        case_id = target_case["case_id"]

        # Get detail by public KAR-XXXXXXXX case_id
        detail_res = client.get(f"/api/cases/{case_id}", headers=dcpu_tvm_headers)
        assert detail_res.status_code == 200
        assert detail_res.json()["case_id"] == case_id

        # Update status via /api/cases/{case_id}/status
        update_res = client.patch(
            f"/api/cases/{case_id}/status",
            json={"status": "Under Review"},
            headers=dcpu_tvm_headers,
        )
        assert update_res.status_code == 200
        assert update_res.json()["status"] == "Under Review"
