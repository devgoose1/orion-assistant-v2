"""
Database connection and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL (SQLite for now, PostgreSQL later)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./orion.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False  # Set to True for SQL query logging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """
    Dependency for FastAPI to get database session.
    Usage: db = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initialize database - create all tables.
    Call this on application startup.
    """
    from models.device import Device
    from models.session import Session
    from models.tool_execution import ToolExecution
    from models.event import Event
    from models.context_memory import ContextMemory
    
    Base.metadata.create_all(bind=engine)
    print("✓ Database initialized")
