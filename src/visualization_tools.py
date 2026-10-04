import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


DB_PATH = Path(__file__).resolve().parent.parent / "data" / "banking.db"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"


def plot_daily_activity(
    agency_id,
    operation_type_id,
    start_date,
    end_date,
    metric="count",
    channel=None
):
    """
    Crée un graphique de l'activité quotidienne d'une agence.

    metric:
    - "count"  -> nombre de transactions
    - "amount" -> montant total

    channel:
    - None     -> tous les canaux
    - "Mobile", "ATM", "Branch", "Web", "Card"
    """

    OUTPUT_DIR.mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)

    # Filtre optionnel sur le canal
    channel_filter = ""

    params = [
        agency_id,
        operation_type_id
    ]

    if channel is not None:
        channel_filter = "AND channel = ?"
        params.append(channel)

    params.extend([
        start_date,
        end_date
    ])

    if metric == "count":

        query = f"""
            SELECT
                transaction_date,
                COUNT(*) AS value
            FROM transactions
            WHERE agency_id = ?
              AND operation_type_id = ?
              {channel_filter}
              AND status = 'Completed'
              AND transaction_date BETWEEN ? AND ?
            GROUP BY transaction_date
            ORDER BY transaction_date
        """

        ylabel = "Number of transactions"

    elif metric == "amount":

        query = f"""
            SELECT
                transaction_date,
                SUM(amount) AS value
            FROM transactions
            WHERE agency_id = ?
              AND operation_type_id = ?
              {channel_filter}
              AND status = 'Completed'
              AND transaction_date BETWEEN ? AND ?
            GROUP BY transaction_date
            ORDER BY transaction_date
        """

        ylabel = "Total amount"

    else:
        conn.close()

        return {
            "success": False,
            "error": "metric must be 'count' or 'amount'"
        }

    df = pd.read_sql_query(
        query,
        conn,
        params=params
    )

    conn.close()

    if df.empty:
        return {
            "success": False,
            "error": "No data found."
        }

    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"]
    )

    all_dates = pd.date_range(
        start=start_date,
        end=end_date,
        freq="D"
    )

    df = (
        df.set_index("transaction_date")
        .reindex(all_dates, fill_value=0)
        .rename_axis("transaction_date")
        .reset_index()
    )

    plt.figure(figsize=(10, 5))

    plt.plot(
        df["transaction_date"],
        df["value"],
        marker="o"
    )

    plt.xlabel("Date")
    plt.ylabel(ylabel)

    title = f"Agency {agency_id} - Daily activity"

    if channel is not None:
        title += f" - {channel}"

    plt.title(title)

    plt.xticks(rotation=45)
    plt.tight_layout()

    channel_suffix = (
        f"_{channel.lower()}"
        if channel is not None
        else ""
    )

    output_path = (
        OUTPUT_DIR
        / f"agency_{agency_id}_{metric}{channel_suffix}.png"
    )

    plt.savefig(output_path)
    plt.close()

    return {
        "success": True,
        "chart_path": str(output_path),
        "channel": channel
    }