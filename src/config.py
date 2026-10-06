import os
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]

load_dotenv(ROOT_DIR / ".env")


GROQ_API_KEY = os.getenv("GROQ_API_KEY")

MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-20b"
)

MAX_AGENT_ITERATIONS = 10


if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is missing. "
        "Add it to the .env file."
    )