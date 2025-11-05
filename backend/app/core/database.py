from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,          # Max number of permanent connections in the pool
    max_overflow=30,       # Max number of temporary connections allowed
    pool_pre_ping=True,    # Check connection health before use
    pool_recycle=3600      # Recycle connections every hour to prevent stale connections
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get DB session
def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

