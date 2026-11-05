"""SQLAlchemy engine, session factory, Base class and the reusable get_db dependency."""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    """Yield one session per request and always close it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
