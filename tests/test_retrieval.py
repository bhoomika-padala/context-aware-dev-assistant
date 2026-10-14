import time
import pytest
from memory import database as db
from memory import retrieval as r

SEED = [
    ("development_experience", "Login fails intermittently with 401 errors",
     "JWT expiry was not checked before authorizing; validate token expiry first."),
    ("development_experience", "Slow dashboard queries on the orders page",
     "Added an index on orders.customer_id and removed an N+1 query."),
    ("development_experience", "ImportError in parse_config after refactor",
     "Circular import between config_loader and settings; moved constants to constants.py."),
    ("decision", "Choice of primary database",
     "Chose PostgreSQL over SQLite for concurrent writes and JSON support."),
    ("decision", "Frontend state management",
     "Use Redux Toolkit rather than Context for shared state."),
    ("convention", "API response format",
     "All endpoints return a {data, error} JSON envelope."),
    ("architecture_note", "Authentication module",
     "auth/ handles login, depends on session middleware, and uses JWT."),
    ("task", "Add password reset",
     "Email flow partially implemented; token generation still pending."),
]

@pytest.fixture
def seeded():
    ids = []
    for cat, d, e in SEED:
        i = db.add_memory("p1", cat, d, e)
        r.index_memory(i)
        ids.append(i)
    return ids

def top(result, cat):
    return result[cat][0]["description"]

def test_semantic_match_with_different_wording(seeded):
    res = r.retrieve("p1", "users get rejected at login because their token is stale")
    assert "Login fails" in top(res, "development_experience")

def test_semantic_decision(seeded):
    res = r.retrieve("p1", "which relational database did we pick?")
    assert "primary database" in top(res, "decision")

def test_exact_identifier_match(seeded):
    res = r.retrieve("p1", "parse_config ImportError")
    assert "parse_config" in top(res, "development_experience")

def test_irrelevant_query_returns_nothing_for_scored_categories(seeded):
    res = r.retrieve("p1", "recipe for banana bread")
    for cat in ("development_experience", "decision", "task"):
        assert cat not in res

def test_bounded_categories_included_directly(seeded):
    res = r.retrieve("p1", "recipe for banana bread")
    assert "convention" in res and "architecture_note" in res

def test_deprecated_entries_excluded(seeded):
    db.deprecate_memory(seeded[3])  # PostgreSQL decision
    res = r.retrieve("p1", "which relational database did we pick?")
    assert "decision" not in res or all(
        "PostgreSQL" not in h["experience"] for h in res["decision"])

def test_retrieval_time_is_small(seeded):
    r.retrieve("p1", "warm up")  # first call loads the model
    t = time.perf_counter()
    r.retrieve("p1", "login token expired")
    assert time.perf_counter() - t < 1.0

