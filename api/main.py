import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


SRC_PATH = Path(__file__).resolve().parents[1] / "src"
sys.path.append(str(SRC_PATH))

from agent_service import query_agent
from document_tools import save_document


app = FastAPI(
    title="Intelligent Data Agent API",
    version="2.0"
)


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=10000, pattern=r"\S")


class QueryResponse(BaseModel):
    answer: str
    tools: list[str]
    chart_path: str | None = None


class DocumentRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=160)
    content: str = Field(min_length=1, max_length=1_000_000)


@app.post("/documents", status_code=201)
def upload_document(request: DocumentRequest):
    try:
        return save_document(request.filename, request.content)
    except FileExistsError:
        raise HTTPException(status_code=409, detail="A document with this name already exists.")
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


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
