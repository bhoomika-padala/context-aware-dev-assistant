import config
from memory import composer, pipeline, retrieval as r
from memory import database as db

def hits(n, cat="decision"):
    return [{"id": i, "category": cat, "description": f"decision {i}",
             "experience": "x" * 80, "score": 1 - i / 10} for i in range(n)]

def test_budget_is_respected(monkeypatch):
    monkeypatch.setitem(config.CATEGORY_BUDGET_TOKENS, "decision", 50)
    prompt, used = composer.compose("req", {"decision": hits(10)})
    assert used == [0, 1]          # ~23 tokens each, only two fit in 50

def test_empty_memory_has_no_memory_section():
    prompt, used = composer.compose("fix the bug", {})
    assert "Project memory" not in prompt
    assert "fix the bug" in prompt and used == []

def test_request_always_present_even_with_zero_budget(monkeypatch):
    monkeypatch.setitem(config.CATEGORY_BUDGET_TOKENS, "decision", 0)
    prompt, used = composer.compose("my request", {"decision": hits(3)})
    assert "my request" in prompt and used == []

def test_stable_categories_come_before_scored_ones():
    retrieved = {"decision": hits(1),
                 "convention": hits(1, "convention")}
    prompt, _ = composer.compose("req", retrieved)
    assert prompt.index("Project conventions") < prompt.index("Past decisions")

def test_get_context_marks_used_entries():
    i = db.add_memory("p1", "decision", "Choice of database",
                      "Chose PostgreSQL for JSON support")
    r.index_memory(i)
    assert db.get_memory(i)["last_used_at"] is None
    prompt = pipeline.get_context("p1", "which database did we choose?")
    assert "PostgreSQL" in prompt
    assert db.get_memory(i)["last_used_at"] is not None
    