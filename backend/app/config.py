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
