# Karuthal Backend Implementation Progress

## Project Overview
Karuthal is a privacy-conscious, AI-assisted child-protection case-support prototype designed for authorized human decision-making support in Kerala.
- Backend: FastAPI, SQLAlchemy 2.x, SQLite (dev) / PostgreSQL compatible
- Working Branch: `backend-officer-api`
- Python Environment: Python 3.12 (`.venv312`)

## Frontend Status Note
- The frontend (React 19 + Vite) is maintained in a separate repo/tree by the frontend teammate.
- This backend strictly conforms to the agreed API contracts defined in `OFFICER_PORTAL_INTEGRATION.md` and UI specifications from `officerApi.js`, `ReportsTable.jsx`, `EmergencyAlertCard.jsx`, `OfficerDashboard.jsx`, and `DcpuDashboard.jsx`.
- Frontend integration examples and handoff guides are documented in `docs/frontend_examples/` and `docs/FRONTEND_HANDOFF.md`.

## Stage Checklist

| Stage | Description | Status | Tests Passed | Notes / Key Decisions |
|---|---|---|---|---|
| Stage 0 | Project setup, venv312, git branch, pre-flight | Completed | - | Branch `backend-officer-api` created; pre-flight secret length verified programmatically. |
| Stage 1 | Foundation API & In-memory to DB migration | Completed | 6 / 6 | Root, health, public report creation, standardized error format `{"message": "..."}` verified. |
| Stage 2 | Locations (Districts & Panchayats) + Validated Public Reporting | Completed | 12 / 12 | 14 Kerala districts seeded; sample panchayats validated; minimal public view vs scoped officer view. |
| Stage 3 | Authentication, Roles, District Scope & Demo Seed | Completed | 18 / 18 | JWT auth, bcrypt, 15-min rate limiting, demo seeder verified idempotent. |
| Stage 4 | Cases, Status Workflow, Dashboard & Report Patch | Completed | 22 / 22 | Scoped cases query, status transitions, real-time dashboard counts, and numeric PATCH /api/report/{id}. |
| Stage 5 | Case Assignments | Completed | 26 / 26 | Scope-validated assignment to active field officers in same district; assignment history tracking. |
| Stage 6 | Field Visits | Completed | 28 / 28 | Assigned field officer visit logging; outcome enum; status set to "Visit Recorded"; no GPS/location tracking. |
| Stage 7 | Referrals & DCPU Dashboard Contract | Completed | 30 / 30 | Referral lifecycle; `confirmed: false` prototype notice; proposed DCPU dashboard endpoint. |
| Stage 8 | Emergency Calls & Case History Audit Trail | Completed | 32 / 32 | Active/Acknowledged/Resolved call lifecycle; disclaimer that authorities are not contacted; case history. |
| Stage 9 | Mock AI Case Summary | Completed | 33 / 33 | Deterministic rule-based summary; unverified label; no external API; disclaimer and human review required. |
| Stage 10 | Security Hardening, Full Documentation, Frontend Examples & Smoke Test | Completed | 39 / 39 | Security headers, contract mirroring test, docs, ready-to-use React components, live server smoke test passed. |
| Stage 11 | Reporter Location Routing & District GeoJSON Map | Completed | 45 / 45 | Kerala bounding box, coordinate rounding to ~1km, location_viewed audit, retention cleanup policy. |
| Stage 12 | VoIP Call Sessions (Simulated & WebRTC Signalling) | Completed | 56 / 56 | In-app voice state machine, ticketed WebSocket relay, reporter token auth, ring timeout, rate limits, live smoke test passed. |

## Decisions Made
1. **Locations & Panchayats**: Kerala's 14 official revenue districts are seeded. Panchayats are provided with clearly marked fictional/sample records for development and testing.
2. **Case Entity**: Following architecture instructions, `cases` and `reports` share the same database table `reports`. No redundant case table is introduced.
3. **Public vs Officer Case Detail**: Public lookup `/api/reports/{case_id}` returns a minimal sanitized view (`case_id`, `status`, `created_at`, `district`). Full sensitive details are restricted to authenticated officers in scope via `/api/cases/{case_id}`.
4. **Referrals & DCPU Dashboard**: DCPU dashboard response shape is implemented as proposed (`{overview: {...}, referrals: [...]}`) with explicit documentation for teammate sign-off.
5. **Rate Limiting**: Auth throttling is handled in-memory per login identifier (5 failures / 15 minutes) and noted as a prototype limitation.
6. **Location Privacy**: GPS coordinates rounded to 2 decimal places (~1 km) server-side prior to storage; dropped if consent is not granted; subject to a 90-day retention cleanup.
7. **VoIP Simulation & Zero Audio Recording**: Call sessions are simulated by default with WebRTC signalling option for demo; audio is never recorded, intercepted, or saved.

---

## Limitations

- **Experimental Prototype**: Karuthal is an academic and technical prototype built for authorized human decision-making support.
- **Not Cleared for Production**: Requires formal legal reviews under Indian child welfare laws (POCSO, Juvenile Justice Act) and data protection statutes (DPDP Act 2023).
- **Simulated External Helplines**: System does not dispatch police, Childline (1098), or emergency services (112).
