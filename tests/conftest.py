import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database import Base, get_db
from src.main import app
from dotenv import load_dotenv
import os

load_dotenv()

# We pull a DIFFERENT variable for testing
# This ensures pytest doesn't touch your production DATABASE_URL
SQLALCHEMY_TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if not SQLALCHEMY_TEST_DATABASE_URL:
    raise ValueError("TEST_DATABASE_URL not found in .env file")

engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def db():
    # 1. Create all tables in the TEST branch
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # 2. WARNING: This deletes everything in the TEST branch after tests finish
        # This keeps your test environment clean for the next run
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def client(db):
    # Dependency override: tell FastAPI to use the test DB session
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c