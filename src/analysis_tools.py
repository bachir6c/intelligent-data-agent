import sqlite3
from pathlib import Path

import pandas as pd


DB_PATH = Path(__file__).resolve().parent.parent / "data" / "banking.db"


def detect_anomalies(
    agency_id,
    operation_type_id,
    z_threshold=2.0
):
    """
    Détecte les jours dont le nombre de transactions
    est anormalement élevé ou faible.
    """

    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT
            transaction_date,
            COUNT(*) AS transaction_count
        FROM transactions
        WHERE agency_id = ?
          AND operation_type_id = ?
          AND status = 'Completed'
        GROUP BY transaction_date
        ORDER BY transaction_date
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=(agency_id, operation_type_id)
    )

    conn.close()

    if df.empty:
        return {
            "success": False,
            "error": "No data found."
        }

    mean = df["transaction_count"].mean()
    std = df["transaction_count"].std()

    if std == 0:
        return {
            "success": True,
            "mean": round(float(mean), 2),
            "std": 0.0,
            "anomalies": []
        }

    df["z_score"] = (
        df["transaction_count"] - mean
    ) / std

    anomalies = df[
        df["z_score"].abs() >= z_threshold
    ]

    anomaly_records = []

    for _, row in anomalies.iterrows():
        anomaly_records.append({
            "transaction_date": str(row["transaction_date"]),
            "transaction_count": int(row["transaction_count"]),
            "z_score": round(float(row["z_score"]), 2)
        })

    return {
        "success": True,
        "mean": round(float(mean), 2),
        "std": round(float(std), 2),
        "z_threshold": z_threshold,
        "anomalies": anomaly_records
    }

# detect_anomalous_agencies
def detect_anomalous_agencies(
    operation_type_id,
    start_date,
    end_date,
    z_threshold=3.0,
    min_transaction_count=10
):
    """
    Détecte les journées avec une activité anormalement élevée
    pour toutes les agences sur une période donnée.

    Une journée est considérée comme anormale si :
    - son z-score dépasse le seuil
    - ET le nombre de transactions est suffisamment important
    """

    from datetime import datetime, timedelta

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    baseline_start = start - timedelta(days=60)

    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT
            agency_id,
            transaction_date,
            COUNT(*) AS transaction_count
        FROM transactions
        WHERE operation_type_id = ?
          AND status = 'Completed'
          AND transaction_date BETWEEN ? AND ?
        GROUP BY agency_id, transaction_date
        ORDER BY agency_id, transaction_date
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=(
            operation_type_id,
            baseline_start.strftime("%Y-%m-%d"),
            end_date
        )
    )

    agencies = pd.read_sql_query(
        "SELECT agency_id, agency_name FROM agencies",
        conn
    )

    conn.close()

    results = []

    for _, agency in agencies.iterrows():

        agency_id = int(agency["agency_id"])

        agency_data = df[
            df["agency_id"] == agency_id
        ].copy()

        all_dates = pd.date_range(
            baseline_start,
            end,
            freq="D"
        )

        if agency_data.empty:
            continue

        daily = agency_data.set_index(
            "transaction_date"
        )["transaction_count"]

        daily.index = pd.to_datetime(daily.index)

        daily = daily.reindex(
            all_dates,
            fill_value=0
        )

        # 60 jours servant de référence
        baseline = daily[
            daily.index < start
        ]

        mean = baseline.mean()
        std = baseline.std()

        if std == 0 or pd.isna(std):
            continue

        target = daily[
            (daily.index >= start)
            & (daily.index <= end)
        ]

        for transaction_date, count in target.items():

            z_score = (count - mean) / std

            if (
                z_score >= z_threshold
                and count >= min_transaction_count
            ):

                results.append({
                    "agency_id": agency_id,
                    "agency_name": str(agency["agency_name"]),
                    "transaction_date":
                        transaction_date.strftime("%Y-%m-%d"),
                    "transaction_count": int(count),
                    "baseline_mean": round(float(mean), 2),
                    "z_score": round(float(z_score), 2)
                })

    return {
        "success": True,
        "threshold": float(z_threshold),
        "minimum_transaction_count": min_transaction_count,
        "baseline_days": 60,
        "start_date": start_date,
        "end_date": end_date,
        "anomalies": results
    }
def detect_channel_anomalies(
    operation_type_id,
    start_date,
    end_date,
    channel=None,
    agency_id=None,
    z_threshold=3.0,
    min_transaction_count=10
):
    """
    Détecte une activité anormale par canal.

    - channel fourni, agency_id=None :
      cherche quelles agences sont anormales sur ce canal.

    - agency_id fourni, channel=None :
      cherche quels canaux sont anormaux pour cette agence.
    """

    from datetime import datetime, timedelta

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    baseline_start = start - timedelta(days=60)

    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT
            agency_id,
            channel,
            transaction_date,
            COUNT(*) AS transaction_count
        FROM transactions
        WHERE operation_type_id = ?
          AND status = 'Completed'
          AND transaction_date BETWEEN ? AND ?
    """

    params = [
        operation_type_id,
        baseline_start.strftime("%Y-%m-%d"),
        end_date
    ]

    if channel is not None:
        query += " AND channel = ?"
        params.append(channel)

    if agency_id is not None:
        query += " AND agency_id = ?"
        params.append(agency_id)

    query += """
        GROUP BY agency_id, channel, transaction_date
        ORDER BY agency_id, channel, transaction_date
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=params
    )

    agencies = pd.read_sql_query(
        "SELECT agency_id, agency_name FROM agencies",
        conn
    )

    conn.close()

    results = []

    if df.empty:
        return {
            "success": True,
            "anomalies": []
        }

    all_dates = pd.date_range(
        baseline_start,
        end,
        freq="D"
    )

    grouped = df.groupby([
        "agency_id",
        "channel"
    ])

    for (current_agency_id, current_channel), group in grouped:

        daily = group.set_index(
            "transaction_date"
        )["transaction_count"]

        daily.index = pd.to_datetime(daily.index)

        daily = daily.reindex(
            all_dates,
            fill_value=0
        )

        baseline = daily[
            daily.index < start
        ]

        mean = baseline.mean()
        std = baseline.std()

        if std == 0 or pd.isna(std):
            continue

        target = daily[
            (daily.index >= start)
            & (daily.index <= end)
        ]

        agency_row = agencies[
            agencies["agency_id"] == current_agency_id
        ]

        agency_name = (
            str(agency_row.iloc[0]["agency_name"])
            if not agency_row.empty
            else None
        )

        for transaction_date, count in target.items():

            z_score = (count - mean) / std

            if (
                z_score >= z_threshold
                and count >= min_transaction_count
            ):

                results.append({
                    "agency_id": int(current_agency_id),
                    "agency_name": agency_name,
                    "channel": str(current_channel),
                    "transaction_date":
                        transaction_date.strftime("%Y-%m-%d"),
                    "transaction_count": int(count),
                    "baseline_mean": round(float(mean), 2),
                    "z_score": round(float(z_score), 2)
                })

    return {
        "success": True,
        "operation_type_id": operation_type_id,
        "agency_id": agency_id,
        "channel": channel,
        "threshold": float(z_threshold),
        "minimum_transaction_count": min_transaction_count,
        "baseline_days": 60,
        "start_date": start_date,
        "end_date": end_date,
        "anomalies": results
    }
def detect_trend_anomalies(
    start_date,
    end_date,
    operation_type_id=None,
    agency_id=None,
    min_growth_ratio=2.0,
    min_last_week_count=20
):
    """
    Détecte les fortes augmentations progressives.

    - operation_type_id fourni :
      cherche quelles agences présentent cette tendance.

    - agency_id fourni :
      cherche quels types d'opérations présentent cette tendance.
    """

    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT
            t.agency_id,
            a.agency_name,
            t.operation_type_id,
            ot.operation_name,
            t.transaction_date,
            COUNT(*) AS transaction_count
        FROM transactions t
        JOIN agencies a
            ON t.agency_id = a.agency_id
        JOIN operation_types ot
            ON t.operation_type_id = ot.operation_type_id
        WHERE t.status = 'Completed'
          AND t.transaction_date BETWEEN ? AND ?
    """

    params = [
        start_date,
        end_date
    ]

    if operation_type_id is not None:
        query += " AND t.operation_type_id = ?"
        params.append(operation_type_id)

    if agency_id is not None:
        query += " AND t.agency_id = ?"
        params.append(agency_id)

    query += """
        GROUP BY
            t.agency_id,
            a.agency_name,
            t.operation_type_id,
            ot.operation_name,
            t.transaction_date
        ORDER BY
            t.agency_id,
            t.operation_type_id,
            t.transaction_date
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=params
    )

    conn.close()

    if df.empty:
        return {
            "success": True,
            "anomalies": []
        }

    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"]
    )

    results = []

    for (
        current_agency_id,
        current_operation_type_id
    ), group in df.groupby([
        "agency_id",
        "operation_type_id"
    ]):

        agency_name = group["agency_name"].iloc[0]
        operation_name = group["operation_name"].iloc[0]

        group = group.set_index(
            "transaction_date"
        )

        weekly = group[
            "transaction_count"
        ].resample("W").sum()

        if len(weekly) < 3:
            continue

        first_week = weekly.iloc[0]
        last_week = weekly.iloc[-1]

        if first_week == 0:
            continue

        growth_ratio = (
            last_week / first_week
        )

        increasing_steps = (
            weekly.diff().dropna() > 0
        ).sum()

        total_steps = len(weekly) - 1

        if (
            growth_ratio >= min_growth_ratio
            and last_week >= min_last_week_count
            and increasing_steps >= total_steps * 0.6
        ):

            results.append({
                "agency_id": int(current_agency_id),
                "agency_name": str(agency_name),
                "operation_type_id": int(
                    current_operation_type_id
                ),
                "operation_name": str(operation_name),
                "first_week_count": int(first_week),
                "last_week_count": int(last_week),
                "growth_ratio": round(
                    float(growth_ratio),
                    2
                ),
                "weekly_counts": [
                    int(value)
                    for value in weekly.tolist()
                ]
            })

    return {
        "success": True,
        "operation_type_id": operation_type_id,
        "agency_id": agency_id,
        "start_date": start_date,
        "end_date": end_date,
        "minimum_growth_ratio": min_growth_ratio,
        "minimum_last_week_count": min_last_week_count,
        "anomalies": results
    }
def detect_amount_anomalies(
    operation_type_id,
    start_date,
    end_date,
    z_threshold=3.0,
    min_total_amount=5000
):
    """
    Détecte les agences ayant un montant total journalier
    anormalement élevé pour un type d'opération.
    """

    from datetime import datetime, timedelta

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    baseline_start = start - timedelta(days=60)

    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT
            agency_id,
            transaction_date,
            SUM(amount) AS total_amount
        FROM transactions
        WHERE operation_type_id = ?
          AND status = 'Completed'
          AND transaction_date BETWEEN ? AND ?
        GROUP BY agency_id, transaction_date
        ORDER BY agency_id, transaction_date
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=(
            operation_type_id,
            baseline_start.strftime("%Y-%m-%d"),
            end_date
        )
    )

    agencies = pd.read_sql_query(
        "SELECT agency_id, agency_name FROM agencies",
        conn
    )

    conn.close()

    results = []

    for _, agency in agencies.iterrows():

        agency_id = int(agency["agency_id"])

        agency_data = df[
            df["agency_id"] == agency_id
        ].copy()

        if agency_data.empty:
            continue

        all_dates = pd.date_range(
            baseline_start,
            end,
            freq="D"
        )

        daily = agency_data.set_index(
            "transaction_date"
        )["total_amount"]

        daily.index = pd.to_datetime(daily.index)

        daily = daily.reindex(
            all_dates,
            fill_value=0
        )

        baseline = daily[
            daily.index < start
        ]

        mean = baseline.mean()
        std = baseline.std()

        if std == 0 or pd.isna(std):
            continue

        target = daily[
            (daily.index >= start)
            & (daily.index <= end)
        ]

        for transaction_date, total_amount in target.items():

            z_score = (total_amount - mean) / std

            if (
                z_score >= z_threshold
                and total_amount >= min_total_amount
            ):

                results.append({
                    "agency_id": agency_id,
                    "agency_name": str(agency["agency_name"]),
                    "transaction_date":
                        transaction_date.strftime("%Y-%m-%d"),
                    "total_amount": round(float(total_amount), 2),
                    "baseline_mean": round(float(mean), 2),
                    "z_score": round(float(z_score), 2)
                })

    return {
        "success": True,
        "threshold": float(z_threshold),
        "minimum_total_amount": min_total_amount,
        "baseline_days": 60,
        "start_date": start_date,
        "end_date": end_date,
        "anomalies": results
    }