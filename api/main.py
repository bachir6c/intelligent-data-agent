import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


SRC_PATH = Path(__file__).resolve().parents[1] / "src"
sys.path.append(str(SRC_PATH))

from agent_service import query_agent


app = FastAPI(
    title="Intelligent Data Agent API",
    version="2.0"
)


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str
    tools: list[str]
    chart_path: str | None = None


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


@app.post(
    "/query",
    response_model=QueryResponse
)
def query(request: QueryRequest):

    try:
        result = query_agent(
            request.question
        )

        return result

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )