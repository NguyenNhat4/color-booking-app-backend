from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# Create database engine
engine = create_engine(settings.DATABASE_URL)

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

def get_database_session():
    """
    Dependency function to get database session.
    Ensures session is properly closed after use.
    """
    database_session = SessionLocal()
    try:
        yield database_session
    finally:
        database_session.close() 