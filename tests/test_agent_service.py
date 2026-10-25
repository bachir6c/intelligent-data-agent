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