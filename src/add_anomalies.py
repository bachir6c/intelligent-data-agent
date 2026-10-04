import json
import random
import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "data" / "banking.db"
GROUND_TRUTH_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "ground_truth.json"
)

random.seed(42)


def get_customer(cursor, account_id):
    cursor.execute(
        "SELECT customer_id FROM accounts WHERE account_id = ?",
        (account_id,)
    )
    return cursor.fetchone()[0]


def add_anomalies():

    # Lire les anomalies déjà existantes
    with open(GROUND_TRUTH_PATH, "r", encoding="utf-8") as file:
        anomalies = json.load(file)

    existing_ids = {a["anomaly_id"] for a in anomalies}

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT MAX(transaction_id) FROM transactions")
    next_id = cursor.fetchone()[0] + 1

    # ==================================================
    # ANOMALIE 2
    # Augmentation progressive des dépôts - Agence 21
    # ==================================================

    if 2 not in existing_ids:

        weeks = [
            ("2026-05-04", 10),
            ("2026-05-11", 20),
            ("2026-05-18", 35),
            ("2026-05-25", 55),
        ]

        total_added = 0

        for day, number_transactions in weeks:

            for _ in range(number_transactions):

                account_id = random.randint(1, 15000)
                customer_id = get_customer(cursor, account_id)

                cursor.execute("""
                    INSERT INTO transactions
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    next_id,
                    account_id,
                    customer_id,
                    21,
                    2,                      # Cash Deposit
                    day,
                    round(random.uniform(500, 3000), 2),
                    "CREDIT",
                    "Branch",
                    "Completed"
                ))

                next_id += 1
                total_added += 1

        anomalies.append({
            "anomaly_id": 2,
            "type": "GRADUAL_INCREASE",
            "agency_id": 21,
            "operation": "Cash Deposit",
            "start_date": "2026-05-04",
            "end_date": "2026-05-25",
            "description": "Progressive increase in cash deposits",
            "transactions_added": total_added
        })

        print("Anomaly 2 added.")

    # ==================================================
    # ANOMALIE 3
    # Pic de virements mobiles - Agence 4
    # ==================================================

    if 3 not in existing_ids:

        total_added = 0

        for day in [
            "2026-08-10",
            "2026-08-11",
            "2026-08-12",
            "2026-08-13",
            "2026-08-14"
        ]:

            for _ in range(30):

                account_id = random.randint(1, 15000)
                customer_id = get_customer(cursor, account_id)

                cursor.execute("""
                    INSERT INTO transactions
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    next_id,
                    account_id,
                    customer_id,
                    4,
                    4,                      # Bank Transfer
                    day,
                    round(random.uniform(500, 5000), 2),
                    "DEBIT",
                    "Mobile",
                    "Completed"
                ))

                next_id += 1
                total_added += 1

        anomalies.append({
            "anomaly_id": 3,
            "type": "CHANNEL_SPECIFIC_SPIKE",
            "agency_id": 4,
            "operation": "Bank Transfer",
            "channel": "Mobile",
            "start_date": "2026-08-10",
            "end_date": "2026-08-14",
            "description": "Abnormally high mobile bank transfer activity",
            "transactions_added": total_added
        })

        print("Anomaly 3 added.")

    conn.commit()
    conn.close()

    with open(
        GROUND_TRUTH_PATH,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(anomalies, file, indent=4)

    print("Ground truth updated.")


if __name__ == "__main__":
    add_anomalies()