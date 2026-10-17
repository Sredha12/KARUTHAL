from app.database import get_db
from app.models import Report
from app.services.location_service import apply_location_retention_policy


def test_typed_location_and_old_payload_compatibility(client):
    # 1. Old payload without any location fields
    old_payload = {
        "district": "Thiruvananthapuram",
        "panchayat": "Varkala",
        "category": "Neglect",
        "description": "Compatibility check without any new location fields.",
    }
    res_old = client.post("/api/reports", json=old_payload)
    assert res_old.status_code == 201
    data_old = res_old.json()
    assert "report" in data_old
    assert data_old["report"]["routed_district"] == "Thiruvananthapuram"
    assert data_old["report"]["has_location"] is False

    # 2. Valid typed location payload
    typed_payload = {
        "district": "Thiruvananthapuram",
        "panchayat": "Varkala",
        "category": "Neglect",
        "description": "Report with ward and location text provided by citizen.",
        "location_text": "Near the community water tank by the temple road",
        "ward": "Ward 4",
        "location_source": "typed",
    }
    res_typed = client.post("/api/reports", json=typed_payload)
    assert res_typed.status_code == 201
    data_typed = res_typed.json()["report"]
    assert data_typed["has_location"] is True


def test_coordinates_consent_and_rounding(client, demo_dcpu_tvm, dcpu_tvm_headers):
    # 1. Coordinates WITH consent: rounded to 2 decimal places (~1 km precision)
    consented_payload = {
        "district": "Thiruvananthapuram",
        "panchayat": "Varkala",
        "category": "Physical abuse",
        "description": "Consented location report for privacy rounding test.",
        "approx_lat": 8.73654,
        "approx_lng": 76.71892,
        "location_consent": True,
        "location_source": "device",
    }
    res_consented = client.post("/api/reports", json=consented_payload)
    assert res_consented.status_code == 201
    case_id = res_consented.json()["report"]["case_id"]

    # Verify via officer location endpoint
    loc_res = client.get(f"/api/cases/{case_id}/location", headers=dcpu_tvm_headers)
    assert loc_res.status_code == 200
    loc_data = loc_res.json()
    assert loc_data["approx_lat"] == 8.74  # Rounded to 2 decimal places
    assert loc_data["approx_lng"] == 76.72  # Rounded to 2 decimal places
    assert loc_data["location_consent"] is True
    assert loc_data["simulated"] is True

    # 2. Coordinates WITHOUT consent: coordinates must be dropped/nulled
    unconsented_payload = {
        "district": "Thiruvananthapuram",
        "panchayat": "Varkala",
        "category": "Neglect",
        "description": "Report where coordinates sent but consent false.",
        "approx_lat": 8.73654,
        "approx_lng": 76.71892,
        "location_consent": False,
        "location_source": "map_pick",
    }
    res_unconsented = client.post("/api/reports", json=unconsented_payload)
    assert res_unconsented.status_code == 201
    unconsented_case_id = res_unconsented.json()["report"]["case_id"]

    loc_unconsented_res = client.get(f"/api/cases/{unconsented_case_id}/location", headers=dcpu_tvm_headers)
    assert loc_unconsented_res.status_code == 200
    loc_unconsented_data = loc_unconsented_res.json()
    assert loc_unconsented_data["approx_lat"] is None
    assert loc_unconsented_data["approx_lng"] is None
    assert loc_unconsented_data["location_consent"] is False


def test_out_of_kerala_coordinates_rejected(client):
    # Latitude / Longitude outside Kerala envelope (e.g. Delhi: 28.61, 77.20)
    out_of_bounds = {
        "district": "Thiruvananthapuram",
        "panchayat": "Varkala",
        "category": "Neglect",
        "description": "Testing rejection of out-of-bounds geographic coordinates.",
        "approx_lat": 28.61,
        "approx_lng": 77.20,
        "location_consent": True,
    }
    res = client.post("/api/reports", json=out_of_bounds)
    assert res.status_code == 422
    assert "message" in res.json()
    assert "outside Kerala boundaries" in res.json()["message"]


def test_case_location_permissions_and_audit(
    client, demo_dcpu_tvm, dcpu_tvm_headers, demo_dcpu_kollam, dcpu_klm_headers
):
    rep = client.post(
        "/api/reports",
        json={
            "district": "Thiruvananthapuram",
            "panchayat": "Varkala",
            "category": "Neglect",
            "description": "Location permission verification case.",
            "location_text": "Near central library",
            "ward": "Ward 2",
        },
    ).json()["report"]
    case_id = rep["case_id"]

    # 1. Unauthenticated -> 401
    res_unauth = client.get(f"/api/cases/{case_id}/location")
    assert res_unauth.status_code == 401
    assert "message" in res_unauth.json()

    # 2. Out-of-district officer (Kollam officer requesting TVM case) -> 403 Forbidden
    res_forbidden = client.get(f"/api/cases/{case_id}/location", headers=dcpu_klm_headers)
    assert res_forbidden.status_code == 403
    assert "district scope" in res_forbidden.json()["message"]

    # 3. Authorized TVM officer -> 200
    res_auth = client.get(f"/api/cases/{case_id}/location", headers=dcpu_tvm_headers)
    assert res_auth.status_code == 200
    assert res_auth.json()["ward"] == "Ward 2"

    # 4. History event 'location_viewed' must be written without coordinates in log text
    hist_res = client.get(f"/api/cases/{case_id}/history", headers=dcpu_tvm_headers)
    assert hist_res.status_code == 200
    events = hist_res.json()["history"]
    loc_events = [e for e in events if e["action"] == "location_viewed"]
    assert len(loc_events) >= 1
    # Check that no coordinates leaked into the text description
    assert "lat" not in loc_events[0]["details"].lower()


def test_dashboard_map_geojson_and_scoping(
    client, demo_dcpu_tvm, dcpu_tvm_headers, demo_dcpu_kollam, dcpu_klm_headers
):
    # Create TVM report with consented coordinates
    client.post(
        "/api/reports",
        json={
            "district": "Thiruvananthapuram",
            "panchayat": "Varkala",
            "category": "Neglect",
            "description": "GeoJSON map test case.",
            "approx_lat": 8.734,
            "approx_lng": 76.712,
            "location_consent": True,
            "is_urgent": True,
        },
    )

    # 1. Unauthenticated -> 401
    res_unauth = client.get("/api/dashboard/map?district=Thiruvananthapuram")
    assert res_unauth.status_code == 401

    # 2. Out of scope district -> 403
    res_forbidden = client.get("/api/dashboard/map?district=Thiruvananthapuram", headers=dcpu_klm_headers)
    assert res_forbidden.status_code == 403

    # 3. Invalid district -> 400
    res_bad = client.get("/api/dashboard/map?district=NotADistrict", headers=dcpu_tvm_headers)
    assert res_bad.status_code == 400

    # 4. Authorized DCPU TVM officer -> 200 GeoJSON FeatureCollection
    res_map = client.get("/api/dashboard/map?district=Thiruvananthapuram", headers=dcpu_tvm_headers)
    assert res_map.status_code == 200
    data = res_map.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) >= 1

    feature = data["features"][0]
    assert feature["type"] == "Feature"
    assert feature["geometry"]["type"] == "Point"
    # GeoJSON coordinates format: [lng, lat]
    assert len(feature["geometry"]["coordinates"]) == 2
    props = feature["properties"]
    assert "report_id" in props
    assert "status" in props
    assert "is_urgent" in props
    assert "panchayat" in props
    # Privacy check: no description, names, or addresses in properties
    assert "description" not in props


def test_location_retention_policy(client, db_session):
    # Insert report with coordinates directly
    rep = Report(
        report_id="KAR-RETENT01",
        district="Thiruvananthapuram",
        panchayat="Varkala",
        category="Neglect",
        description="Testing coordinate retention cleanup.",
        status="Submitted",
        approx_lat=8.73,
        approx_lng=76.71,
        location_consent=True,
    )
    db_session.add(rep)
    db_session.commit()

    # Verify coordinates exist
    assert rep.approx_lat is not None

    # Run retention cleaner with retention_days = 0 (cleaning all reports up to now)
    cleaned = apply_location_retention_policy(db_session, retention_days=0)
    assert cleaned >= 1

    db_session.refresh(rep)
    assert rep.approx_lat is None
    assert rep.approx_lng is None
