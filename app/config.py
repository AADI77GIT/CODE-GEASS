import os

from dotenv import load_dotenv

load_dotenv()


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings:
    app_name = os.getenv("APP_NAME", "MediTrack AI Backend")
    environment = os.getenv("ENVIRONMENT", "development")
    database_url = os.getenv("DATABASE_URL", "sqlite:///./meditrack_ai.db")
    cors_origins = _split_csv(
        os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173",
        )
    )
    seed_demo_data = os.getenv("SEED_DEMO_DATA", "true").lower() in {"1", "true", "yes", "on"}


settings = Settings()
