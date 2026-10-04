from analysis_tools import detect_trend_anomalies


result = detect_trend_anomalies(
    operation_type_id=2,  # Cash Deposit
    start_date="2026-05-01",
    end_date="2026-05-31"
)

print(result)