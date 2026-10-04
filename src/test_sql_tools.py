from sql_tools import (
    list_tables,
    get_table_schema,
    execute_sql
)


print("\n--- TABLES ---")
print(list_tables())


print("\n--- TRANSACTIONS SCHEMA ---")
print(get_table_schema("transactions"))


print("\n--- SQL QUERY ---")

result = execute_sql("""
    SELECT
        agency_id,
        COUNT(*) AS number_transactions
    FROM transactions
    GROUP BY agency_id
    ORDER BY number_transactions DESC
    LIMIT 5
""")

print(result)