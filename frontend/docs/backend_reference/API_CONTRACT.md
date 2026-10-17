# Karuthal API Contract & Endpoint Reference

> **Prototype Notice**: Karuthal is a decision-support prototype for authorized child-protection personnel in Kerala. It does not contact police, DCPU, 112, 1098, or external agencies automatically.

| Method | Endpoint | Description | Status | Auth Required | Scope Enforced |
|---|---|---|---|---|---|
| `GET` | `/` | Service root and health check | Implemented | None | None |
| `GET` | `/health` | Health status ping (`{"status": "healthy"}`) | Implemented | None | None |
| `POST` | `/api/login` | Officer authentication (email/code + password) | Implemented | None (Rate-limited) | Public |
| `GET` | `/api/auth/me` | Officer profile & active jurisdiction | Implemented | Bearer Token | Authenticated |
| `GET` | `/api/locations/districts` | Kerala's 14 official revenue districts | Implemented | None | Public |
| `GET` | `/api/locations/panchayats` | Sample administrative panchayats by district | Implemented | None | Public |
| `POST` | `/api/reports` | Submit child-protection report (KAR-XXXXXXXX) | Implemented | None | Public |
| `GET` | `/api/reports` | List submitted reports | Implemented | None | Public |
| `GET` | `/api/reports/{case_id}` | Public case lookup (minimal status view) | Implemented | None (Officer gets full) | Scoped |
| `GET` | `/api/cases` | Filterable cases list | Implemented | Bearer Token | Scoped (DCPU/FO) |
| `GET` | `/api/cases/{case_id}` | Detailed operational case file | Implemented | Bearer Token | Scoped |
| `PATCH` | `/api/cases/{case_id}/status` | Update workflow status (Submitted -> Solved) | Implemented | Bearer Token | Scoped |
| `POST` | `/api/cases/{case_id}/assign` | Assign case to active district field officer | Implemented | Bearer Token (DCPU/Admin)| District Scoped |
| `GET` | `/api/assignments` | List assignments by case or district | Implemented | Bearer Token | District Scoped |
| `POST` | `/api/cases/{case_id}/field-visits`| Log on-site assessment visit (no GPS) | Implemented | Bearer Token (Assigned FO)| Case Scoped |
| `GET` | `/api/cases/{case_id}/field-visits` | List recorded field visits for case | Implemented | Bearer Token | Scoped |
| `POST` | `/api/cases/{case_id}/referrals` | Record multi-agency service referral | Implemented | Bearer Token | Scoped |
| `GET` | `/api/cases/{case_id}/referrals` | List case referrals | Implemented | Bearer Token | Scoped |
| `PATCH` | `/api/referrals/{id}` | Update referral status or service state | Implemented | Bearer Token (DCPU/Admin)| District Scoped |
| `GET` | `/api/dcpu/dashboard` | DCPU caseload overview & referral cards | Implemented (Proposed)| Bearer Token | District Scoped |
| `GET` | `/api/dashboard` | Real-time officer dashboard stats & items | Implemented (Frontend) | Bearer Token | District Scoped |
| `PATCH` | `/api/report/{id}` | Numeric DB ID report status patch | Implemented (Frontend) | Bearer Token | District Scoped |
| `POST` | `/api/emergency` | Log urgent alert (CALL-XXXXXXXX) | Implemented | Optional Bearer | Public / Officer |
| `GET` | `/api/emergency/{id}` | Retrieve emergency event details | Implemented | Bearer Token | District Scoped |
| `PATCH` | `/api/emergency/{id}` | Numeric DB ID alert status patch | Implemented (Frontend) | Bearer Token | District Scoped |
| `GET` | `/api/cases/{case_id}/history`| Chronological privacy-preserving audit trail | Implemented | Bearer Token | Scoped |
| `POST` | `/api/cases/{case_id}/ai-summary` | Deterministic decision-support AI summary | Implemented | Bearer Token (DCPU/Admin)| District Scoped |
| `GET` | `/api/cases/{case_id}/location` | Consented case location (simulated prototype) | Implemented (Stage 11) | Bearer Token | District Scoped |
| `GET` | `/api/dashboard/map` | District GeoJSON map of consented cases | Implemented (Stage 11) | Bearer Token | District Scoped |
| `POST` | `/api/reports/{id}/callback-request` | Anonymous reporter requests voice callback | Implemented (Stage 12) | `X-Reporter-Token` Header | Case Token Scoped |
| `GET` | `/api/cases/{case_id}/calls` | List voice call sessions for case | Implemented (Stage 12) | Bearer Token | District Scoped |
| `POST` | `/api/cases/{case_id}/calls` | Officer starts/answers voice session | Implemented (Stage 12) | Bearer Token | District Scoped |
| `GET` | `/api/calls/ice-config` | STUN/TURN ICE config for WebRTC path | Implemented (Stage 12) | Optional Bearer | Participant / Officer |
| `GET` | `/api/calls/{call_id}` | Participant call status inspection | Implemented (Stage 12) | Bearer or `X-Reporter-Token` | Participant Scoped |
| `POST` | `/api/calls/{call_id}/accept` | Accept incoming ringing session | Implemented (Stage 12) | Bearer or `X-Reporter-Token` | Participant Scoped |
| `POST` | `/api/calls/{call_id}/decline` | Decline incoming ringing session | Implemented (Stage 12) | Bearer or `X-Reporter-Token` | Participant Scoped |
| `POST` | `/api/calls/{call_id}/end` | Terminate session & calculate duration | Implemented (Stage 12) | Bearer or `X-Reporter-Token` | Participant Scoped |
| `POST` | `/api/calls/{call_id}/ws-ticket` | Single-use 60s WebSocket auth ticket | Implemented (Stage 12) | Bearer or `X-Reporter-Token` | Participant Scoped |
| `WS` | `/api/calls/{call_id}/signal` | Real-time WebRTC/simulated signalling relay | Implemented (Stage 12) | Query Ticket (`ticket=...`) | Participant Scoped |

---

## Detailed Payload Specifications

### 1. Authentication: `POST /api/login`
- **Request Body:**
  ```json
  {
    "login": "DCPU-TVM-01",
    "password": "DemoOfficerPassword2026!"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "token": "eyJhbGciOiJIUzI1NiIsIn...",
    "name": "Anjali Nair",
    "district": "Thiruvananthapuram"
  }
  ```
- **Error (401 Unauthorized):**
  ```json
  {
    "message": "Invalid credentials. Please verify your officer code/email and password."
  }
  ```

---

### 2. Officer Dashboard: `GET /api/dashboard?district=Thiruvananthapuram`
Polled by the frontend dashboard every 3 seconds.
- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):**
  ```json
  {
    "total": 12,
    "solved": 3,
    "pending": 9,
    "urgent": 2,
    "reports": [
      {
        "id": 105,
        "case_id": "KAR-8B2A91F4",
        "report_id": "KAR-8B2A91F4",
        "status": "Submitted",
        "category": "Neglect",
        "abuse_type": "Neglect",
        "panchayat": "Varkala",
        "location": "Varkala",
        "district": "Thiruvananthapuram",
        "description": "Child reported unattended near marketplace.",
        "is_urgent": true,
        "created_at": "2026-10-17T04:15:00+00:00",
        "updated_at": "2026-10-17T04:15:00+00:00",
        "solved_at": null
      }
    ],
    "calls": [
      {
        "id": 42,
        "call_id": "CALL-A1F290BC",
        "call_ref": "CALL-A1F290BC",
        "status": "Active",
        "category": "Immediate protection",
        "district": "Thiruvananthapuram",
        "description": "Distressed youth seeking assistance.",
        "notes": "",
        "created_at": "2026-10-17T04:20:00+00:00",
        "updated_at": "2026-10-17T04:20:00+00:00",
        "related_report_id": 105
      }
    ]
  }
  ```

---

### 3. Report Status Patch: `PATCH /api/report/{id}`
- **URL Param:** `{id}` = Numeric database ID (e.g. `105`)
- **Request Body:**
  ```json
  {
    "status": "Solved"
  }
  ```
- **Response (200 OK):** Updated report object with `solved_at` populated.

---

### 4. Emergency Status Patch: `PATCH /api/emergency/{id}`
- **URL Param:** `{id}` = Numeric call database ID (e.g. `42`)
- **Request Body:**
  ```json
  {
    "status": "Acknowledged",
    "notes": "Field worker notified."
  }
  ```
- **Response (200 OK):** Updated emergency call object.
- **Conflict (409 Conflict):** If status is already `Resolved`.

---

### 5. Consented Case Location: `GET /api/cases/{case_id}/location`
- **Headers:** `Authorization: Bearer <officer_token>`
- **Response (200 OK):**
  ```json
  {
    "district": "Thiruvananthapuram",
    "panchayat": "Varkala",
    "ward": "Ward 3",
    "location_text": "Near the primary health sub-centre",
    "approx_lat": 8.74,
    "approx_lng": 76.72,
    "location_consent": true,
    "location_source": "device",
    "simulated": true
  }
  ```
- **Audit:** Records `location_viewed` in case history (never logging coordinates).

---

### 6. District Case Map (GeoJSON): `GET /api/dashboard/map?district=Thiruvananthapuram`
- **Headers:** `Authorization: Bearer <officer_token>`
- **Response (200 OK):**
  ```json
  {
    "type": "FeatureCollection",
    "district": "Thiruvananthapuram",
    "features": [
      {
        "type": "Feature",
        "geometry": {
          "type": "Point",
          "coordinates": [76.72, 8.74]
        },
        "properties": {
          "report_id": "KAR-8B2A91F4",
          "status": "Submitted",
          "is_urgent": true,
          "panchayat": "Varkala"
        }
      }
    ],
    "simulated": true
  }
  ```

---

### 7. VoIP Call Sessions: Lifecycle & Signalling
- **Callback Request:** `POST /api/reports/{case_id}/callback-request`
  - **Header:** `X-Reporter-Token: <token_from_report_creation>`
  - **Response (201 Created):**
    ```json
    {
      "call": {
        "id": 12,
        "case_id": 105,
        "report_id": "KAR-8B2A91F4",
        "requested_by": "reporter",
        "status": "requested",
        "simulated": true,
        "notice": "Simulated prototype call. No real helpline or authority is contacted."
      },
      "simulated": true,
      "notice": "Simulated prototype call. No real helpline or authority is contacted."
    }
    ```
- **Officer Initiate/Answer Call:** `POST /api/cases/{case_id}/calls`
  - **Headers:** `Authorization: Bearer <token>`
  - **Body:** `{"override_solved": false}`
  - **Response (201 Created / 200 OK):** Transitions to `ringing`.
- **Accept Call:** `POST /api/calls/{call_id}/accept`
  - **Headers:** `Authorization: Bearer <token>` OR `X-Reporter-Token: <token>`
  - **Response (200 OK):** Transitions to `connected`.
- **End Call:** `POST /api/calls/{call_id}/end`
  - **Response (200 OK):** Transitions to `ended` with computed `duration_seconds`.
- **Single-Use WebSocket Ticket:** `POST /api/calls/{call_id}/ws-ticket`
  - **Response (200 OK):** `{"ticket": "...", "expires_in": 60, "simulated": true}`
- **Signalling Channel:** `WS /api/calls/{call_id}/signal?ticket=<ticket>`
  - Relays WebRTC/simulated JSON peer-to-peer between the 2 participants only.

---

## Limitations

1. **Prototype Decision-Support System**: Karuthal is an academic and technical prototype intended exclusively to demonstrate assistive tools for authorized personnel. It is not approved for live deployment.
2. **Not Legally Compliant**: Real deployment in India requires comprehensive legal reviews under the Juvenile Justice (Care and Protection of Children) Act, POCSO Act, Digital Personal Data Protection Act (DPDP), and relevant state welfare regulations.
3. **Simulated Telephony and Audio**: The system does not contact emergency helplines (1098, 112) or police dispatch. Voice call sessions are simulated or WebRTC signalling demonstrations. No voice audio, recording, or audio interception is stored.
4. **Security & Cryptography**: In-memory rate limiting and single-server WebSocket relays require distributed infrastructure (Redis, Redis pub/sub) and a rigorous third-party penetration test and security audit before processing real data.
