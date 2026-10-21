# Karuthal Demo Walkthrough Script (15-Point Demonstration)

This guide provides a step-by-step walkthrough for evaluating the complete Karuthal backend and its integrated decision-support capabilities.

---

### Step 1: Health & Public Portal Baseline
1. Send `GET /health` -> Receives `{"status": "healthy"}`.
2. Send `GET /api/locations/districts` -> Returns all 14 official revenue districts of Kerala.

### Step 2: Location Integrity Validation
3. Send `GET /api/locations/panchayats?district_id=12` (Thiruvananthapuram) -> Receives sample panchayats (`Varkala`, `Kattakada`, etc.) marked `is_sample: true`.
4. Submit `POST /api/reports` with mismatched district and panchayat (e.g. `Thiruvananthapuram` with `Chavara`) -> Backend rejects with `422 Unprocessable Content` and clear error message.

### Step 3: Anonymous Child-Protection Submission
5. Submit valid public report via `POST /api/reports`:
   - Category: `Neglect`
   - District: `Thiruvananthapuram`, Panchayat: `Varkala`
   - Receives unique case ID `KAR-XXXXXXXX`, status `Submitted`.

### Step 4: Privacy-Preserving Public Case Check
6. Send unauthenticated `GET /api/reports/{case_id}` -> Returns minimal status view (`case_id`, `district`, `status`, `created_at`). Raw citizen narrative and confidential notes are strictly omitted.

### Step 5: Officer Authentication & Throttling
7. Submit 5 invalid passwords to `POST /api/login` for `DCPU-TVM-01` -> 6th attempt is throttled with `429 Too Many Requests`.
8. Login with correct password -> Receives 8-hour JWT token, officer name (`Anjali Nair`), and district (`Thiruvananthapuram`).

### Step 6: Real-Time Polling Dashboard
9. Send `GET /api/dashboard?district=Thiruvananthapuram` with Bearer token -> Returns computed real-time counts (`total`, `solved`, `pending`, `urgent`) and UI-ready reports and emergency calls.

### Step 7: Strict District Scope Enforcement
10. Send `GET /api/dashboard?district=Kollam` using Thiruvananthapuram officer token -> Blocked with `403 Forbidden` (`Case or resource is outside your assigned district scope`).

### Step 8: Case Assignment Workflow
11. DCPU Officer assigns case via `POST /api/cases/{case_id}/assign` to active TVM field officer (`FO-TVM-01`, Rahul Varma) -> Case status automatically advances to `Assigned`.

### Step 9: Field Assessment Visit
12. Authenticated Field Officer submits visit via `POST /api/cases/{case_id}/field-visits` (Outcome: `Needs support services`, zero GPS coordinates captured) -> Status advances to `Visit Recorded`.

### Step 10: Multi-Agency Service Referral
13. Officer registers referral via `POST /api/cases/{case_id}/referrals` (Service: `Child Welfare Committee (CWC)`) -> Returns referral card with `confirmed: false` and explicit prototype legal notice.

### Step 11: Emergency Alert Registration & Conflict Handling
14. Log emergency alert via `POST /api/emergency` -> Status is `Active` with disclaimer.
15. Patch call via `PATCH /api/emergency/{id}` to `Resolved`. A second attempt to update returns `409 Conflict` (cannot alter resolved call).

### Step 12: Chronological Audit Trail Inspection
16. Retrieve `GET /api/cases/{case_id}/history` -> Returns chronological chain of custody (`Report Submitted` -> `Case Assigned` -> `Field Visit Recorded` -> `Referral Created`).

### Step 13: Deterministic Rule-Based AI Summary
17. Request `POST /api/cases/{case_id}/ai-summary` -> Returns decision-support summary labelled `unverified`, missing information checklist, and aggregate statistical hints without modifying case status.

### Step 14: Report Resolution
18. Patch report via `PATCH /api/report/{id}` with `{"status": "Solved"}` -> Status updated to `Solved`, `solved_at` timestamp recorded.

### Step 15: Cross-Restart Data Persistence
19. Stop backend process, restart server, query database -> Case records, referrals, and audit trails remain intact.

### Step 16: Privacy-Consented Location Routing & District Case Map (Stage 11)
20. Submit report with GPS coordinates (`8.73654`, `76.71892`) and `location_consent: true`.
21. Verify officer retrieves `GET /api/cases/{case_id}/location`:
    - Coordinates are rounded to 2 decimal places (`8.74`, `76.72`, approx 1 km).
    - Response clearly indicates `"simulated": true`.
    - History log writes `location_viewed` without exposing raw coordinates.
22. Officer queries `GET /api/dashboard/map?district=Thiruvananthapuram` -> Receives standard GeoJSON `FeatureCollection` for mapping without exposing citizen identity.
23. Cross-district check: Kollam officer (`DCPU-KLM-01`) queries the TVM location -> Immediately rejected with `403 Forbidden`.

### Step 17: Simulated VoIP Call Session Lifecycle (Stage 12)
24. Reporter uses `reporter_token` from submission to request callback: `POST /api/reports/{case_id}/callback-request` (status: `requested`).
25. Assigned officer initiates or answers call: `POST /api/cases/{case_id}/calls` (status advances to `ringing`).
26. Reporter accepts incoming ring: `POST /api/calls/{call_id}/accept` with `X-Reporter-Token` (status advances to `connected`).
27. Officer requests single-use WebSocket ticket: `POST /api/calls/{call_id}/ws-ticket` (valid for 60 seconds).
28. Officer connects to `WS /api/calls/{call_id}/signal?ticket=...` for peer signalling.
29. Either party terminates call: `POST /api/calls/{call_id}/end` -> status advances to `ended`, `duration_seconds` calculated, `notice` verifies simulated prototype status.

---

## Limitations

- **Prototype Demonstration**: Karuthal is a demonstration prototype designed for academic review and technical feasibility evaluation.
- **No Emergency Services Contact**: The platform does not place calls to 1098, 112, or law enforcement agencies.
- **Legal Review Pending**: Live implementation mandates formal compliance audits under the Juvenile Justice Act and Digital Personal Data Protection Act (DPDP) 2023.
