import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "data" / "banking.db"

random.seed(42)

N_CUSTOMERS = 10_000
N_ACCOUNTS = 15_000
N_TRANSACTIONS = 100_000


def random_date(start, end):
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def generate_data():

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # -------------------------
    # Nettoyer les anciennes données
    # -------------------------

    cursor.execute("DELETE FROM transactions")
    cursor.execute("DELETE FROM accounts")
    cursor.execute("DELETE FROM customers")
    cursor.execute("DELETE FROM agencies")
    cursor.execute("DELETE FROM operation_types")

    # -------------------------
    # AGENCIES
    # -------------------------

    cities = [
        "Lyon", "Paris", "Marseille", "Toulouse", "Bordeaux",
        "Lille", "Nantes", "Grenoble", "Rennes", "Montpellier"
    ]

    regions = [
        "Auvergne-Rhône-Alpes",
        "Île-de-France",
        "Provence-Alpes-Côte d'Azur",
        "Occitanie",
        "Nouvelle-Aquitaine",
        "Hauts-de-France",
        "Pays de la Loire",
        "Bretagne"
    ]

    agencies = []

    for agency_id in range(1, 31):

        city = random.choice(cities)

        agencies.append((
            agency_id,
            f"Agency_{agency_id:02d}",
            city,
            random.choice(regions),
            random.choice(["Urban", "Regional", "Local"]),
            random_date(
                date(2000, 1, 1),
                date(2020, 12, 31)
            ).isoformat()
        ))

    cursor.executemany("""
        INSERT INTO agencies
        VALUES (?, ?, ?, ?, ?, ?)
    """, agencies)

    # -------------------------
    # OPERATION TYPES
    # -------------------------

    operations = [
        (1, "Cash Withdrawal", "Cash"),
        (2, "Cash Deposit", "Cash"),
        (3, "Card Payment", "Payment"),
        (4, "Bank Transfer", "Transfer"),
        (5, "Salary Deposit", "Income"),
        (6, "Loan Repayment", "Loan"),
        (7, "Bank Fee", "Fee")
    ]

    cursor.executemany("""
        INSERT INTO operation_types
        VALUES (?, ?, ?)
    """, operations)

    # -------------------------
    # CUSTOMERS
    # -------------------------

    segments = [
        "Student",
        "Individual",
        "Professional",
        "Premium"
    ]

    customers = []

    for customer_id in range(1, N_CUSTOMERS + 1):

        customers.append((
            customer_id,
            random.randint(18, 80),
            random.choice(segments),
            random.choice(cities),
            random_date(
                date(2018, 1, 1),
                date(2024, 12, 31)
            ).isoformat()
        ))

    cursor.executemany("""
        INSERT INTO customers
        VALUES (?, ?, ?, ?, ?)
    """, customers)

    # -------------------------
    # ACCOUNTS
    # -------------------------

    account_types = [
        "Checking",
        "Savings",
        "Business"
    ]

    accounts = []

    for account_id in range(1, N_ACCOUNTS + 1):

        customer_id = random.randint(1, N_CUSTOMERS)
        agency_id = random.randint(1, 30)

        accounts.append((
            account_id,
            customer_id,
            agency_id,
            random.choice(account_types),
            round(random.uniform(100, 50_000), 2),
            random_date(
                date(2019, 1, 1),
                date(2024, 12, 31)
            ).isoformat()
        ))

    cursor.executemany("""
        INSERT INTO accounts
        VALUES (?, ?, ?, ?, ?, ?)
    """, accounts)

    # On garde la relation account -> customer
    account_customer = {
        account[0]: account[1]
        for account in accounts
    }

    # -------------------------
    # TRANSACTIONS
    # -------------------------

    transaction_dates = []

    current_date = date(2025, 1, 1)
    end_date = date(2026, 12, 31)

    while current_date <= end_date:

        # Plus de transactions en semaine
        weight = 1

        if current_date.weekday() < 5:
            weight *= 2

        # Pic début de mois
        if current_date.day <= 5:
            weight *= 1.5

        # Pic fin de mois
        if current_date.day >= 25:
            weight *= 1.3

        transaction_dates.append(
            (current_date, weight)
        )

        current_date += timedelta(days=1)

    dates = [x[0] for x in transaction_dates]
    weights = [x[1] for x in transaction_dates]

    channels = [
        "ATM",
        "Branch",
        "Mobile",
        "Web",
        "Card"
    ]

    statuses = [
        "Completed",
        "Completed",
        "Completed",
        "Completed",
        "Failed"
    ]

    transactions = []

    print("Generating transactions...")

    for transaction_id in range(1, N_TRANSACTIONS + 1):

        account_id = random.randint(1, N_ACCOUNTS)

        customer_id = account_customer[account_id]

        agency_id = random.randint(1, 30)

        operation_type_id = random.randint(1, 7)

        transaction_date = random.choices(
            dates,
            weights=weights,
            k=1
        )[0]

        # Montants différents selon le type d'opération
        if operation_type_id == 1:
            amount = random.uniform(20, 1000)

        elif operation_type_id == 2:
            amount = random.uniform(50, 3000)

        elif operation_type_id == 3:
            amount = random.uniform(5, 500)

        elif operation_type_id == 4:
            amount = random.uniform(50, 5000)

        elif operation_type_id == 5:
            amount = random.uniform(1000, 5000)

        elif operation_type_id == 6:
            amount = random.uniform(100, 2000)

        else:
            amount = random.uniform(2, 50)

        debit_credit = (
            "CREDIT"
            if operation_type_id in [2, 5]
            else "DEBIT"
        )

        transactions.append((
            transaction_id,
            account_id,
            customer_id,
            agency_id,
            operation_type_id,
            transaction_date.isoformat(),
            round(amount, 2),
            debit_credit,
            random.choice(channels),
            random.choice(statuses)
        ))

    cursor.executemany("""
        INSERT INTO transactions
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, transactions)

    conn.commit()
    conn.close()

    print("Data generated successfully.")
    print(f"Agencies: 30")
    print(f"Customers: {N_CUSTOMERS}")
    print(f"Accounts: {N_ACCOUNTS}")
    print(f"Transactions: {N_TRANSACTIONS}")


if __name__ == "__main__":
    generate_data()