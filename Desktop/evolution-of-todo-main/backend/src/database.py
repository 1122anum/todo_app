from sqlmodel import SQLModel, create_engine, Session
from src.config import settings
import logging

logger = logging.getLogger(__name__)

# Create database engine
connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
engine_args = {
    "echo": settings.DEBUG,
    "pool_pre_ping": True,
}

if "sqlite" not in settings.DATABASE_URL:
    engine_args["pool_size"] = 5
    engine_args["max_overflow"] = 10
else:
    engine_args["connect_args"] = connect_args

try:
    engine = create_engine(settings.DATABASE_URL, **engine_args)
    logger.info(f"Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {str(e)}")
    raise


def create_db_and_tables():
    """Create all database tables"""
    try:
        # Import models to ensure they are registered in SQLModel.metadata
        from src.models.user import User
        from src.models.todo import Todo

        SQLModel.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise


def get_session():
    """Dependency for getting database session (for FastAPI)"""
    try:
        with Session(engine) as session:
            yield session
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        raise


def get_session_context():
    """Get database session as context manager (for direct usage)"""
    return Session(engine)
