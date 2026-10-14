import pytest
from memory import database as db, retrieval as r

def test_task_transitions():
    t = db.add_memory("p1", "task", "Add reset", "wip")
    db.set_task_state(t, "in_progress")
    db.set_task_state(t, "resolved")
    assert db.get_memory(t)["task_state"] == "resolved"
    with pytest.raises(ValueError):
        db.set_task_state(t, "in_progress")        # resolved can only reopen
    db.set_task_state(t, "open")

def test_non_task_has_no_state():
    d = db.add_memory("p1", "decision", "x", "y")
    with pytest.raises(ValueError):
        db.set_task_state(d, "resolved")

def test_resolved_tasks_rank_below_open_ones():
    done = db.add_memory("p1", "task", "Password reset token expiry", "Finished and shipped")
    todo = db.add_memory("p1", "task", "Password reset token expiry", "Finished and shipped")
    for i in (done, todo):
        r.index_memory(i)
    db.set_task_state(done, "resolved")
    hits = r.retrieve("p1", "password reset token expiry")["task"]
    assert [h["id"] for h in hits] == [todo, done]  # without the factor, ties keep id order