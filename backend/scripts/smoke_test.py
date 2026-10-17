import os
import sys
import time
import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://127.0.0.1:8000"
DEMO_PASSWORD = os.getenv("DEMO_OFFICER_PASSWORD")


def run_smoke_test(stage="initial", test_report_id=None):
    print(f"=== Running Live Smoke Test (Stage: {stage}) ===")

    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        # 1. Health check
        res_health = client.get("/health")
        assert res_health.status_code == 200, f"Health check failed: {res_health.text}"
        assert res_health.json() == {"status": "healthy"}
        print("[OK] Health check verified (200 OK)")

        # 2. Login
        res_login = client.post(
            "/api/login",
            json={"login": "DCPU-TVM-01", "password": DEMO_PASSWORD},
        )
        assert res_login.status_code == 200, f"Login failed: {res_login.text}"
        login_data = res_login.json()
        token = login_data["token"]
        assert len(token) > 20
        print(f"[OK] Login successful for {login_data['name']} ({login_data['district']})")

        headers = {"Authorization": f"Bearer {token}"}

        if stage == "initial":
            # 3. Submit report
            rep_payload = {
                "district": "Thiruvananthapuram",
                "panchayat": "Varkala",
                "category": "Neglect",
                "description": "Live smoke test case to verify persistence across server restarts.",
                "is_urgent": True,
            }
            res_rep = client.post("/api/reports", json=rep_payload)
            assert res_rep.status_code == 201, f"Report submission failed: {res_rep.text}"
            report_data = res_rep.json()["report"]
            numeric_id = report_data["id"]
            case_id = report_data["case_id"]
            print(f"[OK] Public report created: {case_id} (DB ID: {numeric_id})")

            # 4. Check dashboard
            res_dash = client.get("/api/dashboard?district=Thiruvananthapuram", headers=headers)
            assert res_dash.status_code == 200, f"Dashboard failed: {res_dash.text}"
            dash_data = res_dash.json()
            assert dash_data["total"] > 0
            print(f"[OK] Dashboard loaded: total={dash_data['total']}, pending={dash_data['pending']}, urgent={dash_data['urgent']}")

            # 5. Patch report to Solved
            res_patch = client.patch(
                f"/api/report/{numeric_id}",
                json={"status": "Solved"},
                headers=headers,
            )
            assert res_patch.status_code == 200, f"Patch failed: {res_patch.text}"
            assert res_patch.json()["status"] == "Solved"
            print(f"[OK] Report {case_id} marked as 'Solved'")

            print(f"RESULT_CASE_ID={case_id}")
            return numeric_id, case_id

        elif stage == "post_restart":
            assert test_report_id is not None, "Missing test_report_id for restart verification"
            res_case = client.get(f"/api/cases/{test_report_id}", headers=headers)
            assert res_case.status_code == 200, f"Case fetch failed: {res_case.text}"
            case_data = res_case.json()
            assert case_data["status"] == "Solved", f"Expected Solved, got {case_data['status']}"
            print(f"[OK] Post-restart persistence verified! Case {test_report_id} is intact and status is 'Solved'")
            return True


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "initial"
    rep_ref = sys.argv[2] if len(sys.argv) > 2 else None
    run_smoke_test(mode, rep_ref)
