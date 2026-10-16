
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.errors import register_error_handlers
from app.routers import reports


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Enforce JWT_SECRET configuration on startup
    _ = settings.JWT_SECRET
    # Ensure database tables exist
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Karuthal API",
    description="Child-protection support prototype",
    version="0.2.0",
    lifespan=lifespan,
)

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
app.include_router(reports.router)

