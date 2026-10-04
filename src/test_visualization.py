from visualization_tools import plot_daily_activity


result = plot_daily_activity(
    agency_id=8,
    operation_type_id=1,
    start_date="2026-03-01",
    end_date="2026-03-31",
    metric="count"
)

print(result)