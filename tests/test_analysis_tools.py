import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_PATH = ROOT_DIR / "src"

sys.path.append(str(SRC_PATH))

from analysis_tools import (
    detect_anomalies,
    detect_channel_anomalies,
    detect_trend_anomalies,
    detect_amount_anomalies,
)


def test_daily_anomalies_agency_8():
    result = detect_anomalies(
        agency_id=8,
        operation_type_id=1,
        z_threshold=2.0
    )

    assert result["success"] is True

    dates = {
        anomaly["transaction_date"]
        for anomaly in result["anomalies"]
    }

    assert "2026-03-17" in dates
    assert "2026-03-18" in dates
    assert "2026-03-19" in dates


def test_trend_anomaly_agency_21():
    result = detect_trend_anomalies(
        start_date="2026-05-01",
        end_date="2026-05-31",
        agency_id=21
    )

    assert result["success"] is True
    assert len(result["anomalies"]) >= 1

    anomaly = result["anomalies"][0]

    assert anomaly["agency_id"] == 21
    assert anomaly["operation_type_id"] == 2
    assert anomaly["operation_name"] == "Cash Deposit"

    assert anomaly["weekly_counts"] == [
        1,
        11,
        25,
        38,
        60
    ]


def test_mobile_channel_anomaly_agency_4():
    result = detect_channel_anomalies(
        operation_type_id=4,
        start_date="2026-08-01",
        end_date="2026-08-31",
        agency_id=4
    )

    assert result["success"] is True

    mobile_anomalies = [
        anomaly
        for anomaly in result["anomalies"]
        if anomaly["channel"] == "Mobile"
    ]

    dates = {
        anomaly["transaction_date"]
        for anomaly in mobile_anomalies
    }

    assert {
        "2026-08-10",
        "2026-08-11",
        "2026-08-12",
        "2026-08-13",
        "2026-08-14",
    }.issubset(dates)


def test_amount_anomalies_agency_8():
    result = detect_amount_anomalies(
        operation_type_id=1,
        start_date="2026-03-01",
        end_date="2026-03-31"
    )

    assert result["success"] is True

    agency_8_dates = {
        anomaly["transaction_date"]
        for anomaly in result["anomalies"]
        if anomaly["agency_id"] == 8
    }

    assert {
        "2026-03-17",
        "2026-03-18",
        "2026-03-19",
    }.issubset(agency_8_dates)