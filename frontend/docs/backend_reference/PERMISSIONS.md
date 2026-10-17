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
| `GET /api/cases/{case_id}/location` | Denied (401) | Assigned Only | District Only | Statewide | District scoped; logs location_viewed |
| `GET /api/dashboard/map` | Denied (401) | Scoped | Scoped | Statewide | District scoped; no citizen identity |
| `POST /api/reports/{id}/callback-request` | Allowed with valid `X-Reporter-Token` | Allowed with token | Allowed with token | Allowed with token | Token scoped (per case per day rate limit) |
| `GET /api/cases/{case_id}/calls` | Denied (401) | Assigned Only | District Only | Statewide | District scoped |
| `POST /api/cases/{case_id}/calls` | Denied (401) | Assigned Only | District Only | Statewide | District scoped; override required for solved |
| `GET /api/calls/{call_id}` | Allowed with valid `X-Reporter-Token` | Allowed if assigned | Allowed if in district | Statewide | Participant scoped |
| `POST /api/calls/{call_id}/accept` | Allowed with valid `X-Reporter-Token` | Allowed if assigned | Allowed if in district | Statewide | Participant scoped |
| `POST /api/calls/{call_id}/decline` | Allowed with valid `X-Reporter-Token` | Allowed if assigned | Allowed if in district | Statewide | Participant scoped |
| `POST /api/calls/{call_id}/end` | Allowed with valid `X-Reporter-Token` | Allowed if assigned | Allowed if in district | Statewide | Participant scoped |
| `POST /api/calls/{call_id}/ws-ticket` | Allowed with valid `X-Reporter-Token` | Allowed if assigned | Allowed if in district | Statewide | Single-use 60s ticket |
| `WS /api/calls/{call_id}/signal` | Ticket Required | Ticket Required | Ticket Required | Ticket Required | Relays to other participant only |

---

## Location Privacy & Retention Policies

1. **Consent Enforced**: Geographic coordinates (`approx_lat`, `approx_lng`) are only accepted and stored if `location_consent: true` is explicitly provided. If consent is absent or false, coordinates are discarded immediately server-side.
2. **Privacy Rounding**: Consented coordinates are rounded to 2 decimal places (~1 km precision) before committing to the database. Exact GPS coordinates are never stored.
3. **Bounding Box Validation**: All coordinates must reside strictly within Kerala's geographic boundaries (Latitude: 8.1 to 12.9 N, Longitude: 74.8 to 77.5 E). Outside coordinates are rejected with `422 Unprocessable Content`.
4. **Retention Window**: Coordinates are stored for a maximum of `LOCATION_RETENTION_DAYS` (default: 90 days). The policy cleaner `apply_location_retention_policy(db)` nulls expired coordinates while preserving administrative area and ward metadata.
5. **Audit Logging**: Reading `/api/cases/{case_id}/location` logs a `location_viewed` audit event with officer ID and timestamp. Raw coordinates are never logged into the audit text.

---

## Audio and VoIP Call Policies

1. **Simulated Prototype Only**: Karuthal VoIP is a prototype demonstration. All API responses carry `"simulated": true` and the prototype disclaimer: `"Simulated prototype call. No real helpline or authority is contacted."`
2. **Zero Audio Recording**: No voice streams, recordings, transcripts, or telephone numbers are stored in any mode. The server relays signalling messages peer-to-peer and manages operational state transitions only.
3. **Anonymous Reporter Credentials**: Anonymous reporters authenticate using a randomly generated token (`reporter_token`) provided once at submission. Only its bcrypt hash is persisted. The token is never logged or exposed.
4. **Abuse and Rate Controls**: Maximum of `VOIP_MAX_CALLS_PER_CASE_PER_DAY` (default: 5 calls/day) allowed per case. Exactly one active call session can exist per case at any given time.

---

## Limitations

- **Not Production Ready**: Karuthal is an experimental prototype for academic and technical evaluation. It cannot be used in production or crisis response.
- **Legal Compliance**: Full legal and procedural clearance under Indian child-protection statutes (JJ Act, POCSO) and privacy laws (DPDP Act 2023) is required prior to real-world deployment.
- **Telephony & Real Helplines**: The prototype has no integration with 1098 (Childline), 112 (Emergency Response), or police dispatch networks.
