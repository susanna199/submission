# database.py

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from .env [cite: 79]
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Create the SQLAlchemy engine
# Neon/Postgres usually requires sslmode=require for cloud connections
engine = create_engine(DATABASE_URL)

# Create a SessionLocal class for database operations
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for your models to inherit from [cite: 35]
Base = declarative_base()

# Dependency to get DB session in FastAPI routes later
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()