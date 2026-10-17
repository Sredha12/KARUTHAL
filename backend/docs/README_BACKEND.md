# Karuthal Backend Service (FastAPI)

> **Child-Protection Case-Support Prototype for Kerala**  
> Karuthal supports authorized human decision-makers. It never decides guilt, liability, or abuse severity, does not automate case closure or escalation, and does not contact police or external agencies automatically.

---

## 1. Quickstart (Windows PowerShell)

Ensure you are in the `backend/` directory:
```powershell
cd C:\Users\Sreddha\KARUTHAL\backend
```

### Run Tests
```powershell
.venv312\Scripts\python.exe -m pytest -q
```

### Seed Demo Accounts & Data (Idempotent)
```powershell
.venv312\Scripts\python.exe scripts/seed_demo.py
```

### Start Development Server
```powershell
.venv312\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
- API Docs (Swagger UI): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 2. Seeded Demo Accounts

All demo accounts use the fictional password provided in `DEMO_OFFICER_PASSWORD` in your `.env`.

| Role | Officer Code | Email | District | Description |
|---|---|---|---|---|
| DCPU Officer | `DCPU-TVM-01` | `dcpu.tvm@karuthal.demo` | Thiruvananthapuram | District unit coordinator |
| Field Officer | `FO-TVM-01` | `fo.tvm@karuthal.demo` | Thiruvananthapuram | Assigned field caseworker |
| DCPU Officer | `DCPU-KLM-01` | `dcpu.klm@karuthal.demo` | Kollam | Cross-district comparison account |
| Field Officer | `FO-KLM-01` | `fo.klm@karuthal.demo` | Kollam | Cross-district comparison account |
| DCPU Officer | `DCPU-EKM-01` | `dcpu.ekm@karuthal.demo` | Ernakulam | Central zone account |
| DCPU Officer | `DCPU-KKD-01` | `dcpu.kkd@karuthal.demo` | Kozhikode | North zone account |
| Administrator | `ADMIN-01` | `admin@karuthal.demo` | Thiruvananthapuram | Statewide administrative reviewer |

---

## 3. Privacy & Security Architecture: Implemented vs. Future

| Feature / Control | Current Prototype Implementation | Future Production Requirement |
|---|---|---|
| **Data Minimization** | Strictly fictional data; no child names, phone numbers, or photos stored in DB or logs. | Full legal compliance review with DPDP Act (India) and POCSO data handling norms. |
| **Token Storage** | PyJWT with 8-hour expiry; Bearer Authorization header (localStorage in demo UI). | HttpOnly, SameSite=Strict cookies with rotating refresh tokens and server revocation. |
| **Transport Security** | Security headers middleware (`nosniff`, `DENY`, `HSTS`); local HTTP for dev. | Mandatory HTTPS/TLS 1.3 across all endpoints with automated certificate management. |
| **Audit Trails** | Chronological `case_history` logging actions and actor IDs without sensitive text. | Tamper-evident append-only ledger with cryptographic hash chains and immutable storage. |
| **AI Safeguards** | Fully deterministic rule-based generator; strict `unverified` and `human-review` labels; zero external LLM API calls. | Monitored, specialized local on-premise model with explicit ethical review and prompt isolation. |
| **Data Retention** | Persistent SQLite / PostgreSQL database without scheduled deletion. | Automated data retention and disposal schedules complying with statutory requirements. |
| **Rate Limiting** | In-memory 5 failures / 15 min lockouts per login identifier. | Distributed Redis token-bucket limiter protecting all endpoints against denial of service. |
| **Database** | SQLite with WAL mode & foreign keys enabled (PostgreSQL-compatible schema). | High-availability PostgreSQL cluster with encrypted volumes at rest and connection pooling. |
