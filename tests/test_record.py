import json
from memory import database as db, pipeline

def dec(exp):
    return {"category": "decision", "description": "Primary database", "experience": exp}

def test_empty_extraction_writes_nothing():
    assert pipeline.record("p1", "t", extractor=lambda t: []) == []
    assert db.list_memories("p1") == []

def test_flipped_decision_retires_the_old_one():
    pipeline.record("p1", "t", extractor=lambda t: [dec("Chose PostgreSQL for JSON support")])
    log = pipeline.record("p1", "t", extractor=lambda t: [dec("Switched to SQLite")],
                          judge_fn=lambda c, e: "contradicts")
    assert log[0]["action"] == "DEPRECATE"
    active = db.list_memories("p1", category="decision")
    assert len(active) == 1 and "SQLite" in active[0]["experience"]

def test_task_state_follows_the_extractor():
    task = lambda state: {"category": "task", "description": "Password reset flow",
                          "experience": "Token generation", "task_state": state}
    pipeline.record("p1", "t", extractor=lambda t: [task("open")])
    pipeline.record("p1", "t", extractor=lambda t: [task("resolved")],
                    judge_fn=lambda c, e: "same")
    assert db.list_memories("p1", category="task")[0]["task_state"] == "resolved"

def test_full_chain_with_fake_model(fake_llm):
    fake_llm(json.dumps({"candidates": [dec("Chose PostgreSQL")]}))
    log = pipeline.record("p1", "transcript")
    assert log[0]["action"] == "ADD" and len(db.list_memories("p1")) == 1