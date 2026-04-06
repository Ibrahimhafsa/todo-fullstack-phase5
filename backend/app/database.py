"""Database connection module for Neon PostgreSQL."""
from typing import Generator
import logging

from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

logger = logging.getLogger(__name__)

# Create engine with connection pooling for serverless environment
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,  # Disable SQL logging in production
    pool_pre_ping=True,  # Check connections before use (serverless resilience)
    pool_size=5,
    max_overflow=10,
)


def init_db() -> None:
    """
    Initialize database. Creates tables if they don't exist.

    Note: In production, use Alembic migrations instead of create_all().
    This function is safe for development/testing with fresh databases.

    Phase 5 (Spec-006): Alembic migrations handle schema extensions.
    """
    # Import all models to ensure they're registered with SQLModel
    from app.models.task import Task  # noqa: F401
    from app.models.user import User  # noqa: F401
    from app.models.conversation import Conversation, Message  # noqa: F401 (Spec-4)

    # Create all tables defined in models
    # This is safe for development but production should use Alembic
    SQLModel.metadata.create_all(engine)
    logger.info("Database initialized: all tables created")


def run_migrations() -> None:
    """
    Run Alembic migrations programmatically.

    This is called during application startup to ensure schema is up-to-date.
    Used for: application initialization, Docker startup scripts, CI/CD pipelines.

    Phase 5 (Spec-006): Alembic handles zero-downtime schema migration.
    """
    import subprocess
    import sys

    try:
        # Run alembic upgrade to latest revision
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=".",
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            logger.info("Alembic migrations applied successfully")
        else:
            logger.error(f"Alembic migration failed: {result.stderr}")
    except Exception as e:
        logger.error(f"Error running migrations: {str(e)}")
        raise


def get_session() -> Generator[Session, None, None]:
    """Provide a database session for request handling."""
    with Session(engine) as session:
        yield session
