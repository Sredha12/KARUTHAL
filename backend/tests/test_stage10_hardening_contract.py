import os
import tempfile
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.models import Report
from app.seed_data import KERALA_DISTRICTS
from main import app


def test_frontend_contract_mirroring_officer_api(client, demo_dcpu_tvm, dcpu_tvm_headers):
    """
    Contract test strictly mirroring the client checks in src/services/officerApi.js.
    1. POST /api/login -> {token, name, district} non-empty strings, district in keralaDistricts
    2. GET /api/dashboard -> {total, solved, pending, urgent, reports:[...], calls:[...]}
    3. PATCH /api/report/{id} -> updated report JSON
    4. PATCH /api/emergency/{id} -> updated call JSON
    """
    # 1. Login Contract
    login_res = client.post(
        "/api/login",
        json={"login": "DCPU-TVM-01", "password": "DemoTestPass123"},
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert isinstance(login_data.get("token"), str) and len(login_data["token"]) > 0
    assert isinstance(login_data.get("name"), str) and len(login_data["name"]) > 0
    assert isinstance(login_data.get("district"), str) and len(login_data["district"]) > 0
    valid_district_names = [d["name"] for d in KERALA_DISTRICTS]
    assert login_data["district"] in valid_district_names

    # 2. Dashboard Contract
    dash_res = client.get(f"/api/dashboard?district={login_data['district']}", headers=dcpu_tvm_headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()

    # Numbers must be finite integers
    for metric in ("total", "solved", "pending", "urgent"):
        assert isinstance(dash_data.get(metric), int)
        assert dash_data[metric] >= 0

    assert isinstance(dash_data.get("reports"), list)
    assert isinstance(dash_data.get("calls"), list)

    # 3. PATCH /api/report/{id} Contract
    rep_res = client.post(
        "/api/reports",
        json={
            "district": "Thiruvananthapuram",
            "panchayat": "Varkala",
            "category": "Neglect",
            "description": "Contract validation report.",
        },
    )
    rep_id = rep_res.json()["report"]["id"]

    patch_rep_res = client.patch(
        f"/api/report/{rep_id}",
        json={"status": "Solved"},
        headers=dcpu_tvm_headers,
    )
    assert patch_rep_res.status_code == 200
    assert patch_rep_res.json()["status"] == "Solved"

    # 4. PATCH /api/emergency/{id} Contract
    em_res = client.post(
        "/api/emergency",
        json={"category": "Urgent Alert", "district": "Thiruvananthapuram"},
        headers=dcpu_tvm_headers,
    )
    call_id = em_res.json()["call"]["id"]

    patch_em_res = client.patch(
        f"/api/emergency/{call_id}",
        json={"status": "Acknowledged", "notes": "Handled."},
        headers=dcpu_tvm_headers,
    )
    assert patch_em_res.status_code == 200
    assert patch_em_res.json()["status"] == "Acknowledged"


def test_security_headers_present(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.headers.get("x-content-type-options") == "nosniff"
    assert res.headers.get("x-frame-options") == "DENY"
    assert res.headers.get("x-xss-protection") == "1; mode=block"
    assert "strict-transport-security" in res.headers


def test_cors_preflight_for_patch_with_auth(client):
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "PATCH",
        "Access-Control-Request-Headers": "Authorization, Content-Type",
    }
    res = client.options("/api/report/1", headers=headers)
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "PATCH" in res.headers.get("access-control-allow-methods", "")
    assert "authorization" in res.headers.get("access-control-allow-headers", "").lower()


def test_consistent_message_format_on_all_error_types(client, dcpu_tvm_headers):
    # 400 Bad Request
    res_400 = client.get("/api/dashboard?district=InvalidDistrictName", headers=dcpu_tvm_headers)
    assert res_400.status_code == 400
    assert "message" in res_400.json() and "detail" not in res_400.json()

    # 401 Unauthorized
    res_401 = client.get("/api/dashboard?district=Thiruvananthapuram")
    assert res_401.status_code == 401
    assert "message" in res_401.json() and "detail" not in res_401.json()

    # 403 Forbidden
    res_403 = client.get("/api/dashboard?district=Kollam", headers=dcpu_tvm_headers)
    assert res_403.status_code == 403
    assert "message" in res_403.json() and "detail" not in res_403.json()

    # 404 Not Found
    res_404 = client.get("/api/reports/KAR-NONEXISTENT")
    assert res_404.status_code == 404
    assert "message" in res_404.json() and "detail" not in res_404.json()

    # 422 Unprocessable Content
    res_422 = client.post("/api/reports", json={"district": "T"})
    assert res_422.status_code == 422
    assert "message" in res_422.json() and "detail" not in res_422.json()


def test_data_survives_restart_on_file_db():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "test_persistence.db")
        db_url = f"sqlite:///{db_path}"

        # 1. Start session 1: create table and insert report
        engine1 = create_engine(db_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine1)
        Session1 = sessionmaker(bind=engine1)

        with Session1() as db1:
            rep = Report(
                report_id="KAR-PERSIST1",
                district="Thiruvananthapuram",
                panchayat="Varkala",
                category="Neglect",
                description="Checking data persistence across restarts.",
                status="Submitted",
            )
            db1.add(rep)
            db1.commit()

        engine1.dispose()

        # 2. Simulate complete restart: new engine and session connecting to same file
        engine2 = create_engine(db_url, connect_args={"check_same_thread": False})
        Session2 = sessionmaker(bind=engine2)

        with Session2() as db2:
            saved_rep = db2.query(Report).filter(Report.report_id == "KAR-PERSIST1").first()
            assert saved_rep is not None
            assert saved_rep.report_id == "KAR-PERSIST1"
            assert saved_rep.district == "Thiruvananthapuram"

        engine2.dispose()


def test_database_unavailable_returns_message_format():
    def broken_db_override():
        from sqlalchemy.exc import OperationalError
        raise OperationalError("Unable to connect to database", {}, None)

    app.dependency_overrides[get_db] = broken_db_override
    with TestClient(app) as test_client:
        res = test_client.get("/api/reports")
        assert res.status_code == 503
        data = res.json()
        assert "message" in data
        assert "Database service is temporarily unavailable" in data["message"]
    app.dependency_overrides.clear()
