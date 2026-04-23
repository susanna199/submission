# check_schema.py
# This file connects to the database and prints the tables found in Neon for verification.

from sqlalchemy import inspect
from src.database import engine

inspector = inspect(engine)
tables = inspector.get_table_names()

print("Tables found in Neon:")
for table in tables:
    print(f"- {table}")
    # Optional: print columns for the users table
    if table == 'users':
        columns = inspector.get_columns(table)
        print(f"  Columns in users: {[c['name'] for c in columns]}")