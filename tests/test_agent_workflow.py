"""Exercise the real tool loop with a simulated model; no API key is needed."""
import json
from types import SimpleNamespace

import agent
import document_tools


def completion(content=None, calls=None):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
        content=content, tool_calls=calls or []))])


def tool_call(name, arguments, identifier):
    return SimpleNamespace(id=identifier, function=SimpleNamespace(
        name=name, arguments=json.dumps(arguments)))


def test_optional_null_settings_use_python_defaults(monkeypatch):
    received = {}

    def fake_detector(**kwargs):
        received.update(kwargs)
        return {"success": True}

    monkeypatch.setattr(agent, "detect_channel_anomalies", fake_detector)
    agent.call_tool("detect_channel_anomalies", {
        "operation_type_id": 4, "start_date": "2026-08-01",
        "end_date": "2026-08-31", "channel": "Mobile", "agency_id": None,
        "z_threshold": None, "min_transaction_count": None,
    })
    assert received["z_threshold"] == 3.0
    assert received["min_transaction_count"] == 10
    schema = next(tool["function"]["parameters"] for tool in agent.tools
                  if tool["function"]["name"] == "detect_channel_anomalies")
    assert "null" in schema["properties"]["z_threshold"]["type"]


def test_hybrid_question_uses_sql_and_document_passages(monkeypatch, tmp_path):
    monkeypatch.setattr(document_tools, "DOCUMENT_DIR", tmp_path)
    document_tools.save_document("policy.txt", "Mobile transfers require supervisor approval.")
    responses = iter([
        completion(calls=[
            tool_call("execute_sql", {"query": "SELECT COUNT(*) AS total FROM transactions"}, "sql"),
            tool_call("search_documents", {"query": "Mobile transfer approval"}, "docs"),
        ]),
        completion("Transactions counted. Mobile transfers require supervisor approval [policy.txt#1]."),
    ])
    requests = []

    def fake_model(**kwargs):
        requests.append(list(kwargs["messages"]))
        return next(responses)

    monkeypatch.setattr(agent.client.chat.completions, "create", fake_model)
    result = agent.run_agent("Count transactions and explain Mobile approval.", return_trace=True, verbose=False)
    assert result["tools"] == ["execute_sql", "search_documents"]
    tool_results = [json.loads(m["content"]) for m in requests[1] if isinstance(m, dict) and m.get("role") == "tool"]
    assert tool_results[0]["success"] is True
    assert tool_results[1]["matches"][0]["citation"] == "[policy.txt#1]"


def test_sql_error_is_returned_to_model_for_retry(monkeypatch):
    responses = iter([
        completion(calls=[tool_call("execute_sql", {"query": "SELECT missing FROM missing_table"}, "bad")]),
        completion(calls=[tool_call("execute_sql", {"query": "SELECT 1 AS value"}, "fixed")]),
        completion("The result is 1."),
    ])
    requests = []

    def fake_model(**kwargs):
        requests.append(list(kwargs["messages"]))
        return next(responses)

    monkeypatch.setattr(agent.client.chat.completions, "create", fake_model)
    result = agent.run_agent("Run a query", return_trace=True, verbose=False)
    assert result["tools"] == ["execute_sql", "execute_sql"]
    first_result = [m for m in requests[1] if isinstance(m, dict) and m.get("role") == "tool"][0]
    assert json.loads(first_result["content"])["success"] is False
