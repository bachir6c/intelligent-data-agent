import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "data" / "banking.db"

def create_database():
    # Crée le dossier data s'il n'existe pas
    DB_PATH.parent.mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agencies (
            agency_id INTEGER PRIMARY KEY,
            agency_name TEXT NOT NULL,
            city TEXT NOT NULL,
            region TEXT NOT NULL,
            agency_type TEXT NOT NULL,
            opening_date TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY,
            age INTEGER NOT NULL,
            customer_segment TEXT NOT NULL,
            city TEXT NOT NULL,
            registration_date TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            account_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            agency_id INTEGER NOT NULL,
            account_type TEXT NOT NULL,
            balance REAL NOT NULL,
            opening_date TEXT NOT NULL,

            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (agency_id) REFERENCES agencies(agency_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS operation_types (
            operation_type_id INTEGER PRIMARY KEY,
            operation_name TEXT NOT NULL,
            operation_category TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER PRIMARY KEY,
            account_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            agency_id INTEGER NOT NULL,
            operation_type_id INTEGER NOT NULL,
            transaction_date TEXT NOT NULL,
            amount REAL NOT NULL,
            debit_credit TEXT NOT NULL,
            channel TEXT NOT NULL,
            status TEXT NOT NULL,

            FOREIGN KEY (account_id) REFERENCES accounts(account_id),
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (agency_id) REFERENCES agencies(agency_id),
            FOREIGN KEY (operation_type_id)
                REFERENCES operation_types(operation_type_id)
        )
    """)

    conn.commit()
    conn.close()

    print(f"Database created: {DB_PATH}")


if __name__ == "__main__":
    create_database()