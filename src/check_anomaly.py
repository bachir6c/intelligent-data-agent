import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "data" / "banking.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
    SELECT
        transaction_date,
        COUNT(*) AS number_of_withdrawals,
        ROUND(SUM(amount), 2) AS total_amount
    FROM transactions
    WHERE agency_id = 8
      AND operation_type_id = 1
      AND status = 'Completed'
      AND transaction_date BETWEEN '2026-03-10' AND '2026-03-25'
    GROUP BY transaction_date
    ORDER BY transaction_date
""")

results = cursor.fetchall()

print("Cash withdrawals - Agency 8\n")

for row in results:
    print(
        f"{row[0]} | "
        f"{row[1]} withdrawals | "
        f"{row[2]} €"
    )

conn.close()