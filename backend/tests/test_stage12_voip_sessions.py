from datetime import datetime, timedelta, timezone
from app.database import get_db
from app.models import CallSession, CaseHistory, Report
from app.security import verify_password
from app.services.voip_service import (
    check_and_expire_ring_timeouts,
    create_ws_ticket,
    validate_and_consume_ws_ticket,
)


def create_sample_report(client, district="Thiruvananthapuram", panchayat="Varkala"):
    payload = {
        "district": district,
        "panchayat": panchayat,
        "category": "Neglect",
        "description": "Simulated report for VoIP call testing.",
    }
    res = client.post("/api/reports", json=payload)
    assert res.status_code == 201
    data = res.json()
    return data["report"]["case_id"], data["reporter_token"]


def test_reporter_callback_request_with_correct_and_wrong_token(client, db_session):
    case_id, reporter_token = create_sample_report(client)
    assert reporter_token is not None
    assert len(reporter_token) > 10

    # Verify plain token is NOT stored in DB, only its bcrypt hash
    report = db_session.query(Report).filter(Report.report_id == case_id).first()
    assert report.reporter_token_hash is not None
    assert report.reporter_token_hash != reporter_token
    assert verify_password(reporter_token, report.reporter_token_hash)

    # 1. Missing header -> 401
    res_no_header = client.post(f"/api/reports/{case_id}/callback-request")
    assert res_no_header.status_code == 401
    assert "Missing X-Reporter-Token" in res_no_header.json()["message"]

    # 2. Wrong token in header -> 401
    res_wrong_token = client.post(
        f"/api/reports/{case_id}/callback-request",
        headers={"X-Reporter-Token": "wrong_token_123"},
    )
    assert res_wrong_token.status_code == 401
    assert "Invalid reporter token" in res_wrong_token.json()["message"]

    # 3. Correct token -> 201 Created
    res_ok = client.post(
        f"/api/reports/{case_id}/callback-request",
        headers={"X-Reporter-Token": reporter_token},
    )
    assert res_ok.status_code == 201
    data = res_ok.json()
    assert data["simulated"] is True
    assert "notice" in data
    assert "Simulated prototype call" in data["notice"]
    call = data["call"]
    assert call["status"] == "requested"
    assert call["requested_by"] == "reporter"
    assert call["simulated"] is True


def test_district_scope_on_every_officer_call_endpoint(
    client,
    demo_dcpu_tvm,
    dcpu_tvm_headers,
    demo_dcpu_kollam,
    dcpu_klm_headers,
):
    case_id, reporter_token = create_sample_report(client, district="Thiruvananthapuram")

    # Reporter creates callback request
    res_req = client.post(
        f"/api/reports/{case_id}/callback-request",
        headers={"X-Reporter-Token": reporter_token},
    )
    assert res_req.status_code == 201
    call_id = res_req.json()["call"]["id"]

    # 1. GET /api/cases/{case_id}/calls
    # Unauthenticated -> 401
    assert client.get(f"/api/cases/{case_id}/calls").status_code == 401
    # TVM officer (matching district) -> 200
    res_tvm = client.get(f"/api/cases/{case_id}/calls", headers=dcpu_tvm_headers)
    assert res_tvm.status_code == 200
    assert res_tvm.json()["count"] == 1
    # KLM officer (different district) -> 403
    res_klm = client.get(f"/api/cases/{case_id}/calls", headers=dcpu_klm_headers)
    assert res_klm.status_code == 403

    # 2. POST /api/cases/{case_id}/calls
    # KLM officer tries to start call on TVM case -> 403
    res_post_klm = client.post(
        f"/api/cases/{case_id}/calls",
        headers=dcpu_klm_headers,
        json={"override_solved": False},
    )
    assert res_post_klm.status_code == 403

    # 3. GET /api/calls/{call_id}
    # TVM officer -> 200
    assert client.get(f"/api/calls/{call_id}", headers=dcpu_tvm_headers).status_code == 200
    # KLM officer -> 403
    assert client.get(f"/api/calls/{call_id}", headers=dcpu_klm_headers).status_code == 403


def test_full_happy_path_requested_to_ringing_to_connected_to_ended(
    client,
    demo_dcpu_tvm,
    dcpu_tvm_headers,
):
    case_id, reporter_token = create_sample_report(client)

    # 1. Reporter requests callback (status: requested)
    res_req = client.post(
        f"/api/reports/{case_id}/callback-request",
        headers={"X-Reporter-Token": reporter_token},
    )
    assert res_req.status_code == 201
    call_id = res_req.json()["call"]["id"]
    assert res_req.json()["call"]["status"] == "requested"

    # 2. Officer answers callback -> transitions status to ringing
    res_start = client.post(
        f"/api/cases/{case_id}/calls",
        headers=dcpu_tvm_headers,
        json={"override_solved": False},
    )
    assert res_start.status_code == 200 or res_start.status_code == 201
    call_ringing = res_start.json()["call"]
    assert call_ringing["id"] == call_id
    assert call_ringing["status"] == "ringing"
    assert call_ringing["ringing_at"] is not None

    # 3. Reporter accepts the incoming ring -> transitions to connected
    res_accept = client.post(
        f"/api/calls/{call_id}/accept",
        headers={"X-Reporter-Token": reporter_token},
    )
    assert res_accept.status_code == 200
    call_conn = res_accept.json()["call"]
    assert call_conn["status"] == "connected"
    assert call_conn["connected_at"] is not None

    # 4. Officer ends the call -> transitions to ended with duration
    res_end = client.post(
        f"/api/calls/{call_id}/end",
        headers=dcpu_tvm_headers,
    )
    assert res_end.status_code == 200
    call_ended = res_end.json()["call"]
    assert call_ended["status"] == "ended"
    assert call_ended["ended_at"] is not None
    assert call_ended["end_reason"] == "normal"
    assert call_ended["duration_seconds"] >= 0


def test_officer_outbound_and_decline_and_cancel(
    client,
    demo_dcpu_tvm,
    dcpu_tvm_headers,
):
    case_id, reporter_token = create_sample_report(client)

    # 1. Officer initiates outbound call -> status: ringing
    res_start = client.post(
        f"/api/cases/{case_id}/calls",
        headers=dcpu_tvm_headers,
        json={"override_solved": False},
    )
    assert res_start.status_code == 201
    call_1 = res_start.json()["call"]
    assert call_1["status"] == "ringing"
    assert call_1["requested_by"] == "officer"

    # 2. Reporter declines the call -> status: declined
    res_dec = client.post(
        f"/api/calls/{call_1['id']}/decline",
        headers={"X-Reporter-Token": reporter_token},
    )
    assert res_dec.status_code == 200
    assert res_dec.json()["call"]["status"] == "declined"
    assert res_dec.json()["call"]["end_reason"] == "declined"

    # 3. Officer starts another call -> status: ringing
    res_start_2 = client.post(
        f"/api/cases/{case_id}/calls",
        headers=dcpu_tvm_headers,
        json={"override_solved": False},
    )
    assert res_start_2.status_code == 201
    call_2 = res_start_2.json()["call"]

    # 4. Officer cancels before connection -> status: cancelled
    res_cancel = client.post(
        f"/api/calls/{call_2['id']}/end",
        headers=dcpu_tvm_headers,
    )
    assert res_cancel.status_code == 200
    assert res_cancel.json()["call"]["status"] == "cancelled"
    assert res_cancel.json()["call"]["end_reason"] == "cancelled"


def test_ring_timeout_to_missed(client, db_session, demo_dcpu_tvm, dcpu_tvm_headers):
    case_id, reporter_token = create_sample_report(client)

    res_start = client.post(
        f"/api/cases/{case_id}/calls",
        headers=dcpu_tvm_headers,
        json={"override_solved": False},
    )
    assert res_start.status_code == 201
    call_id = res_start.json()["call"]["id"]

    # Manually backdate ringing_at to 60 seconds ago
    call = db_session.query(CallSession).filter(CallSession.id == call_id).first()
    call.ringing_at = datetime.now(timezone.utc) - timedelta(seconds=60)
    db_session.commit()

    # Call the ring timeout helper
    expired_count = check_and_expire_ring_timeouts(db_session, timeout_seconds=45)
    assert expired_count >= 1

    # Verify session transitioned to missed
    db_session.refresh(call)
    assert call.status == "missed"
    assert call.end_reason == "missed"

    # Verify history event was recorded
    history_entry = (
        db_session.query(CaseHistory)
        .filter(CaseHistory.entity_id == call_id, CaseHistory.action == "call_missed")
        .first()
    )
    assert history_entry is not None


def test_illegal_transitions_rejected(client, demo_dcpu_tvm, dcpu_tvm_headers):
    case_id, reporter_token = create_sample_report(client)

    res_start = client.post(
        f"/api/cases/{case_id}/calls",
        headers=dcpu_tvm_headers,
        json={"override_solved": False},
    )
    call_id = res_start.json()["call"]["id"]

    # End the call
    client.post(f"/api/calls/{call_id}/end", headers=dcpu_tvm_headers)

    # Attempting to accept an ended call -> 400
    res_accept = client.post(
        f"/api/calls/{call_id}/accept",
        headers={"X-Reporter-Token": reporter_token},
    )
    assert res_accept.status_code == 400
    assert "Illegal call transition" in res_accept.json()["message"]

    # Attempting to decline an ended call -> 400
    res_decline = client.post(
        f"/api/calls/{call_id}/decline",
        headers={"X-Reporter-Token": reporter_token},
    )
    assert res_decline.status_code == 400
    assert "Illegal call transition" in res_decline.json()["message"]


def test_one_active_call_per_case_and_rate_limit(
    client,
    demo_dcpu_tvm,
    dcpu_tvm_headers,
):
    case_id, reporter_token = create_sample_report(client)

    # 1. Start a call (status ringing)
    res1 = client.post(
        f"/api/cases/{case_id}/calls",
        headers=dcpu_tvm_headers,
        json={"override_solved": False},
    )
    assert res1.status_code == 201

    # 2. Attempting to start another active call returns 409 Conflict
    res2 = client.post(
        f"/api/cases/{case_id}/calls",
        headers=dcpu_tvm_headers,
        json={"override_solved": False},
    )
    assert res2.status_code == 409
    assert "already exists" in res2.json()["message"]

    # End call 1
    call_id = res1.json()["call"]["id"]
    client.post(f"/api/calls/{call_id}/end", headers=dcpu_tvm_headers)

    # 3. Create calls up to limit (5 calls per case per day)
    # We already have 1 ended call. Create 4 more ended calls.
    for _ in range(4):
        r_start = client.post(
            f"/api/cases/{case_id}/calls",
            headers=dcpu_tvm_headers,
            json={"override_solved": False},
        )
        assert r_start.status_code == 201
        c_id = r_start.json()["call"]["id"]
        client.post(f"/api/calls/{c_id}/end", headers=dcpu_tvm_headers)

    # 4. 6th call should hit 429 Too Many Requests
    res_limit = client.post(
        f"/api/cases/{case_id}/calls",
        headers=dcpu_tvm_headers,
        json={"override_solved": False},
    )
    assert res_limit.status_code == 429
    assert "Daily call limit reached" in res_limit.json()["message"]


def test_solved_case_call_behavior(client, db_session, demo_dcpu_tvm, dcpu_tvm_headers):
    case_id, reporter_token = create_sample_report(client)

    # Mark report as Solved
    rep = db_session.query(Report).filter(Report.report_id == case_id).first()
    rep.status = "Solved"
    db_session.commit()

    # 1. Attempting without override returns 400
    res_fail = client.post(
        f"/api/cases/{case_id}/calls",
        headers=dcpu_tvm_headers,
        json={"override_solved": False},
    )
    assert res_fail.status_code == 400
    assert "Case is already Solved" in res_fail.json()["message"]

    # 2. With override_solved=True succeeds
    res_ok = client.post(
        f"/api/cases/{case_id}/calls",
        headers=dcpu_tvm_headers,
        json={"override_solved": True},
    )
    assert res_ok.status_code == 201
    call_id = res_ok.json()["call"]["id"]

    # Verify call_override_logged event in history
    override_event = (
        db_session.query(CaseHistory)
        .filter(CaseHistory.action == "call_override_logged")
        .first()
    )
    assert override_event is not None


def test_ws_ticket_single_use_and_expires(client, demo_dcpu_tvm, dcpu_tvm_headers):
    case_id, reporter_token = create_sample_report(client)

    res_start = client.post(
        f"/api/cases/{case_id}/calls",
        headers=dcpu_tvm_headers,
        json={"override_solved": False},
    )
    call_id = res_start.json()["call"]["id"]

    # 1. Request ticket as officer
    res_ticket = client.post(
        f"/api/calls/{call_id}/ws-ticket",
        headers=dcpu_tvm_headers,
    )
    assert res_ticket.status_code == 200
    ticket_data = res_ticket.json()
    ticket = ticket_data["ticket"]
    assert ticket_data["expires_in"] == 60
    assert ticket_data["simulated"] is True

    # 2. First consumption succeeds
    consumed = validate_and_consume_ws_ticket(ticket, call_id)
    assert consumed is not None
    assert consumed["role"] == "officer"

    # 3. Second consumption with same ticket fails (single-use)
    consumed_again = validate_and_consume_ws_ticket(ticket, call_id)
    assert consumed_again is None

    # 4. Ticket with expired time fails
    expired_ticket = create_ws_ticket(call_id=call_id, role="reporter", expires_in=-10)
    assert validate_and_consume_ws_ticket(expired_ticket, call_id) is None


def test_signalling_websocket_relay(client, demo_dcpu_tvm, dcpu_tvm_headers):
    case_id, reporter_token = create_sample_report(client)

    res_start = client.post(
        f"/api/cases/{case_id}/calls",
        headers=dcpu_tvm_headers,
        json={"override_solved": False},
    )
    call_id = res_start.json()["call"]["id"]

    # Get tickets for officer and reporter
    res_t1 = client.post(f"/api/calls/{call_id}/ws-ticket", headers=dcpu_tvm_headers)
    assert res_t1.status_code == 200
    t1 = res_t1.json()["ticket"]

    res_t2 = client.post(
        f"/api/calls/{call_id}/ws-ticket",
        headers={"X-Reporter-Token": reporter_token},
    )
    assert res_t2.status_code == 200
    t2 = res_t2.json()["ticket"]

    # Connect officer WebSocket
    with client.websocket_connect(f"/api/calls/{call_id}/signal?ticket={t1}") as ws_officer:
        # Connect reporter WebSocket
        with client.websocket_connect(f"/api/calls/{call_id}/signal?ticket={t2}") as ws_reporter:
            # Officer should receive notification that reporter joined
            peer_event = ws_officer.receive_json()
            assert peer_event["type"] == "peer_joined"
            assert peer_event["role"] == "reporter"

            # Reporter sends simulated offer
            ws_reporter.send_json({"type": "offer", "sdp": "simulated-offer-data"})

            # Officer receives relayed message untouched
            relayed_msg = ws_officer.receive_json()
            assert relayed_msg["type"] == "offer"
            assert relayed_msg["sdp"] == "simulated-offer-data"


def test_ice_config_endpoint(client, dcpu_tvm_headers):
    res = client.get("/api/calls/ice-config", headers=dcpu_tvm_headers)
    assert res.status_code == 200
    data = res.json()
    assert "ice_servers" in data
    assert data["simulated"] is True
