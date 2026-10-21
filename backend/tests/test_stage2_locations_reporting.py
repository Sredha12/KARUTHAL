def test_get_all_kerala_districts(client):
    res = client.get("/api/locations/districts")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 14
    names = [d["name"] for d in data]
    assert "Thiruvananthapuram" in names
    assert "Kollam" in names
    assert "Ernakulam" in names
    assert "Kozhikode" in names
    assert "Wayanad" in names


def test_get_panchayats_by_district(client):
    # Find Thiruvananthapuram district id
    dist_res = client.get("/api/locations/districts")
    tvm = next(d for d in dist_res.json() if d["name"] == "Thiruvananthapuram")

    panch_res = client.get(f"/api/locations/panchayats?district_id={tvm['id']}")
    assert panch_res.status_code == 200
    panchayats = panch_res.json()
    assert len(panchayats) >= 5
    panch_names = [p["name"] for p in panchayats]
    assert "Varkala" in panch_names
    assert "Nedumangad" in panch_names
    # Sample flag is explicitly True
    assert all(p["is_sample"] is True for p in panchayats)


def test_get_panchayats_nonexistent_district_404(client):
    res = client.get("/api/locations/panchayats?district_id=9999")
    assert res.status_code == 404
    assert "message" in res.json()


def test_public_report_validation_district_mismatch(client):
    # Chavara is in Kollam, not Thiruvananthapuram
    payload = {
        "district": "Thiruvananthapuram",
        "panchayat": "Chavara",
        "category": "Neglect",
        "description": "Suspected child neglect report in residential area.",
    }
    res = client.post("/api/reports", json=payload)
    assert res.status_code == 422
    assert "message" in res.json()
    assert "does not belong" in res.json()["message"]


def test_public_report_validation_invalid_category(client):
    payload = {
        "district": "Kollam",
        "panchayat": "Chavara",
        "category": "Alien Abduction",
        "description": "Nonsense category description exceeding minimum length requirement.",
    }
    res = client.post("/api/reports", json=payload)
    assert res.status_code == 422
    assert "message" in res.json()
    assert "Invalid category" in res.json()["message"]


def test_public_report_minimal_view_vs_officer_full_view(
    client, demo_dcpu_tvm, dcpu_tvm_headers, demo_dcpu_kollam, dcpu_klm_headers
):
    # Submit report in Thiruvananthapuram
    payload = {
        "district": "Thiruvananthapuram",
        "panchayat": "Varkala",
        "category": "Emotional abuse",
        "description": "Extremely detailed sensitive narrative that must be hidden from public view.",
        "is_urgent": True,
    }
    create_res = client.post("/api/reports", json=payload)
    assert create_res.status_code == 201
    case_id = create_res.json()["report"]["case_id"]

    # 1. Unauthenticated public view: should be minimal, NO description
    public_res = client.get(f"/api/reports/{case_id}")
    assert public_res.status_code == 200
    pub_data = public_res.json()
    assert pub_data["case_id"] == case_id
    assert pub_data["district"] == "Thiruvananthapuram"
    assert pub_data["status"] == "Submitted"
    assert "description" not in pub_data
    assert "privacy_notice" in pub_data

    # 2. Authenticated DCPU officer in Thiruvananthapuram: receives full view with description
    officer_res = client.get(f"/api/reports/{case_id}", headers=dcpu_tvm_headers)
    assert officer_res.status_code == 200
    off_data = officer_res.json()
    assert off_data["case_id"] == case_id
    assert off_data["description"] == payload["description"]
    assert off_data["panchayat"] == "Varkala"

    # 3. Authenticated DCPU officer from Kollam: denied (403 Forbidden)
    forbidden_res = client.get(f"/api/reports/{case_id}", headers=dcpu_klm_headers)
    assert forbidden_res.status_code == 403
    assert "message" in forbidden_res.json()
    assert "district scope" in forbidden_res.json()["message"]


def test_public_report_without_panchayat_succeeds(client):
    payload = {
        "district": "Thiruvananthapuram",
        "category": "Neglect",
        "description": "Report submitted without any panchayat specification.",
        "is_urgent": False,
    }
    res = client.post("/api/reports", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert "report" in data
    assert data["report"]["district"] == "Thiruvananthapuram"
    assert "reporter_token" in data

