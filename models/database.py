"""
Database configuration and connection setup
"""
import sqlite3
from pathlib import Path
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from loguru import logger

# Database file path
DB_PATH = Path("data/mindtrade.db")
DB_PATH.parent.mkdir(exist_ok=True)

# SQLite database URL
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=False  # Set to True for SQL query logging
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database and create tables"""
    try:
        # Import all models to ensure they're registered
        from .models import Trade, PsychologyNote, Setup, AgentOutput
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
        
        # Create default setups
        create_default_setups()
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

def create_default_setups():
    """Create default trading setups"""
    from .models import Setup
    
    db = SessionLocal()
    try:
        # Check if setups already exist
        existing_setups = db.query(Setup).count()
        if existing_setups > 0:
            return
        
        # Default trading setups
        default_setups = [
            "Liquidity Trap",
            "Fake Breakout", 
            "Transition Phase",
            "Breakout",
            "Pullback",
            "Range Break",
            "Trend Continuation",
            "Reversal",
            "Other"
        ]
        
        for setup_name in default_setups:
            setup = Setup(name=setup_name, description=f"{setup_name} trading setup")
            db.add(setup)
        
        db.commit()
        logger.info(f"Created {len(default_setups)} default trading setups")
        
    except Exception as e:
        logger.error(f"Error creating default setups: {e}")
        db.rollback()
    finally:
        db.close()

def reset_db():
    """Reset database (drop all tables and recreate)"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Database reset successfully")
        init_db()
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        raise
