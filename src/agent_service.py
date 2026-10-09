import re
from pathlib import Path

from agent import run_agent


def extract_chart_path(text):
    """
    Extract the path of a PNG chart
    from the agent's textual response.
    """

    match = re.search(
        r"([A-Za-z]:\\[^\n`]+\.png)",
        text
    )

    if match:
        return match.group(1).strip()

    return None


def query_agent(question):
    """
    Main service entry point for the agent.

    Returns a structured response that can be used
    by FastAPI, Streamlit, or another client.
    """

    result = run_agent(
        question,
        return_trace=True,
        verbose=False
    )

    if isinstance(result, dict):
        answer = result.get("answer", "")
        tools = result.get("tools", [])
    else:
        answer = str(result)
        tools = []

    chart_path = extract_chart_path(answer)

    # Remove Markdown image syntax
    answer = re.sub(
        r"!\[[^\]]*\]\(.*?\.png\)",
        "",
        answer,
        flags=re.DOTALL
    )

    # Remove the raw chart path
    if chart_path:
        answer = answer.replace(
            chart_path,
            ""
        )

    # Remove empty Markdown code blocks
    answer = re.sub(
        r"```(?:text)?\s*```",
        "",
        answer,
        flags=re.IGNORECASE
    )

    # Remove unnecessary chart-opening instructions
    answer = re.sub(
        r"Open the image to view the chart\.?",
        "",
        answer,
        flags=re.IGNORECASE
    )

    # Remove excessive blank lines
    answer = re.sub(
        r"\n{3,}",
        "\n\n",
        answer
    ).strip()

    if chart_path and not Path(chart_path).exists():
        chart_path = None

    return {
        "answer": answer,
        "tools": tools,
        "chart_path": chart_path
    }