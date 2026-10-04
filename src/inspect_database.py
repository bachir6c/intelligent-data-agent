import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "data" / "banking.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

tables = [
    "agencies",
    "customers",
    "accounts",
    "operation_types",
    "transactions"
]

for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"{table}: {count}")

conn.close()