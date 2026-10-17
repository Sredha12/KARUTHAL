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

        # 2. Login as DCPU TVM officer
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
            # 3. Submit standard report
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

            # 6. Stage 11 Live Check: Location Routing & Map
            print("\n--- Verifying Stage 11 Location Routing ---")
            loc_payload = {
                "district": "Thiruvananthapuram",
                "panchayat": "Varkala",
                "category": "Physical abuse",
                "description": "Smoke test case with privacy-consented GPS coordinates.",
                "location_text": "Near the primary health sub-centre",
                "ward": "Ward 3",
                "approx_lat": 8.73654,
                "approx_lng": 76.71892,
                "location_consent": True,
                "location_source": "device",
            }
            res_loc_rep = client.post("/api/reports", json=loc_payload)
            assert res_loc_rep.status_code == 201, f"Location report failed: {res_loc_rep.text}"
            loc_rep_body = res_loc_rep.json()
            loc_case_id = loc_rep_body["report"]["case_id"]
            loc_reporter_token = loc_rep_body["reporter_token"]
            print(f"[OK] Location report created: {loc_case_id}")

            # Verify officer case location endpoint rounds coordinates (~1km) and labels simulated
            res_loc_view = client.get(f"/api/cases/{loc_case_id}/location", headers=headers)
            assert res_loc_view.status_code == 200, f"Location view failed: {res_loc_view.text}"
            loc_view_data = res_loc_view.json()
            assert loc_view_data["approx_lat"] == 8.74, f"Expected 8.74, got {loc_view_data['approx_lat']}"
            assert loc_view_data["approx_lng"] == 76.72, f"Expected 76.72, got {loc_view_data['approx_lng']}"
            assert loc_view_data["simulated"] is True
            print(f"[OK] Officer location retrieved: lat={loc_view_data['approx_lat']}, lng={loc_view_data['approx_lng']} (rounded to 2 decimal places, simulated: true)")

            # Verify district dashboard map GeoJSON
            res_map = client.get("/api/dashboard/map?district=Thiruvananthapuram", headers=headers)
            assert res_map.status_code == 200, f"Map failed: {res_map.text}"
            map_data = res_map.json()
            assert map_data["type"] == "FeatureCollection"
            assert any(f["properties"]["report_id"] == loc_case_id for f in map_data["features"])
            print(f"[OK] Dashboard GeoJSON map verified ({len(map_data['features'])} feature(s) found in Thiruvananthapuram)")

            # 7. Stage 12 Live Check: VoIP Call Session Lifecycle
            print("\n--- Verifying Stage 12 VoIP Call Sessions ---")
            # Step A: Anonymous reporter requests voice callback
            res_cb = client.post(
                f"/api/reports/{loc_case_id}/callback-request",
                headers={"X-Reporter-Token": loc_reporter_token},
            )
            assert res_cb.status_code == 201, f"Callback request failed: {res_cb.text}"
            cb_data = res_cb.json()
            call_id = cb_data["call"]["id"]
            assert cb_data["call"]["status"] == "requested"
            assert cb_data["simulated"] is True
            print(f"[OK] Reporter requested callback session #{call_id} (status: requested)")

            # Step B: Officer answers callback -> ringing
            res_call_start = client.post(
                f"/api/cases/{loc_case_id}/calls",
                headers=headers,
                json={"override_solved": False},
            )
            assert res_call_start.status_code in (200, 201), f"Call start failed: {res_call_start.text}"
            assert res_call_start.json()["call"]["status"] == "ringing"
            print(f"[OK] Officer initiated ringing for session #{call_id} (status: ringing)")

            # Step C: Reporter accepts call -> connected
            res_accept = client.post(
                f"/api/calls/{call_id}/accept",
                headers={"X-Reporter-Token": loc_reporter_token},
            )
            assert res_accept.status_code == 200, f"Call accept failed: {res_accept.text}"
            assert res_accept.json()["call"]["status"] == "connected"
            print(f"[OK] Reporter accepted session #{call_id} (status: connected)")

            # Step D: Officer ends call -> ended
            res_end = client.post(f"/api/calls/{call_id}/end", headers=headers)
            assert res_end.status_code == 200, f"Call end failed: {res_end.text}"
            ended_data = res_end.json()["call"]
            assert ended_data["status"] == "ended"
            assert ended_data["end_reason"] == "normal"
            assert ended_data["duration_seconds"] is not None
            assert ended_data["simulated"] is True
            print(f"[OK] Officer ended session #{call_id} (status: ended, duration: {ended_data['duration_seconds']}s, simulated: true)")

            # Step E: Check call list for the case
            res_calls_list = client.get(f"/api/cases/{loc_case_id}/calls", headers=headers)
            assert res_calls_list.status_code == 200, f"Calls list failed: {res_calls_list.text}"
            assert res_calls_list.json()["count"] >= 1
            print(f"[OK] Case calls list verified ({res_calls_list.json()['count']} session(s) recorded)")

            print(f"\nRESULT_CASE_ID={case_id}")
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
