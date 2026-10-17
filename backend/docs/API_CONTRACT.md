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
