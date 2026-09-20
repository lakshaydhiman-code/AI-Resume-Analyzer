import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.database.models import Base

logger = logging.getLogger("resumelab.database")

def init_engine():
    """
    Initialize SQLAlchemy engine.
    Tries configured DATABASE_URL (PostgreSQL).
    If unreachable or fails, seamlessly falls back to local SQLite.
    """
    db_url = settings.DATABASE_URL
    try:
        if db_url.startswith("postgresql"):
            test_engine = create_engine(db_url, pool_pre_ping=True, connect_args={"connect_timeout": 3})
            with test_engine.connect() as conn:
                pass
            logger.info("Connected to PostgreSQL successfully.")
            return test_engine
        else:
            connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}
            return create_engine(db_url, connect_args=connect_args)
    except Exception as e:
        logger.warning(f"Could not connect to primary database ({db_url}): {e}. Falling back to SQLite ({settings.SQLITE_FALLBACK_URL}).")
        return create_engine(settings.SQLITE_FALLBACK_URL, connect_args={"check_same_thread": False})

engine = init_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)

# Auto-create tables on startup
create_tables()

def get_db():
    """FastAPI dependency to provide a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
