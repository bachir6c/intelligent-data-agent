from analysis_tools import detect_channel_anomalies


result = detect_channel_anomalies(
    operation_type_id=4,   # Bank Transfer
    channel="Mobile",
    start_date="2026-08-01",
    end_date="2026-08-31"
)

print(result)