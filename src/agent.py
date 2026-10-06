import json

from groq import Groq

from config import (
    GROQ_API_KEY,
    MODEL,
    MAX_AGENT_ITERATIONS
)
from visualization_tools import plot_daily_activity
from sql_tools import (
    list_tables,
    get_table_schema,
    execute_sql
)

from analysis_tools import (
    detect_anomalies,
    detect_anomalous_agencies,
    detect_channel_anomalies,
    detect_trend_anomalies,
    detect_amount_anomalies
)



client = Groq(
    api_key=GROQ_API_KEY
)



# =========================================================
# TOOLS AVAILABLE TO THE AGENT
# =========================================================

tools = [
    {
        "type": "function",
        "function": {
            "name": "list_tables",
            "description": "List all available tables in the SQL database.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_table_schema",
            "description": "Get the columns and types of a database table.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string"
                    }
                },
                "required": ["table_name"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "execute_sql",
            "description": "Execute a read-only SQL SELECT query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string"
                    }
                },
                "required": ["query"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "detect_anomalies",
            "description": (
                "Detect statistically unusual days for a specific agency "
                "and operation type using transaction counts and z-scores."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "agency_id": {
                        "type": "integer"
                    },
                    "operation_type_id": {
                        "type": "integer"
                    },
                    "z_threshold": {
                        "type": "number"
                    }
                },
                "required": [
                    "agency_id",
                    "operation_type_id"
                ]
            }
        }
    },
    {
    "type": "function",
    "function": {
        "name": "detect_anomalous_agencies",
        "description": (
            "Detect agencies with unusually high transaction activity "
            "for a specific operation type during a date range."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "operation_type_id": {
                    "type": "integer"
                },
                "start_date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format."
                },
                "end_date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format."
                },
                "z_threshold": {
                    "type": "number"
                },
                "min_transaction_count": {
                    "type": "integer"
                }
            },
            "required": [
                "operation_type_id",
                "start_date",
                "end_date"
            ]
        }
    }
    },
    {
    "type": "function",
    "function": {
        "name": "detect_channel_anomalies",
        "description": (
            "Detect agencies with unusually high transaction activity "
            "for a specific operation type and channel during a date range."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "operation_type_id": {
                    "type": "integer"
                },
                "channel": {
                    "type": "string"
                },
                "start_date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format."
                },
                "end_date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format."
                },
                "z_threshold": {
                    "type": "number"
                },
                "min_transaction_count": {
                    "type": "integer"
                },
                "agency_id": {
                    "type": "integer"
                },
            },
            "required": [
                "operation_type_id",
                "start_date",
                "end_date"
            ]
        }
    }
    },
    {
    "type": "function",
    "function": {
        "name": "detect_trend_anomalies",
        "description": (
            "Detect agencies showing a strong progressive increase "
            "in transaction activity over a date range."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "operation_type_id": {
                    "type": "integer"
                },
                "start_date": {
                    "type": "string"
                },
                "end_date": {
                    "type": "string"
                },
                "min_growth_ratio": {
                    "type": "number"
                },
                "min_last_week_count": {
                    "type": "integer"
                },
                "agency_id": {
                    "type": "integer"
                },
            },
            "required": [
                
                "start_date",
                "end_date"
            ]
        }
    }
    },
    {
    "type": "function",
    "function": {
        "name": "detect_amount_anomalies",
        "description": (
            "Detect agencies with unusually high daily total transaction "
            "amounts for a specific operation type during a date range."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "operation_type_id": {
                    "type": "integer"
                },
                "start_date": {
                    "type": "string"
                },
                "end_date": {
                    "type": "string"
                },
                "z_threshold": {
                    "type": "number"
                },
                "min_total_amount": {
                    "type": "number"
                }
            },
            "required": [
                "operation_type_id",
                "start_date",
                "end_date"
            ]
        }
    }
    },
    {
    "type": "function",
    "function": {
        "name": "plot_daily_activity",
        "description": (
            "Create a daily activity chart for a specific agency "
            "and operation type over a date range."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "agency_id": {
                    "type": "integer"
                },
                "operation_type_id": {
                    "type": "integer"
                },
                "start_date": {
                    "type": "string"
                },
                "end_date": {
                    "type": "string"
                },
                "metric": {
                    "type": "string",
                    "enum": ["count", "amount"]
                },
                "channel": {
                    "type": "string",
                    "enum": ["Mobile", "ATM", "Branch", "Web", "Card"]
                }
            },
            "required": [
                "agency_id",
                "operation_type_id",
                "start_date",
                "end_date",
                "metric"
            ]
        }
    }
    }

]


# =========================================================
# TOOL EXECUTION
# =========================================================

def call_tool(name, arguments):

    if name == "list_tables":
        return list_tables()

    if name == "get_table_schema":
        return get_table_schema(
            arguments["table_name"]
        )

    if name == "execute_sql":
        return execute_sql(
            arguments["query"]
        )

    if name == "detect_anomalies":
        return detect_anomalies(
            agency_id=arguments["agency_id"],
            operation_type_id=arguments["operation_type_id"],
            z_threshold=arguments.get("z_threshold", 2.0)
        )

    if name == "detect_anomalous_agencies":
        return detect_anomalous_agencies(
            operation_type_id=arguments["operation_type_id"],
            start_date=arguments["start_date"],
            end_date=arguments["end_date"],
            z_threshold=arguments.get("z_threshold", 3.0),
            min_transaction_count=arguments.get("min_transaction_count", 10)
        )
    if name == "detect_channel_anomalies":
        return detect_channel_anomalies(
            operation_type_id=arguments["operation_type_id"],
            start_date=arguments["start_date"],
            end_date=arguments["end_date"],
            channel=arguments.get("channel"),
            agency_id=arguments.get("agency_id"),
            z_threshold=arguments.get("z_threshold", 3.0),
            min_transaction_count=arguments.get(
                "min_transaction_count",
                10
            )
        )
    
    
    if name == "detect_trend_anomalies":
        return detect_trend_anomalies(
            start_date=arguments["start_date"],
            end_date=arguments["end_date"],
            operation_type_id=arguments.get("operation_type_id"),
            agency_id=arguments.get("agency_id"),
            min_growth_ratio=arguments.get(
                "min_growth_ratio",
                2.0
            ),
            min_last_week_count=arguments.get(
                "min_last_week_count",
                20
            )
        )
    if name == "detect_amount_anomalies":
        return detect_amount_anomalies(
            operation_type_id=arguments["operation_type_id"],
            start_date=arguments["start_date"],
            end_date=arguments["end_date"],
            z_threshold=arguments.get("z_threshold", 3.0),
            min_total_amount=arguments.get(
                "min_total_amount",
                5000
        )
    )
    if name == "plot_daily_activity":
        return plot_daily_activity(
            agency_id=arguments["agency_id"],
            operation_type_id=arguments["operation_type_id"],
            start_date=arguments["start_date"],
            end_date=arguments["end_date"],
            metric=arguments["metric"],
            channel=arguments.get("channel")
        )
    return {
        "error": f"Unknown tool: {name}"
    }



# =========================================================
# AGENT
# =========================================================

def run_agent(question, return_trace=False, verbose=True):

    messages = [
        {
            "role": "system",
            "content": """
You are an intelligent data analysis agent.

You have access to a SQL banking database.

Use tools when the user's question requires database information.

Important rules:
- Inspect the database schema when necessary.
- Never invent tables or columns.
- Use only read-only SQL.
- If a SQL query fails, read the error message.
- Inspect the schema again if necessary.
- Correct the SQL query and retry.
- Do not give up after the first SQL error.
- Do not use tools for general knowledge questions.
- Give the final answer clearly and concisely.
- Answer in the same language as the user.
- For any question about the database, never answer from your own knowledge.
- Always use the available database tools to obtain the factual result.
- Base database-specific answers only on tool results.
- Never invent database values, statistics, tables, columns, or records.
- Use detect_anomalies when the user asks about unusual, abnormal,
  anomalous, or statistically exceptional transaction activity.
- Never guess agency IDs or operation type IDs.
  Retrieve them from the database when necessary.
- Your answers are displayed in a terminal.
- Do not use LaTeX.
- Write mathematical formulas using plain text.
- Never invent statistical thresholds.
- When explaining anomaly results, use only the threshold actually used by the analysis tool.
- Use detect_anomalous_agencies when the user asks which agencies
  show abnormal activity during a specified time period.
- Use detect_channel_anomalies when the user asks about abnormal
  activity for a specific transaction channel such as Mobile, ATM,
  Branch, Web, or Card.
- Retrieve operation type IDs from the database instead of guessing them.
- Use detect_trend_anomalies when the user asks about a strong
  progressive increase in transaction activity over time.
- Use detect_amount_anomalies when the user asks about unusually high
  transaction amounts or abnormal monetary volumes over a time period.
- Use plot_daily_activity when the user explicitly asks for a chart,
  graph, plot, or visualization of transaction activity.
- Use metric="count" for number of transactions.
- Use metric="amount" for monetary amounts.
- If the requested information is not available in the database
  and no available tool can retrieve it, explicitly say that the
  information cannot be determined from the available data.

- Never invent external information such as weather, news,
  geographic conditions, or other data that is not present
  in the database.
- If a tool result does not explicitly contain a currency, never display any currency name or symbol. Display only the numeric amount.
"""
        },
        {
            "role": "user",
            "content": question
        }
    ]

    max_iterations = MAX_AGENT_ITERATIONS
    tool_history = []
    for iteration in range(max_iterations):

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0
        )

        message = response.choices[0].message

        # Réponse finale
        if not message.tool_calls:

            if return_trace:
                return {
                    "answer": message.content,
                    "tools": tool_history
                }

            return message.content

        messages.append(message)

        if verbose:
            print(f"\nIteration {iteration + 1}")

        for tool_call in message.tool_calls:

            tool_name = tool_call.function.name
            tool_history.append(tool_name)
            arguments = json.loads(
                tool_call.function.arguments
            )

            if verbose:
                print(f"Tool: {tool_name}")
                print(f"Arguments: {arguments}")

            result = call_tool(
                tool_name,
                arguments
            )

            if verbose:
                print(f"Result: {result}")

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": json.dumps(
                    result,
                    ensure_ascii=False
                )
            })

    if return_trace:
        return {
            "answer": "Maximum number of agent iterations reached.",
            "tools": tool_history
        }

    return "Maximum number of agent iterations reached."


# =========================================================
# TERMINAL
# =========================================================

if __name__ == "__main__":

    question = input(
        "\nAsk a question about the database:\n> "
    )

    answer = run_agent(question)

    print("\nFinal answer:")
    print(answer)