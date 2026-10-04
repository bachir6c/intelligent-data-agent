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


def inject_anomalies():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # On récupère le prochain ID disponible
    cursor.execute("SELECT MAX(transaction_id) FROM transactions")
    next_id = cursor.fetchone()[0] + 1

    anomalies = []

    # --------------------------------------------------
    # ANOMALIE 1
    # Forte hausse des retraits - Agence 8
    # 17 au 19 mars 2026
    # --------------------------------------------------

    inserted = 0

    for day in ["2026-03-17", "2026-03-18", "2026-03-19"]:

        for _ in range(70):

            account_id = random.randint(1, 15000)

            cursor.execute(
                """
                SELECT customer_id
                FROM accounts
                WHERE account_id = ?
                """,
                (account_id,)
            )

            customer_id = cursor.fetchone()[0]

            amount = round(
                random.uniform(500, 1500),
                2
            )

            cursor.execute(
                """
                INSERT INTO transactions
                (
                    transaction_id,
                    account_id,
                    customer_id,
                    agency_id,
                    operation_type_id,
                    transaction_date,
                    amount,
                    debit_credit,
                    channel,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    next_id,
                    account_id,
                    customer_id,
                    8,
                    1,              # Cash Withdrawal
                    day,
                    amount,
                    "DEBIT",
                    "ATM",
                    "Completed"
                )
            )

            next_id += 1
            inserted += 1

    anomalies.append({
        "anomaly_id": 1,
        "type": "SPIKE",
        "agency_id": 8,
        "operation": "Cash Withdrawal",
        "start_date": "2026-03-17",
        "end_date": "2026-03-19",
        "description": "Abnormally high cash withdrawal activity",
        "transactions_added": inserted
    })

    conn.commit()
    conn.close()

    # --------------------------------------------------
    # Sauvegarde du ground truth
    # --------------------------------------------------

    with open(
        GROUND_TRUTH_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            anomalies,
            file,
            indent=4
        )

    print("Anomalies injected successfully.")
    print(f"Ground truth saved to: {GROUND_TRUTH_PATH}")


if __name__ == "__main__":
    inject_anomalies()