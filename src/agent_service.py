import re
from pathlib import Path

from agent import run_agent


def extract_chart_path(text):
    """
    Extrait le chemin d'un graphique PNG éventuellement
    présent dans la réponse de l'agent.
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
    Point d'entrée principal pour utiliser l'agent.

    Retourne une réponse structurée exploitable
    par Streamlit, FastAPI ou un autre client.
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

    if chart_path and not Path(chart_path).exists():
        chart_path = None

    return {
        "answer": answer,
        "tools": tools,
        "chart_path": chart_path
    }