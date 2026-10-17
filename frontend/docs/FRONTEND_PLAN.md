# Karuthal Frontend Architecture & Integration Plan

## 1. Overview
This document outlines the API integration strategy for the React + Vite frontend of the Karuthal prototype, aligned against the FastAPI backend specification in `docs/backend_reference/API_CONTRACT.md`.

---

## 2. API Contract Mapping

| Frontend View / Feature | Backend Endpoint | HTTP Method | Expected Request Payload / Headers | Expected Response Shape | Status / Handling |
|---|---|---|---|---|---|
| **Location Dropdowns** | `/api/locations/districts` | `GET` | None | `[{id, name, code}, ...]` | Exact match |
| **Panchayat Dropdowns** | `/api/locations/panchayats?district_id=` | `GET` | `district_id` query param | `[{id, district_id, name, is_sample}, ...]` | Exact match |
| **Citizen Report Form** | `/api/reports` | `POST` | `{district, panchayat, category, description, is_urgent, location_text?, ward?, approx_lat?, approx_lng?, location_consent?, location_source?}` | `{message, reporter_token, report: {case_id, id, routed_district, has_location, ...}}` | Save `reporter_token` in `sessionStorage` |
| **Officer Authentication**| `/api/login` | `POST` | `{login, password}` | `{token, name, district}` | Store in `localStorage`, set active district |
| **Officer Dashboard** | `/api/dashboard?district=` | `GET` | `Authorization: Bearer <token>` | `{total, solved, pending, urgent, reports[], calls[]}` | Poll every 5s; pause on tab hidden |
| **Mark Case Solved** | `/api/report/:id` | `PATCH` | `Authorization: Bearer <token>`, `{status: "Solved"}` | `{id, case_id, status: "Solved", solved_at}` | Must use numeric database `id` |
| **Emergency Patch** | `/api/emergency/:id` | `PATCH` | `Authorization: Bearer <token>`, `{status, notes?}` | `{id, call_ref, status, ...}` | Numeric `id` (e.g. 1) |
| **Case Detail & History** | `/api/cases/:case_id` & `/api/cases/:case_id/history` | `GET` | `Authorization: Bearer <token>` | Scoped operational case file & audit array | Exact match |
| **Case Location** | `/api/cases/:case_id/location` | `GET` | `Authorization: Bearer <token>` | `{district, panchayat, ward, location_text, approx_lat, approx_lng, location_consent, simulated: true}` | Logs `location_viewed` in audit |
| **District Case Map** | `/api/dashboard/map?district=` | `GET` | `Authorization: Bearer <token>` | GeoJSON `FeatureCollection` | Plain SVG pins (no API key required) |
| **Callback Request** | `/api/reports/:id/callback-request` | `POST` | `X-Reporter-Token: <token>` | `{call: {id, status: "requested", ...}, simulated: true, notice}` | Anonymous citizen initiation |
| **Case Calls List** | `/api/cases/:id/calls` | `GET` | `Authorization: Bearer <token>` | `{count, calls[], simulated: true}` | Officer view |
| **Officer Call Start** | `/api/cases/:id/calls` | `POST` | `Authorization: Bearer <token>`, `{override_solved: bool}` | `{call: {id, status: "ringing", ...}, simulated: true}` | Advances to `ringing` |
| **Call Accept/Decline** | `/api/calls/:id/accept` & `/decline` | `POST` | Bearer token OR `X-Reporter-Token` | `{call: {id, status: "connected"\|"declined", ...}}` | Participant scoped |
| **Call End** | `/api/calls/:id/end` | `POST` | Bearer token OR `X-Reporter-Token` | `{call: {id, status: "ended", duration_seconds, ...}}` | Computes duration |
| **WebSocket Ticket** | `/api/calls/:id/ws-ticket` | `POST` | Bearer token OR `X-Reporter-Token` | `{ticket, expires_in: 60, simulated: true}` | Prevents token in query URL |
| **Signalling Channel** | `/api/calls/:id/signal?ticket=` | `WS` | Single-use ticket query param | JSON `{peer_joined, offer, answer, ice}` | Peer-to-peer relay |

---

## 3. Discrepancies & Resolutions

1. **Standardized Error Handling**: Backend returns errors strictly as `{"message": "<description>"}` (with fallback to `detail`). The API helper parses `data.message || data.detail || data.error`.
2. **District Name Integrity**: The backend seeds Kerala's 14 official revenue districts (`Thiruvananthapuram`, `Kollam`, `Pathanamthitta`, `Alappuzha`, `Kottayam`, `Idukki`, `Ernakulam`, `Thrissur`, `Palakkad`, `Malappuram`, `Kozhikode`, `Wayanad`, `Kannur`, `Kasaragod`). Dropdowns fetch directly from `/api/locations/districts` to eliminate spelling mismatches.
3. **Numeric vs KAR ID in Mutations**: Dashboard status mutation uses `/api/report/{numeric_id}`, whereas case detail inspection uses `/api/cases/{case_id}` (e.g. `KAR-XXXXXXXX`). Both IDs are mapped properly from the dashboard response.
4. **Prototype Disclaimers**: All call and location screens display `"SIMULATED PROTOTYPE"` banners and render the backend `"notice"` string.
