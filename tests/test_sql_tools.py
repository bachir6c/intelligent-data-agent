import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_PATH = ROOT_DIR / "src"

sys.path.append(str(SRC_PATH))

from sql_tools import execute_sql


def test_empty_query_is_rejected():
    result = execute_sql("")

    assert result["success"] is False
    assert result["error"] == "Empty SQL query."


def test_update_is_rejected():
    result = execute_sql(
        "UPDATE customers SET customer_id = 1"
    )

    assert result["success"] is False
    assert "Only SELECT queries are allowed" in result["error"]


def test_delete_is_rejected():
    result = execute_sql(
        "DELETE FROM transactions"
    )

    assert result["success"] is False


def test_drop_is_rejected():
    result = execute_sql(
        "DROP TABLE customers"
    )

    assert result["success"] is False


def test_dangerous_command_after_select_is_rejected():
    result = execute_sql(
        "SELECT * FROM customers; DROP TABLE customers;"
    )

    assert result["success"] is False
    assert "Forbidden SQL operation: DROP" in result["error"]


def test_valid_select_is_allowed():
    result = execute_sql(
        "SELECT 1 AS value"
    )

    assert result["success"] is True
    assert result["columns"] == ["value"]
    assert result["rows"] == [(1,)]