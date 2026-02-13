"""
FRA Diagnostic App - Configuration
"""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""

    # Application
    APP_NAME: str = "FRA Diagnostic Software"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./fra_diagnostic.db"

    # File Upload
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 100

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # JWT Auth (Phase 7)
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ML Models
    MODEL_DIR: str = "ml/saved_models"

    # FRA Data Validation
    MIN_FREQUENCY_HZ: float = 20.0
    MAX_FREQUENCY_HZ: float = 2_000_000.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Ensure upload directory exists
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
