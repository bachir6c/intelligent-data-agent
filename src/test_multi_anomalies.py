from analysis_tools import detect_anomalous_agencies


result = detect_anomalous_agencies(
    operation_type_id=1,
    start_date="2026-03-01",
    end_date="2026-03-31"
)

print(result)
