import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("DATABASE_URL")
engine = create_engine(url)

try:
    with engine.connect() as connection:
        print("Successfully connected to Neon!")
except Exception as e:
    print(f"Connection failed: {e}")