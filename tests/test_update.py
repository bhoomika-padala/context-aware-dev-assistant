import config
from memory import database as db, retrieval as r, links, update

def cand(cat, d, e, **kw):
    return {"category": cat, "description": d, "experience": e, **kw}

BUG = ("development_experience", "Intermittent 401 errors after login",
       "JWT expiry was not validated before authorizing requests; check token expiry first.")

def seed(project="p1"):
    i = db.add_memory(project, *BUG)
    r.index_memory(i)
    return i

def test_unrelated_candidate_is_added():
    seed()
    res = update.consolidate("p1", cand("development_experience", "Orders page loads slowly",
                                        "N+1 query; added eager loading."))
    assert res["action"] == "ADD" and len(db.list_memories("p1")) == 2

def test_near_duplicate_is_edited_not_duplicated():
    i = seed()
    res = update.consolidate("p1", cand(BUG[0], BUG[1],
        "JWT expiry was not validated before authorising requests; always check expiry, then refresh."))
    assert res["action"] == "EDIT" and res["id"] == i
    assert len(db.list_memories("p1")) == 1
    assert "refresh" in db.get_memory(i)["experience"]

def test_contradiction_deprecates_old_and_adds_new():
    old = db.add_memory("p1", "decision", "Primary database", "Chose PostgreSQL for JSON support")
    r.index_memory(old)
    res = update.consolidate("p1", cand("decision", "Primary database",
                                        "Switched to SQLite for simplicity"),
                             judge=lambda c, e: "contradicts")
    assert res["action"] == "DEPRECATE" and res["replaced"] == old
    assert db.get_memory(old)["status"] == "deprecated"
    assert len(db.list_memories("p1", category="decision")) == 1

def test_judge_not_called_for_dissimilar_candidates():
    seed(); calls = []
    update.consolidate("p1", cand(BUG[0], "Orders page loads slowly", "N+1 query."),
                       judge=lambda c, e: calls.append(1) or "same")
    assert calls == []

def test_bounded_cap_deprecates_oldest(monkeypatch):
    monkeypatch.setattr(config, "BOUNDED_CAP", 2)
    for d, e in [("Formatting", "Format with black"), ("API shape", "Return a data/error envelope")]:
        r.index_memory(db.add_memory("p1", "convention", d, e))
    res = update.consolidate("p1", cand("convention", "Typing", "Type-hint all public functions"))
    assert res["action"] == "ADD" and res["evicted"] is not None
    assert len(db.list_memories("p1", category="convention")) == 2

def test_added_entry_gets_linked():
    note = db.add_memory("p1", "architecture_note", "Authentication module",
                         "auth/ handles login and sessions and issues JWT access tokens.")
    r.index_memory(note)
    res = update.consolidate("p1", cand(*BUG))
    assert note in {b for b, _ in db.get_links(res["id"])}