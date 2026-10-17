# How to Run Karuthal (Backend + Frontend)

This guide provides the exact steps to launch the Karuthal FastAPI backend and the React + Vite frontend together.

---

## 1. Prerequisites

- Python 3.12 (using `.venv312` located in `backend/`)
- Node.js (v18+ or v24+) & npm

---

## 2. Terminal 1: Seed Demo Data & Start Backend Server (Port 8000)

Open PowerShell in the project root:

```powershell
cd C:\Users\Sreddha\KARUTHAL\backend
.\.venv312\Scripts\Activate.ps1
python scripts\seed_demo.py
python -m uvicorn main:app --reload --port 8000
```

- Backend URL: `http://127.0.0.1:8000`
- Health check: `http://127.0.0.1:8000/health`
- Swagger Docs: `http://127.0.0.1:8000/docs`

---

## 3. Terminal 2: Start the Frontend Application (Vite Dev Server)

Open a second PowerShell terminal in the project root:

```powershell
cd C:\Users\Sreddha\KARUTHAL\frontend
npm run dev
```

- Frontend URL: `http://localhost:5173`
- The frontend connects to the backend at `http://127.0.0.1:8000` (configured via `VITE_API_BASE_URL` in `frontend/.env`).

---

## 4. Demo Officer Accounts (for Testing & Evaluation)

Use the seeded officer credentials from `backend/docs/DEMO_SCRIPT.md`:

| Officer Role | Revenue District | Officer Code / Login |
|---|---|---|
| **DCPU Officer** | Thiruvananthapuram | `DCPU-TVM-01` |
| **Field Officer** | Thiruvananthapuram | `FO-TVM-01` |
| **DCPU Officer** | Kollam | `DCPU-KLM-01` |

*(Password: Use your configured `DEMO_OFFICER_PASSWORD` from your environment. Password is not hard-coded in UI or documentation).*

---

## 5. Prototype Safety Notice

- **SIMULATED PROTOTYPE ONLY**: Does not contact emergency helplines (1098, 112) or law enforcement.
- **Zero Audio Storage**: Voice call sessions simulate signalling and state management. No audio is recorded or stored.
- **Location Privacy**: GPS coordinates are rounded to ~1 km and purged after 90 days.

---

## 6. Language Note

- **Malayalam strings need review by a native speaker.**
