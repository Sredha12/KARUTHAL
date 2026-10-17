import json
import os
import sys
from dotenv import load_dotenv

# Load .env if present (never print or log its contents)
load_dotenv()


class Settings:
    def __init__(self):
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./karuthal_dev.db")
        self.CORS_ORIGINS: list[str] = [
            origin.strip()
            for origin in os.getenv(
                "CORS_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000",
            ).split(",")
            if origin.strip()
        ]
        
        enforce_scope_str = os.getenv("ENFORCE_DISTRICT_SCOPE", "true").lower()
        self.ENFORCE_DISTRICT_SCOPE: bool = enforce_scope_str in ("true", "1", "yes")
        
        self.DEMO_OFFICER_PASSWORD: str | None = os.getenv("DEMO_OFFICER_PASSWORD")

        # Location retention policy
        try:
            self.LOCATION_RETENTION_DAYS: int = int(os.getenv("LOCATION_RETENTION_DAYS", "90"))
        except ValueError:
            self.LOCATION_RETENTION_DAYS = 90

        # VoIP & Call Session configuration
        self.VOIP_MODE: str = os.getenv("VOIP_MODE", "simulated").lower()
        
        raw_ice = os.getenv("VOIP_ICE_SERVERS", "[]")
        try:
            self.VOIP_ICE_SERVERS: list[dict] = json.loads(raw_ice)
        except Exception:
            self.VOIP_ICE_SERVERS = []

        try:
            self.VOIP_RING_TIMEOUT_SECONDS: int = int(os.getenv("VOIP_RING_TIMEOUT_SECONDS", "45"))
        except ValueError:
            self.VOIP_RING_TIMEOUT_SECONDS = 45

        try:
            self.VOIP_MAX_CALLS_PER_CASE_PER_DAY: int = int(os.getenv("VOIP_MAX_CALLS_PER_CASE_PER_DAY", "5"))
        except ValueError:
            self.VOIP_MAX_CALLS_PER_CASE_PER_DAY = 5

    @property
    def JWT_SECRET(self) -> str:
        secret = os.getenv("JWT_SECRET")
        if not secret:
            raise RuntimeError(
                "CRITICAL STARTUP ERROR: JWT_SECRET environment variable is missing. "
                "Set JWT_SECRET in your environment or .env file before starting the server."
            )
        return secret


settings = Settings()
