from memory import retrieval, composer, links
from memory import database as db

def build_context(project_id, request, code_context="", categories=None, expand_links=True):
    retrieved = retrieval.retrieve(project_id, request, categories)
    if expand_links:
        retrieved = links.expand(retrieved)
    prompt, used = composer.compose(request, retrieved, code_context)
    db.mark_used(used)
    return prompt, used

def get_context(project_id, request, code_context="", categories=None, expand_links=True):
    return build_context(project_id, request, code_context, categories, expand_links)[0]

def record(project_id, trajectory, judge_fn=None, extractor=None):
    """Integration point 2: called by the agent after a task.
    Returns a log of what happened to each candidate (useful for review and evaluation)."""
    from memory import extract, judge, update
    extractor = extractor or extract.extract_candidates
    judge_fn = judge_fn or judge.judge
    log = []
    for cand in extractor(trajectory):
        res = update.consolidate(project_id, cand, judge=judge_fn)
        if cand["category"] == "task" and res["action"] == "EDIT":
            try:    # proposed transition; the developer confirms or overrides in the UI later
                db.set_task_state(res["id"], cand.get("task_state", "open"))
            except ValueError:
                pass
        log.append({"candidate": cand, **res})
    return log