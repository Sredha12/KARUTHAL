# Frontend Handoff Guide for Karuthal Backend

This document details every endpoint provided by the Karuthal backend for the frontend team.

---

## Environment Setup
In your React/Vite frontend root, set:
```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```
All errors consistently return `{"message": "<friendly error description>"}`. Never expect or look for `res.data.detail`.

---

## 1. Locations
### `GET /api/locations/districts`
- **Request:** None
- **Response:**
  ```json
  [
    {"id": 1, "name": "Alappuzha", "code": "ALP"},
    {"id": 12, "name": "Thiruvananthapuram", "code": "TVM"}
  ]
  ```

### `GET /api/locations/panchayats?district_id=12`
- **Request:** `district_id` as query param
- **Response:**
  ```json
  [
    {"id": 55, "district_id": 12, "name": "Varkala", "is_sample": true},
    {"id": 56, "district_id": 12, "name": "Kattakada", "is_sample": true}
  ]
  ```

---

## 2. Public Reporting Form
### `POST /api/reports`
- **Request Body:**
  ```json
  {
    "district": "Thiruvananthapuram",
    "panchayat": "Varkala",
    "category": "Neglect",
    "description": "Observed child unattended during school hours near bus stand.",
    "is_urgent": false
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "message": "Demo report submitted successfully",
    "report": {
      "case_id": "KAR-8B2A91F4",
      "report_id": "KAR-8B2A91F4",
      "id": 105,
      "district": "Thiruvananthapuram",
      "panchayat": "Varkala",
      "location": "Varkala",
      "category": "Neglect",
      "abuse_type": "Neglect",
      "status": "Submitted",
      "is_urgent": false,
      "created_at": "2026-10-17T04:15:00+00:00"
    }
  }
  ```

---

## 3. Officer Authentication
### `POST /api/login`
- **Request Body:**
  ```json
  {
    "login": "DCPU-TVM-01",
    "password": "<DEMO_OFFICER_PASSWORD>"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ...",
    "name": "Anjali Nair",
    "district": "Thiruvananthapuram"
  }
  ```

---

## 4. Officer Dashboard Polling
### `GET /api/dashboard?district=Thiruvananthapuram`
- **Header:** `Authorization: Bearer <token>`
- **Response (200 OK):**
  ```json
  {
    "total": 5,
    "solved": 1,
    "pending": 4,
    "urgent": 1,
    "reports": [...],
    "calls": [...]
  }
  ```

### `PATCH /api/report/{id}`
- **URL Param:** `{id}` is numeric report ID (e.g., `105`)
- **Request Body:** `{"status": "Solved"}`
- **Response (200 OK):** Updated report object.

---

## 5. Case Assignment (DCPU / Admin)
### `POST /api/cases/{case_id}/assign`
- **Request Body:**
  ```json
  {
    "field_officer_id": 2,
    "notes": "Conduct welfare check at address."
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "message": "Case assigned successfully",
    "assignment": {
      "id": 1,
      "report_id": 105,
      "assigned_to_id": 2,
      "assigned_to_name": "Rahul Varma",
      "assigned_by_name": "Anjali Nair",
      "notes": "Conduct welfare check at address.",
      "is_active": true,
      "created_at": "2026-10-17T04:20:00+00:00"
    },
    "case_status": "Assigned"
  }
  ```

---

## 6. Field Visits (Assigned Field Officer)
### `POST /api/cases/{case_id}/field-visits`
- **Request Body:**
  ```json
  {
    "visit_at": "2026-10-17T11:00:00Z",
    "outcome": "Needs support services",
    "notes": "Caregivers consulted; food and education assistance recommended."
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "message": "Field visit recorded successfully",
    "field_visit": {
      "id": 1,
      "report_id": 105,
      "field_officer_name": "Rahul Varma",
      "visit_at": "2026-10-17T11:00:00+00:00",
      "outcome": "Needs support services",
      "notes": "Caregivers consulted; food and education assistance recommended."
    },
    "case_status": "Visit Recorded"
  }
  ```

---

## 7. Referrals & DCPU Dashboard
### `POST /api/cases/{case_id}/referrals`
- **Request Body:**
  ```json
  {
    "urgency": "Standard",
    "concern_category": "Neglect",
    "next_action": "Schedule child welfare committee review",
    "service": "Child Welfare Committee (CWC)",
    "notes": "Formal referral registered."
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "referral": {
      "id": 1,
      "caseRef": "KAR-8B2A91F4",
      "district": "Thiruvananthapuram",
      "concernCategory": "Neglect",
      "receivedAt": "17 Oct 2026",
      "urgency": "Standard",
      "status": "New",
      "nextAction": "Schedule child welfare committee review",
      "serviceLinkage": {
        "service": "Child Welfare Committee (CWC)",
        "state": "Referred"
      },
      "history": [...]
    },
    "confirmed": false,
    "disclaimer": "Prototype record only. Creating or updating this referral does NOT contact external agencies or services."
  }
  ```

---

## 8. AI Case Summary (DCPU / Admin)
### `POST /api/cases/{case_id}/ai-summary`
- **Response (200 OK):**
  ```json
  {
    "ai_generated": true,
    "verified": false,
    "human_review_required": true,
    "disclaimer": "AI-assisted prototype summary for authorized human decision-making only. Reported details are unverified allegations...",
    "case_id": "KAR-8B2A91F4",
    "structured_summary": "[Reported, Unverified Intake] A child-protection concern...",
    "missing_information": [
      "Formal verification of child identity and age documentation",
      "Direct assessment interview conducted by authorized child-protection officer"
    ],
    "tentative_timeline": [
      {"timestamp": "2026-10-17 04:15 UTC", "event": "Initial concern reported (unverified intake)"}
    ],
    "related_case_hints": [
      {
        "category": "Neglect",
        "district": "Thiruvananthapuram",
        "similar_cases_count": 4,
        "note": "Statistical count of historical reports in the same district..."
      }
    ]
  }
  ```

---

## 9. Chronological Case Audit Trail
### `GET /api/cases/{case_id}/history`
- **Response (200 OK):**
  ```json
  {
    "case_id": "KAR-8B2A91F4",
    "count": 3,
    "history": [
      {
        "id": 1,
        "action": "Report Submitted",
        "details": "Public report received via portal",
        "actor_name": null,
        "created_at": "2026-10-17T04:15:00+00:00"
      },
      {
        "id": 2,
        "action": "Case Assigned",
        "details": "Assigned to Rahul Varma (FO-TVM-01)",
        "actor_name": "Anjali Nair (dcpu_officer)",
        "created_at": "2026-10-17T04:20:00+00:00"
      }
    ]
  }
  ```
