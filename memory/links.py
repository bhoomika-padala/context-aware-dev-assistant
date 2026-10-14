import config
from memory import database as db
from memory import retrieval as r

def _vec(m):
    return r.from_blob(m["embedding"]) if m["embedding"] else r.embed(r.entry_text(m))

def create_links(project_id, memory_id):
    """Link an entry to similar entries in OTHER categories (same-category near-duplicates
    are handled by EDIT instead). Degree-capped; returns [(other_id, similarity)]."""
    m = db.get_memory(memory_id)
    if m is None or m["status"] != "active":
        return []
    vec = _vec(m)
    scored = []
    for e in db.list_memories(project_id):
        if e["id"] == memory_id or e["category"] == m["category"]:
            continue
        sim = float(vec @ _vec(e))
        if sim >= config.THETA_LINK:
            scored.append((sim, e["id"]))
    scored.sort(reverse=True)
    made = []
    for sim, eid in scored[:config.MAX_LINKS]:
        db.add_link(memory_id, eid, sim, config.MAX_LINKS)
        made.append((eid, sim))
    return made

def expand(retrieved):
    """One-hop link expansion. Only entries that were actually scored seed the lookup.
    Entries included directly (conventions, architecture notes) do not, or their
    links would pull in unrelated experiences on every request."""
    seeds = [h["id"] for hs in retrieved.values() for h in hs if h.get("score") is not None]
    if not seeds:
        return retrieved
    have = {h["id"] for hs in retrieved.values() for h in hs}
    out = {c: list(hs) for c, hs in retrieved.items()}
    added = 0
    for row in db.linked_entries(seeds):
        if row["id"] in have:
            continue
        if added >= config.MAX_LINKED_IN_PROMPT:
            break
        out.setdefault(row["category"], []).append({
            "id": row["id"], "category": row["category"],
            "description": row["description"], "experience": row["experience"],
            "score": None, "linked": True, "link_similarity": row["link_sim"]})
        have.add(row["id"])
        added += 1
    return out