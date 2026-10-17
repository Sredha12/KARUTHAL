# Role and District Scope Permissions Matrix

Karuthal enforces strict two-dimensional authorization:
1. **Functional Role**: Defines operational actions an officer is permitted to execute.
2. **Jurisdictional District Scope**: Restricts officer access exclusively to records situated within their assigned revenue district in Kerala. Changing an ID in a URL never grants access across district boundaries.

---

## Role Definitions

- `admin`: State-level administrator. Can access cases, reports, and emergency events across all 14 districts of Kerala. Permitted to reassign cases and review aggregate data.
- `dcpu_officer`: District Child Protection Unit officer. Has comprehensive oversight across their assigned district. Can review all district cases, assign field officers, manage multi-agency referrals, and generate AI case assistance summaries.
- `field_officer`: Ground-level child-protection officer. Has restricted access: **can only view and log visits for cases actively assigned to them** within their district.

---

## Endpoint Permission Matrix

| Endpoint / Action | Unauthenticated | Field Officer | DCPU Officer | State Admin | District Scope Rule |
|---|---|---|---|---|---|
| `GET /api/locations/districts` | Allowed | Allowed | Allowed | Allowed | Public statewide reference |
| `GET /api/locations/panchayats` | Allowed | Allowed | Allowed | Allowed | Public reference |
| `POST /api/reports` | Allowed | Allowed | Allowed | Allowed | Validates district-panchayat match |
| `GET /api/reports/{case_id}` | Minimal Status | Full (if in scope)| Full (if in scope)| Full (any) | Scoped if authenticated |
| `POST /api/login` | Allowed | Allowed | Allowed | Allowed | Rate limited (5/15 min) |
| `GET /api/auth/me` | Denied (401) | Allowed | Allowed | Allowed | Self profile only |
| `GET /api/dashboard` | Denied (401) | Scoped | Scoped | Any District | Must match officer's district |
| `PATCH /api/report/{id}` | Denied (401) | Scoped | Scoped | Any District | Must match officer's district |
| `GET /api/cases` | Denied (401) | Assigned Only | District Only | Statewide | FO sees assigned only; DCPU sees district |
| `GET /api/cases/{case_id}` | Denied (401) | Assigned Only | District Only | Any Case | FO sees assigned only; DCPU sees district |
| `PATCH /api/cases/{case_id}/status` | Denied (401) | Assigned Only | District Only | Any Case | FO sees assigned only; DCPU sees district |
| `POST /api/cases/{case_id}/assign` | Denied (401) | Denied (403) | Allowed | Allowed | Target FO must be in same district |
| `GET /api/assignments` | Denied (401) | Scoped | Scoped | Statewide | District scoped |
| `POST /api/cases/{case_id}/field-visits`| Denied (401) | Assigned Only | Denied (403) | Allowed | Only currently assigned FO |
| `GET /api/cases/{case_id}/field-visits` | Denied (401) | Assigned Only | District Only | Statewide | District scoped |
| `POST /api/cases/{case_id}/referrals` | Denied (401) | Assigned Only | District Only | Statewide | District scoped |
| `PATCH /api/referrals/{id}` | Denied (401) | Denied (403) | District Only | Statewide | District scoped |
| `GET /api/dcpu/dashboard` | Denied (401) | Denied (403) | District Only | Statewide | District scoped |
| `POST /api/emergency` | Allowed | Allowed | Allowed | Allowed | Validates Kerala district |
| `PATCH /api/emergency/{id}` | Denied (401) | Scoped | Scoped | Statewide | District scoped |
| `GET /api/cases/{case_id}/history` | Denied (401) | Assigned Only | District Only | Statewide | District scoped |
| `POST /api/cases/{case_id}/ai-summary` | Denied (401) | Denied (403) | District Only | Statewide | DCPU / Admin only |
