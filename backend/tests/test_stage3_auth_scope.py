from app.security import clear_login_failures


def test_login_success_by_officer_code(client, demo_dcpu_tvm):
    clear_login_failures("DCPU-TVM-01")
    payload = {
        "login": "DCPU-TVM-01",
        "password": "DemoTestPass123",
    }
    res = client.post("/api/login", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "token" in data and len(data["token"]) > 20
    assert data["name"] == "Anjali Nair"
    assert data["district"] == "Thiruvananthapuram"


def test_login_success_by_email(client, demo_dcpu_tvm):
    clear_login_failures("dcpu.tvm@karuthal.demo")
    payload = {
        "login": "dcpu.tvm@karuthal.demo",
        "password": "DemoTestPass123",
    }
    res = client.post("/api/login", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Anjali Nair"
    assert data["district"] == "Thiruvananthapuram"


def test_login_bad_password_401(client, demo_dcpu_tvm):
    clear_login_failures("DCPU-TVM-01")
    payload = {
        "login": "DCPU-TVM-01",
        "password": "WrongPassword123!",
    }
    res = client.post("/api/login", json=payload)
    assert res.status_code == 401
    assert "message" in res.json()
    assert "Invalid credentials" in res.json()["message"]


def test_login_nonexistent_user_401(client):
    clear_login_failures("UNKNOWN-99")
    payload = {
        "login": "UNKNOWN-99",
        "password": "WrongPassword123!",
    }
    res = client.post("/api/login", json=payload)
    assert res.status_code == 401
    assert "message" in res.json()


def test_login_rate_limiting_throttle(client, demo_dcpu_tvm):
    clear_login_failures("DCPU-TVM-01")
    # Fail 5 times
    for _ in range(5):
        res = client.post(
            "/api/login",
            json={"login": "DCPU-TVM-01", "password": "WrongPassword!"},
        )
        assert res.status_code == 401

    # 6th attempt should be blocked by rate limiter (429)
    res_blocked = client.post(
        "/api/login",
        json={"login": "DCPU-TVM-01", "password": "DemoTestPass123"},
    )
    assert res_blocked.status_code == 429
    assert "message" in res_blocked.json()
    assert "Too many failed login attempts" in res_blocked.json()["message"]

    # Clear for subsequent tests
    clear_login_failures("DCPU-TVM-01")


def test_auth_me_endpoints(client, dcpu_tvm_headers):
    # 1. Without token: 401
    res_no_token = client.get("/api/auth/me")
    assert res_no_token.status_code == 401
    assert "message" in res_no_token.json()

    # 2. With invalid token: 401
    res_bad_token = client.get("/api/auth/me", headers={"Authorization": "Bearer badtoken123"})
    assert res_bad_token.status_code == 401
    assert "message" in res_bad_token.json()

    # 3. With valid token: 200
    res_valid = client.get("/api/auth/me", headers=dcpu_tvm_headers)
    assert res_valid.status_code == 200
    data = res_valid.json()
    assert data["officer_code"] == "DCPU-TVM-01"
    assert data["role"] == "dcpu_officer"
    assert data["district"] == "Thiruvananthapuram"
