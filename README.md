# KARUTHAL
### CARE BEFORE CRISIS

**Organizing information. Supporting professionals. Putting child safety first.**

KARUTHAL is a child-protection support platform prototype designed to help authorized professionals organize reports, review case information, and coordinate follow-up through a centralized interface.

Developed for **She Builds Tech 3.0 — AI Hackathon**.

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Problem Statement](#-problem-statement)
- [Our Solution](#-our-solution)
- [Key Features](#-key-features)
- [System Workflow](#-system-workflow)
- [Technology Stack](#-technology-stack)
- [System Architecture](#-system-architecture)
- [Getting Started](#-getting-started)
- [Testing](#-testing)
- [Privacy and Responsible AI](#-privacy-and-responsible-ai)
- [Current Status](#-current-status)
- [Future Enhancements](#-future-enhancements)
- [Team](#-team)
- [Disclaimer](#-disclaimer)

## 🌱 Overview

Child-protection professionals may receive information from different sources and need to organize reports, review relevant details, and coordinate appropriate follow-up. Fragmented information and manual workflows can make this process challenging.

KARUTHAL explores how technology can support these workflows through structured reporting, district-based organization, case information management, and simulated communication features.

The platform is intended to support authorized professionals—not replace their judgment, established safeguarding procedures, or official child-protection systems.

## 🎯 Problem Statement

- Reports and concerns may arrive through different channels.
- Organizing information and maintaining case timelines can be time-consuming.
- Relevant information may be difficult to connect when records are fragmented.
- Location-based coordination may require additional effort.
- Child-related information requires careful access control and responsible handling.

## 💡 Our Solution

KARUTHAL aims to provide a centralized interface for submitting concerns and supporting authorized professionals in reviewing and organizing relevant case information.

The proposed approach combines:

- Structured public reporting.
- District-based information organization.
- An officer-facing dashboard.
- Case detail views.
- Simulated emergency and communication workflows.
- Advisory AI-assisted summaries, where implemented.

**Core principle:** Technology should assist human professionals in making informed decisions, never make safeguarding decisions autonomously.

## ✨ Key Features

### 1. Public Reporting
A reporting interface designed to collect relevant details about a child-safety concern.

### 2. District-Based Organization
A district selection interface and geographic visualization to support location-based organization.

### 3. Officer Dashboard
An interface for authorized officers to review submitted reports and access relevant case information.

### 4. Case Details
A structured view of individual reports intended to support review and follow-up.

### 5. Emergency Reporting Interface
A workflow designed to highlight concerns that may require urgent human attention. The prototype does not automatically contact a real helpline.

### 6. Simulated Communication Workflow
WebSocket-based signalling supports a simulated communication workflow. It does not place calls through the public telephone network.

### 7. Voice Input
Browser-based speech recognition can support voice-to-text input when the browser and device support the Web Speech API.

### 8. Language Accessibility
An English/Malayalam toggle implemented with a custom dictionary.

### 9. Geographic Visualization
A district map rendered with SVG and geographic data represented using GeoJSON, without requiring a third-party map-rendering library or map API key.

### 10. Authentication and Security
The backend includes authentication-related functionality using JWT tokens and password/token hashing. Production security requires additional verification and configuration.

*Feature availability depends on the current branch and integration status. Descriptions of planned or partially implemented functionality should not be interpreted as proof that the feature is production-ready.*

## 🔄 System Workflow

1. **Report submission:** A user submits information through the reporting interface.
2. **Request processing:** The frontend sends supported requests to the backend API.
3. **Data organization:** The backend processes and stores information using the configured database.
4. **Officer review:** Authorized users access the available dashboard and case information.
5. **Communication simulation:** Supported WebSocket functionality handles the prototype's simulated signalling workflow.
6. **Professional assessment:** Authorized professionals review information and determine appropriate follow-up.

AI-assisted summaries, where available, are intended to provide supporting context rather than automated conclusions.

## 🛠️ Technology Stack

### Backend

| Technology | Purpose |
|---|---|
| Python 3.12 | Backend development |
| FastAPI | REST API framework |
| Uvicorn | ASGI application server |
| SQLAlchemy | Database ORM |
| SQLite | Local development database |
| JWT | Authentication tokens |
| Password/token hashing | Credential and token security |
| WebSocket | Simulated signalling workflow |
| pytest | Automated testing |
| GeoJSON | Geographic data representation |

**Database note:** The current development database is SQLite, using `karuthal_dev.db`. PostgreSQL is a possible future migration and is not described as the current database.

### Frontend

| Technology | Purpose |
|---|---|
| React | Component-based user interface |
| Vite | Development server and build tooling |
| React Router DOM | Client-side navigation |
| Plain CSS | Custom interface styling |
| SVG | District map visualization |
| Web Speech API | Browser-based voice-to-text |
| Geolocation API | Optional location access |
| WebSocket API | Simulated real-time communication |
| Custom dictionary | English/Malayalam language toggle |

The exact installed React and other dependency versions should be taken from `frontend/package.json`.

### Development Tools

- **Git and GitHub** — Version control and collaboration.
- **Node.js and npm** — Frontend tooling and dependency management.
- **PowerShell** — Windows development environment.
- **Antigravity** — AI-assisted coding workflow.
- **Claude** — Planning, prompt development, and code review assistance.

AI-assisted development tools were used during development; they are not necessarily runtime dependencies of the application.

## 🏗️ System Architecture

```text
             Public User
                  |
                  v
       React + Vite Frontend
                  |
          HTTP / REST API
                  |
                  v
          FastAPI Backend
           /           \
          v             v
   SQLAlchemy       WebSocket
          |         Signalling
          v
    SQLite Database

   Officer Dashboard
          |
          v
   Case Review Interface

   SVG District Map
          |
          v
    GeoJSON Data
```

This diagram describes the intended high-level architecture. Actual runtime connections depend on the current implementation and configuration.

## 🚀 Getting Started

### Prerequisites

Install the following:

- Git
- Node.js and npm
- Python 3.12
- A terminal such as Windows PowerShell

### 1. Clone the repository

```bash
git clone https://github.com/Sredha12/KARUTHAL.git
cd KARUTHAL
```

### 2. Start the frontend

Open PowerShell in the repository directory:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL displayed in the terminal. Vite commonly uses:

`http://localhost:5173`

### 3. Start the backend

Open a **separate terminal**. Navigate to the backend directory containing the application's `main.py`.

For the backend worktree layout used during development, the directory may be:

```powershell
cd C:\Users\Sreddha\KARUTHAL\KARUTHAL-backend\backend
```

Activate the project's existing Python 3.12 environment if available. Otherwise, create one:

```powershell
py -3.12 -m venv .venv312
.\.venv312\Scripts\Activate.ps1
```

Install dependencies from the requirements file configured for that backend:

```powershell
pip install -r requirements.txt
```

If the project uses a differently named requirements file, use that file instead.

Start the API:

```powershell
python -m uvicorn main:app --reload --port 8000
```

The local API should be accessible at:

`http://127.0.0.1:8000`

If FastAPI's interactive documentation is enabled, open:

`http://127.0.0.1:8000/docs`

**Important:** The frontend and backend must both be running for local end-to-end testing. Actual folder names and dependency files should be checked against the branch being used.

## 🧪 Testing

The project team reports **56 pytest tests**.

Run the tests from the configured backend environment:

```powershell
python -m pytest
```

To verify the current test count and results, run the test suite against the current code. The reported count does not guarantee that every test is currently passing.

Frontend production-build verification can be performed from the frontend directory:

```powershell
npm run build
```

## 🔐 Privacy and Responsible AI

Child-protection systems handle sensitive information. Privacy and responsible use are central design requirements for KARUTHAL.

### Privacy Principles

- Limit access to sensitive information to authorized users.
- Collect only information necessary for the intended purpose.
- Avoid using real child-related information in demonstrations unless appropriately authorized.
- Protect credentials and secret configuration values.
- Apply suitable access controls, secure transmission, and audit logging before operational deployment.
- Request permission before accessing optional browser location features.

### Simulated Communication

The communication workflow is a prototype simulation.

- It does not place calls through the public telephone network.
- It does not automatically connect users to a real helpline.
- It does not record audio as part of the simulated call-signalling workflow.

Browser speech recognition is a separate browser capability and may have its own browser or service behaviour.

### Responsible AI

Any AI-generated summary is advisory only.

- AI must not independently determine guilt or establish that abuse has occurred.
- Automated outputs must not replace professional assessment.
- Potential patterns should be reviewed by authorized professionals.
- Model identity, data handling, and AI integration must be verified before claiming a particular AI provider or model.

## 🚧 Current Status

KARUTHAL is an evolving hackathon prototype.

The development stack includes a React frontend, FastAPI backend, SQLAlchemy, SQLite, authentication-related functionality, geographic visualization, and simulated WebSocket signalling.

The availability and integration of individual features may differ across development branches. Production deployment, security validation, database migration, and AI capabilities require separate verification.

## 🗺️ Future Enhancements

Potential future improvements include:

- PostgreSQL migration if required by deployment needs.
- Expanded role-based access controls and audit logging.
- Improved case timeline and follow-up management.
- Additional Malayalam accessibility improvements.
- Carefully evaluated AI-assisted summarization.
- Integration testing and secure deployment.
- Usability testing with relevant professionals and stakeholders.

These are possible enhancements, not claims of completed functionality.

## 👥 Team

**KARUTHAL Team**  
She Builds Tech 3.0 — AI Hackathon

## 📄 Disclaimer

KARUTHAL is a prototype developed to explore technology-assisted child-protection workflows. It is not a replacement for official child-protection systems, emergency services, legal processes, or qualified professional judgment.

Any real-world deployment would require appropriate authorization, security assessment, privacy safeguards, stakeholder validation, and compliance with applicable laws and procedures.
