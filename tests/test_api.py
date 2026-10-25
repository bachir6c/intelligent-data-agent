import os

os.environ.setdefault(
    "GROQ_API_KEY",
    "test-key"
)

from fastapi.testclient import TestClient

import api.main as api_main


client = TestClient(api_main.app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok"
    }


def test_query_endpoint(monkeypatch):
    def fake_query_agent(question):
        return {
            "answer": "Cash Deposit",
            "tools": [
                "detect_trend_anomalies"
            ],
            "chart_path": None
        }

    monkeypatch.setattr(
        api_main,
        "query_agent",
        fake_query_agent
    )

    response = client.post(
        "/query",
        json={
            "question": (
                "Which operation type shows "
                "a progressive increase?"
            )
        }
    )

    assert response.status_code == 200

    assert response.json() == {
        "answer": "Cash Deposit",
        "tools": [
            "detect_trend_anomalies"
        ],
        "chart_path": None
    }