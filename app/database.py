from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def run_startup_migrations() -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    inspector = inspect(engine)
    if "patients" not in inspector.get_table_names():
        return

    patient_columns = {column["name"] for column in inspector.get_columns("patients")}
    with engine.begin() as connection:
        if "blood_group" not in patient_columns:
            connection.execute(text("ALTER TABLE patients ADD COLUMN blood_group VARCHAR(20)"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
