import json
from types import SimpleNamespace as NS
import pytest
import llm

def client_returning(message):
    def create(**kw):
        create.kwargs = kw
        return NS(choices=[NS(message=message)])
    return NS(chat=NS(completions=NS(create=create))), create

def test_tool_call_is_parsed_and_request_shaped(monkeypatch):
    msg = NS(content=None, tool_calls=[NS(id="c1", function=NS(
        name="read_file", arguments=json.dumps({"path": "a.py"})))])
    client, create = client_returning(msg)
    monkeypatch.setattr(llm, "_client", client)
    tools = [{"name": "read_file", "description": "d",
              "parameters": {"type": "object", "properties": {}}}]
    resp = llm.chat("sys", [{"role": "user", "content": "hi"}], tools=tools)
    assert resp.tool_calls[0].name == "read_file" and resp.tool_calls[0].args == {"path": "a.py"}
    kw = create.kwargs
    assert kw["messages"][0] == {"role": "system", "content": "sys"}
    assert kw["tools"][0]["function"]["name"] == "read_file"

def test_malformed_tool_arguments_are_flagged_not_raised(monkeypatch):
    msg = NS(content="", tool_calls=[NS(id="c1", function=NS(name="x", arguments="{bad"))])
    monkeypatch.setattr(llm, "_client", client_returning(msg)[0])
    resp = llm.chat("s", [{"role": "user", "content": "q"}])
    assert "_parse_error" in resp.tool_calls[0].args

def test_message_helpers_round_trip():
    resp = llm.LLMResponse(text="", tool_calls=[llm.ToolCall("c1", "run_tests", {"k": 1})])
    m = llm.assistant_message(resp)
    assert m["tool_calls"][0]["function"]["arguments"] == '{"k": 1}'
    assert llm.tool_result_message("c1", "ok") == {"role": "tool", "tool_call_id": "c1", "content": "ok"}

def test_transient_error_is_retried(monkeypatch):
    class Rate(Exception):
        status_code = 429
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)
    calls = []
    def flaky():
        calls.append(1)
        if len(calls) == 1:
            raise Rate()
        return "ok"
    assert llm._with_retry(flaky) == "ok" and len(calls) == 2

def test_parse_json_handles_fences_and_prose():
    assert llm.parse_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert llm.parse_json('Sure! {"a": 1} Hope that helps') == {"a": 1}
    with pytest.raises(ValueError):
        llm.parse_json("no json here")