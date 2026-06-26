"""
test_connection.py
Verifies the database connection from config.py actually works in Python.
"""

from sqlalchemy import create_engine, text

# Adjust this import to match your actual config.py location/function name.
# Based on your screenshots, something like this should exist:
from config import get_database_url  # <-- change if the name/path differs

def test_connection():
    url = get_database_url()
    print("Attempting to connect...")

    engine = create_engine(url)

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Connection successful:", result.scalar())

            tables = conn.execute(text("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
            """)).fetchall()
            print("✅ Tables found:", [t[0] for t in tables])

    except Exception as e:
        print("❌ Connection FAILED:", e)

if __name__ == "__main__":
    test_connection()