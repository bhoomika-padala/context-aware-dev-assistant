import config
from memory import database as db
from memory import retrieval as r
from memory import links

def _vec(m):
    return r.from_blob(m["embedding"]) if m["embedding"] else r.embed(r.entry_text(m))

def _most_similar(project_id, category, vec, desc_vec):
    """Best match by full text, plus the best description-only match."""
    best, best_sim, best_dsim = None, -1.0, -1.0
    for e in db.list_memories(project_id, category=category):
        sim = float(vec @ _vec(e))
        dsim = float(desc_vec @ r.embed(e["description"]))
        # rank by the stronger of the two signals
        if max(sim, dsim) > max(best_sim, best_dsim):
            best, best_sim, best_dsim = e, sim, dsim
    return best, best_sim, best_dsim

def _make_room(project_id, category):
    """Bounded categories are capped. Over the cap, the oldest entry is deprecated
    (kept, flagged), never hard-deleted."""
    if category not in config.BOUNDED:
        return None
    active = db.list_memories(project_id, category=category)
    if len(active) < config.BOUNDED_CAP:
        return None
    oldest = min(active, key=lambda m: (m["updated_at"], m["id"]))
    db.deprecate_memory(oldest["id"])
    return oldest["id"]

def consolidate(project_id, candidate, judge=None):
    """Decide ADD / EDIT / DEPRECATE for one candidate {category, description, experience}.
    judge(candidate, existing) -> 'same' | 'contradicts' | 'unrelated' is a hook for the
    LLM contradiction check. Without it, similarity alone decides ADD vs EDIT."""
    cat = candidate["category"]
    if cat not in db.MEMORY_CATEGORIES:
        raise ValueError(f"Unknown category: {cat}")
    vec = r.embed(f"{candidate['description']} {candidate['experience']}")
    desc_vec = r.embed(candidate["description"])
    existing, sim, dsim = _most_similar(project_id, cat, vec, desc_vec)

    action = "ADD"
    if existing is not None:
        if judge is not None:
            if max(sim, dsim) >= config.THETA_JUDGE:
                verdict = judge(candidate, existing)
                action = {"same": "EDIT", "contradicts": "DEPRECATE"}.get(verdict, "ADD")
        elif sim >= config.THETA_DUP:
            action = "EDIT"

    if action == "EDIT":
        db.edit_memory(existing["id"], candidate["description"],
                       candidate["experience"], r.to_blob(vec))
        db.clear_links(existing["id"])              # old links may be stale
        links.create_links(project_id, existing["id"])
        return {"action": "EDIT", "id": existing["id"], "replaced": None,
                "evicted": None, "similarity": sim}

    replaced = None
    if action == "DEPRECATE":
        db.deprecate_memory(existing["id"])
        replaced = existing["id"]
    evicted = _make_room(project_id, cat)
    new_id = db.add_memory(project_id, cat, candidate["description"],
                           candidate["experience"],
                           task_state=candidate.get("task_state"),
                           embedding=r.to_blob(vec))
    links.create_links(project_id, new_id)
    return {"action": action, "id": new_id, "replaced": replaced,
            "evicted": evicted, "similarity": sim}