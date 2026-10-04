import re
import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "data" / "banking.db"


def list_tables():
    """
    Retourne la liste des tables présentes dans la base.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)

    tables = [row[0] for row in cursor.fetchall()]

    conn.close()

    return tables


def get_table_schema(table_name):
    """
    Retourne les colonnes et leurs types pour une table.
    """

    # Vérifie d'abord que la table existe
    if table_name not in list_tables():
        return {
            "error": f"Table '{table_name}' does not exist."
        }

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(f"PRAGMA table_info({table_name})")

    columns = []

    for column in cursor.fetchall():

        columns.append({
            "name": column[1],
            "type": column[2],
            "not_null": bool(column[3]),
            "primary_key": bool(column[5])
        })

    conn.close()

    return columns


def execute_sql(query, max_rows=100):
    """
    Exécute uniquement des requêtes SQL en lecture seule.
    """

    query = query.strip()

    if not query:
        return {
            "success": False,
            "error": "Empty SQL query."
        }

    query_upper = query.upper()

    # Seules SELECT et WITH sont autorisées
    if not (
        query_upper.startswith("SELECT")
        or query_upper.startswith("WITH")
    ):
        return {
            "success": False,
            "error": "Only SELECT queries are allowed."
        }

    # Protection contre les commandes dangereuses
    forbidden_keywords = [
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "CREATE",
        "REPLACE",
        "ATTACH",
        "DETACH",
        "VACUUM"
    ]

    for keyword in forbidden_keywords:

        if re.search(
            rf"\b{keyword}\b",
            query_upper
        ):
            return {
                "success": False,
                "error": f"Forbidden SQL operation: {keyword}"
            }

    try:

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(query)

        columns = [
            description[0]
            for description in cursor.description
        ]

        rows = cursor.fetchmany(max_rows + 1)

        truncated = len(rows) > max_rows

        if truncated:
            rows = rows[:max_rows]

        conn.close()

        return {
            "success": True,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "truncated": truncated
        }

    except sqlite3.Error as error:

        return {
            "success": False,
            "error": str(error)
        }