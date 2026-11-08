import os
import sys
from pathlib import Path

os.environ.setdefault(
    "GROQ_API_KEY",
    "test-key"
)

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_PATH = ROOT_DIR / "src"

sys.path.append(str(SRC_PATH))

from agent_service import extract_chart_path


def test_extract_chart_path():
    text = (
        "Chart generated at "
        r"G:\project\outputs\agency_4_count_mobile.png"
    )

    result = extract_chart_path(text)

    assert result == (
        r"G:\project\outputs\agency_4_count_mobile.png"
    )


def test_extract_chart_path_returns_none():
    text = "No chart was generated."

    result = extract_chart_path(text)

    assert result is None


def test_extract_chart_path_linux():
    assert extract_chart_path(
        "Chart generated at /app/outputs/agency_4_count_mobile.png"
    ) == "/app/outputs/agency_4_count_mobile.png"


def test_query_agent_uses_tool_chart_without_path_in_answer(monkeypatch, tmp_path):
    import agent_service

    chart = tmp_path / "chart.png"
    chart.write_bytes(b"test")
    monkeypatch.setattr(agent_service, "run_agent", lambda *args, **kwargs: {
        "answer": "Here is the chart.",
        "tools": ["plot_daily_activity"],
        "chart_path": str(chart),
    })
    result = agent_service.query_agent("Plot daily activity")
    assert result["chart_path"] == str(chart)
    assert result["answer"] == "Here is the chart."
