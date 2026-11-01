import os


class Settings:
    """Application settings and runtime configuration."""
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "URL Shortener & Analytics API")
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./urls.db")
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")

    DEFAULT_EXPIRY_DAYS: int = int(os.getenv("DEFAULT_EXPIRY_DAYS", "30"))
    SHORT_CODE_LENGTH: int = int(os.getenv("SHORT_CODE_LENGTH", "7"))


settings = Settings()
