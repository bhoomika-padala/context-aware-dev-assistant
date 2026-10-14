import pytest
import llm
from agent import loop
from memory import pipeline

def R(text="", calls=()):
    return llm.LLMResponse(text=text, tool_calls=list(calls))

def script(monkeypatch, *responses):
    it, seen = iter(responses), []
    def _chat(system, messages, **kw):
        seen.append(list(messages))
        return next(it)
    monkeypatch.setattr(llm, "chat", _chat)
    return seen

@pytest.fixture
def ws(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n")
    return tmp_path

def test_tool_then_answer_and_record(monkeypatch, ws):
    script(monkeypatch, R(calls=[llm.ToolCall("c1", "read_file", {"path": "a.py"})]), R("done"))
    recorded = {}
    monkeypatch.setattr(pipeline, "build_context", lambda p, r, code_context="": ("PROMPT", [7]))
    monkeypatch.setattr(pipeline, "record", lambda p, t: recorded.setdefault("t", t) and [])
    res = loop.run_task("p1", "fix it", workspace=ws)
    assert res["answer"] == "done" and res["steps"] == 2 and res["injected"] == [7]
    assert "read_file" in recorded["t"] and "User: fix it" in recorded["t"]

def test_memory_off_never_touches_memory(monkeypatch, ws):
    script(monkeypatch, R("done"))
    def boom(*a, **k): raise AssertionError("memory used")
    monkeypatch.setattr(pipeline, "build_context", boom)
    monkeypatch.setattr(pipeline, "record", boom)
    res = loop.run_task("p1", "q", use_memory=False, workspace=ws)
    assert res["answer"] == "done" and res["injected"] == [] and res["memory_updates"] is None

def test_step_limit(monkeypatch, ws):
    forever = R(calls=[llm.ToolCall("c", "list_files", {})])
    script(monkeypatch, *[forever] * 10)
    res = loop.run_task("p1", "q", use_memory=False, workspace=ws, max_steps=3)
    assert "Stopped after 3 steps" in res["answer"] and res["steps"] == 3

def test_malformed_tool_arguments_go_back_to_the_model(monkeypatch, ws):
    seen = script(monkeypatch, R(calls=[llm.ToolCall("c1", "read_file", {"_parse_error": "{bad"})]),
                  R("ok"))
    loop.run_task("p1", "q", use_memory=False, workspace=ws)
    assert seen[1][-1]["content"].startswith("Error")

def test_record_failure_does_not_lose_the_answer(monkeypatch, ws):
    script(monkeypatch, R("done"))
    monkeypatch.setattr(pipeline, "build_context", lambda p, r, code_context="": ("P", []))
    def fail(p, t): raise RuntimeError("rate limited")
    monkeypatch.setattr(pipeline, "record", fail)
    res = loop.run_task("p1", "q", workspace=ws)
    assert res["answer"] == "done" and "rate limited" in res["memory_error"]