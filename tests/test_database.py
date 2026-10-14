import pytest
from memory import database as db

@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATABASE_PATH", tmp_path / "test.db")
    db.initialize_database()

def test_add_and_get():
    mid = db.add_memory("p1", "development_experience",
                        "Expired tokens cause failures",
                        "Check token expiry before authorizing.")
    m = db.get_memory(mid)
    assert m["description"] == "Expired tokens cause failures"
    assert m["status"] == "active"

def test_deprecated_excluded_by_default():
    a = db.add_memory("p1", "decision", "Use PostgreSQL", "Chosen for JSON support")
    b = db.add_memory("p1", "decision", "Use SQLite", "Chosen for simplicity")
    assert db.deprecate_memory(a) is True
    assert [m["id"] for m in db.list_memories("p1")] == [b]
    assert len(db.list_memories("p1", include_deprecated=True)) == 2
    assert db.get_memory(a)["status"] == "deprecated"

def test_deprecate_missing_or_twice_returns_false():
    assert db.deprecate_memory(999) is False
    mid = db.add_memory("p1", "convention", "x", "y")
    assert db.deprecate_memory(mid) is True
    assert db.deprecate_memory(mid) is False

def test_invalid_category_rejected():
    with pytest.raises(ValueError):
        db.add_memory("p1", "bogus", "x", "y")

def test_task_defaults_to_open_and_projects_isolated():
    tid = db.add_memory("p1", "task", "Add login", "Unfinished")
    assert db.get_memory(tid)["task_state"] == "open"
    assert db.list_memories("p2") == []