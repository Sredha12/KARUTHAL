# Karuthal Database Schema Architecture

The Karuthal database utilizes SQLAlchemy 2.x with declarative models, strict foreign key constraints, automated UTC timestamps, and composite indexing tailored for fast querying by district and status.

---

## Mermaid Entity-Relationship Diagram

```mermaid
erDiagram
    districts ||--o{ panchayats : contains
    districts ||--o{ reports : locates
    panchayats ||--o{ reports : localizes
    officers ||--o{ reports : solves
    officers ||--o{ emergency_calls : records
    officers ||--o{ assignments : receives
    officers ||--o{ assignments : assigns
    officers ||--o{ field_visits : conducts
    reports ||--o{ assignments : tracks
    reports ||--o{ field_visits : logs
    reports ||--o{ referrals : refers
    reports ||--o{ emergency_calls : links
    reports ||--o{ case_history : audits
    reports ||--o{ call_sessions : conducts
    officers ||--o{ call_sessions : answers

    districts {
        int id PK
        string name UK "14 Kerala Districts"
        string code UK
    }

    panchayats {
        int id PK
        int district_id FK
        string name
        boolean is_sample "True for demo data"
    }

    officers {
        int id PK
        string officer_code UK
        string email UK
        string name
        string password_hash
        string role "dcpu_officer, field_officer, admin"
        string district
        boolean is_active
        datetime created_at
    }

    reports {
        int id PK
        string report_id UK "KAR-XXXXXXXX"
        int district_id FK
        int panchayat_id FK
        string district
        string panchayat
        string category
        text description
        string status "Submitted, Under Review, Assigned, Visit Recorded, Referred, Solved"
        boolean is_urgent
        string location_text "Optional free text, max 200 chars"
        string ward "Optional ward identifier"
        float approx_lat "Rounded to 2 decimal places (~1km)"
        float approx_lng "Rounded to 2 decimal places (~1km)"
        boolean location_consent "True required to store coordinates"
        string location_source "typed, device, map_pick"
        string routed_district "Server-set district copy"
        string reporter_token_hash "Bcrypt hash of reporter token"
        datetime created_at
        datetime updated_at
        datetime solved_at
        int solved_by FK
    }

    assignments {
        int id PK
        int report_id FK
        int assigned_to_id FK
        int assigned_by_id FK
        text notes
        boolean is_active
        datetime created_at
    }

    field_visits {
        int id PK
        int report_id FK
        int field_officer_id FK
        datetime visit_at
        string outcome
        text notes
        datetime created_at
    }

    referrals {
        int id PK
        int report_id FK
        string district
        string concern_category
        string urgency
        string status "New, Pending review, Under review, Follow-up due, Closed"
        string next_action
        datetime follow_up_due
        string service
        string service_state "Draft, Referred, Engaged, Completed"
        text notes
        int created_by_id FK
        datetime created_at
        datetime updated_at
    }

    emergency_calls {
        int id PK
        string call_ref UK "CALL-XXXXXXXX"
        string district
        string category
        string description
        int related_report_id FK
        string status "Active, Acknowledged, Resolved"
        text notes
        datetime created_at
        datetime updated_at
        int recorded_by FK
    }

    case_history {
        int id PK
        string entity_type "report, case, emergency_call, referral, call_session"
        int entity_id
        int report_id FK
        string action
        string details "Non-sensitive operational event metadata"
        int actor_officer_id FK
        datetime created_at
    }

    call_sessions {
        int id PK
        int case_id FK
        string requested_by "reporter, officer"
        int officer_id FK
        string status "requested, ringing, connected, ended, declined, missed, cancelled"
        datetime created_at
        datetime ringing_at
        datetime connected_at
        datetime ended_at
        string end_reason "normal, declined, missed, cancelled"
        int duration_seconds
        string mode "simulated, webrtc"
        boolean simulated "Always true in prototype"
    }
```

---

## Architectural Principles

1. **Unified Case Entity**: Reports and Cases share the same physical database table (`reports`). A case *is* a report row progressing through defined operational states.
2. **Zero Sensitive Audit**: `case_history` never records citizen descriptions, child names, contact numbers, or credentials. It references IDs and operational action labels only.
3. **Location Privacy & Retention**: Coordinates are rounded to 2 decimal places (~1 km precision) before storage and discarded if consent is false. Coordinates are subject to a retention period (`LOCATION_RETENTION_DAYS`, default 90 days) via `apply_location_retention_policy()`.
4. **Anonymous Reporter Token**: Reporters authenticate callbacks via `report_id` + `X-Reporter-Token`. Only the bcrypt hash (`reporter_token_hash`) is persisted; the plain token is returned once upon report submission and never logged.
5. **No Call Recording**: `call_sessions` records metadata only (timestamps, duration, participant role, end reason). Audio is neither transmitted to real telecom networks nor recorded/transcribed.
6. **Compound Query Indexes**:
   - `ix_reports_district_status`: accelerates real-time polling on `/api/dashboard`.
   - `ix_calls_district_status`: accelerates emergency alert queries.
   - `ix_call_sessions_case_status`: accelerates active call verification and history queries.
   - `ix_panchayats_district_name`: validates district-panchayat integrity efficiently.
7. **PostgreSQL Compatibility**: SQLite is used for local development via WAL mode and foreign key pragmas; all data types and constraints cleanly migrate to PostgreSQL without schema modifications.

---

## Limitations

- **Prototype Prototype Only**: Designed for academic demonstration of privacy-preserving case support workflows. Not cleared for production deployment or handling live cases.
- **Legal Compliance**: Operational use requires formal legal audits under the Juvenile Justice Act, Protection of Children from Sexual Offences (POCSO) Act, and the Digital Personal Data Protection (DPDP) Act 2023.
- **Telephony & Signalling**: Real-world voice callbacks require certified telecommunication infrastructure, secure STUN/TURN clusters, and legal consent mechanisms.
