# create_tables.py
# This script creates the tables in Neon database defined in models.py using
# SQLAlchemy's Base.metadata.create_all() method. 


from src.database import engine, Base
from src.models import User, Institution, Batch, BatchInvite, Session, Attendance

print("Creating tables in Neon...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully!")