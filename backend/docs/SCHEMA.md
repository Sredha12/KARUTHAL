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
        string entity_type "report, case, emergency_call, referral"
        int entity_id
        int report_id FK
        string action
        string details "Non-sensitive operational event metadata"
        int actor_officer_id FK
        datetime created_at
    }
```

---

## Architectural Principles

1. **Unified Case Entity**: Reports and Cases share the same physical database table (`reports`). A case *is* a report row progressing through defined operational states.
2. **Zero Sensitive Audit**: `case_history` never records citizen descriptions, child names, contact numbers, or credentials. It references IDs and operational action labels only.
3. **Compound Query Indexes**:
   - `ix_reports_district_status`: accelerates real-time polling on `/api/dashboard`.
   - `ix_calls_district_status`: accelerates emergency alert queries.
   - `ix_panchayats_district_name`: validates district-panchayat integrity efficiently.
4. **PostgreSQL Compatibility**: SQLite is used for local development via WAL mode and foreign key pragmas; all data types and constraints cleanly migrate to PostgreSQL without schema modifications.
