def test_root_and_health(client):
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert res_root.json() == {"project": "Karuthal", "message": "Backend is running"}

    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json() == {"status": "healthy"}


def test_create_report_success(client):
    payload = {
        "district": "Kollam",
        "panchayat": "Chavara",
        "category": "Neglect",
        "description": "Child seen wandering alone without supervision near the market.",
    }
    response = client.post("/api/reports", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Demo report submitted successfully"
    report = data["report"]
    assert report["case_id"].startswith("KAR-")
    assert len(report["case_id"]) == 12  # KAR- (4) + 8 hex chars
    assert report["district"] == "Kollam"
    assert report["panchayat"] == "Chavara"
    assert report["category"] == "Neglect"
    assert report["status"] == "Submitted"


def test_list_and_get_report(client):
    payload = {
        "district": "Thiruvananthapuram",
        "panchayat": "Varkala",
        "category": "Physical abuse",
        "description": "Concern about suspected physical mistreatment in residential area.",
    }
    post_res = client.post("/api/reports", json=payload)
    case_id = post_res.json()["report"]["case_id"]

    # List
    list_res = client.get("/api/reports")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["count"] >= 1
    case_ids = [r["case_id"] for r in list_data["reports"]]
    assert case_id in case_ids

    # Get single
    get_res = client.get(f"/api/reports/{case_id}")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["case_id"] == case_id
    assert get_data["district"] == "Thiruvananthapuram"


def test_not_found_returns_message_format(client):
    res = client.get("/api/reports/KAR-NONEXIST")
    assert res.status_code == 404
    data = res.json()
    assert "message" in data
    assert data["message"] == "Report not found"
    assert "detail" not in data


def test_validation_error_returns_message_format(client):
    # Missing description and short district
    payload = {"district": "A", "category": "Neglect"}
    res = client.post("/api/reports", json=payload)
    assert res.status_code == 422
    data = res.json()
    assert "message" in data
    assert isinstance(data["message"], str)
    assert "detail" not in data


def test_cors_headers(client):
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "PATCH",
        "Access-Control-Request-Headers": "Authorization, Content-Type",
    }
    res = client.options("/api/reports", headers=headers)
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "http://localhost:5173"
