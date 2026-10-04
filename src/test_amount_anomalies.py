from analysis_tools import detect_amount_anomalies


result = detect_amount_anomalies(
    operation_type_id=1,
    start_date="2026-03-01",
    end_date="2026-03-31"
)

print(result)