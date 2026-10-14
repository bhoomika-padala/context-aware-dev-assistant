import pytest
from memory import database as db, retrieval as r, links, pipeline

def add(cat, d, e, project="p1"):
    i = db.add_memory(project, cat, d, e)
    r.index_memory(i)
    return i

AUTH_NOTE = ("architecture_note", "Authentication module",
             "auth/ handles login and sessions and issues JWT access tokens.")
JWT_BUG = ("development_experience", "Intermittent 401 errors after login",
           "JWT expiry was not validated before authorizing requests.")
CELERY_TASK = ("task", "Add retries to Celery email jobs",
               "Redis queue workers need a retry policy.")

def test_links_created_across_categories_and_mutual():
    note = add(*AUTH_NOTE); celery = add(*CELERY_TASK); bug = add(*JWT_BUG)
    made = [i for i, _ in links.create_links("p1", bug)]
    assert note in made and celery not in made
    assert bug in {b for b, _ in db.get_links(note)}          # both directions

def test_same_category_entries_are_not_linked():
    add("decision", "Choice of database", "Chose PostgreSQL for JSON support")
    b = add("decision", "Database for analytics", "Use PostgreSQL read replicas")
    assert links.create_links("p1", b) == []

def test_degree_cap_drops_lowest_similarity():
    ids = [db.add_memory("p1", "decision", f"d{i}", "x") for i in range(5)]
    hub = ids[0]
    for sim, other in zip([0.9, 0.8, 0.7, 0.6], ids[1:]):
        db.add_link(hub, other, sim, max_links=3)
    assert {b for b, _ in db.get_links(hub)} == {ids[1], ids[2], ids[3]}
    assert db.get_links(ids[4]) == []                          # reverse row removed too

def test_deprecating_removes_links():
    a = db.add_memory("p1", "decision", "a", "x")
    b = db.add_memory("p1", "task", "b", "y")
    db.add_link(a, b, 0.9, 5)
    db.deprecate_memory(a)
    assert db.get_links(b) == []

def test_one_hop_expansion_adds_linked_entry():
    bug = add(*JWT_BUG); note = add(*AUTH_NOTE)
    links.create_links("p1", bug)
    res = r.retrieve("p1", "401 after login token expiry", categories=("development_experience",))
    assert "architecture_note" not in res
    expanded = links.expand(res)
    assert any(h["id"] == note and h.get("linked") for h in expanded["architecture_note"])

def test_directly_included_entries_do_not_seed_expansion():
    bug = add(*JWT_BUG); note = add(*AUTH_NOTE)
    links.create_links("p1", bug)
    res = r.retrieve("p1", "recipe for banana bread")          # only the note, included directly
    assert "development_experience" not in links.expand(res)

def test_expansion_can_be_switched_off():
    bug = add(*JWT_BUG); add(*AUTH_NOTE)
    links.create_links("p1", bug)
    q = "401 after login token expiry"
    on, _ = pipeline.build_context("p1", q, categories=("development_experience",))
    off, _ = pipeline.build_context("p1", q, categories=("development_experience",),
                                    expand_links=False)
    assert "Authentication module" in on and "Authentication module" not in off