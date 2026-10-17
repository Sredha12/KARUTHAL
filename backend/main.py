from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.errors import register_error_handlers
from app.init_db import init_locations
from app.routers import (
    ai_summary,
    assignments,
    auth,
    cases,
    dashboard,
    emergency,
    field_visits,
    history,
    locations,
    referrals,
    reports,
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Enforce JWT_SECRET configuration on startup
    _ = settings.JWT_SECRET
    # Ensure database tables exist
    Base.metadata.create_all(bind=engine)
    # Ensure standard locations exist
    with SessionLocal() as db:
        init_locations(db)
    yield


app = FastAPI(
    title="Karuthal API",
    description="Privacy-conscious child-protection support backend prototype",
    version="0.2.0",
    lifespan=lifespan,
)

# Strict Security Headers
app.add_middleware(SecurityHeadersMiddleware)

# CORS Middleware (strict origins, explicit methods and headers, no wildcard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Standardized error responses: {"message": "<text>"}
register_error_handlers(app)


@app.get("/")
def home():
    return {
        "project": "Karuthal",
        "message": "Backend is running",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


# Include routers
app.include_router(auth.router)
app.include_router(locations.router)
app.include_router(reports.router)
app.include_router(cases.router)
app.include_router(dashboard.router)
app.include_router(assignments.router)
app.include_router(field_visits.router)
app.include_router(referrals.router)
app.include_router(emergency.router)
app.include_router(history.router)
app.include_router(ai_summary.router)
