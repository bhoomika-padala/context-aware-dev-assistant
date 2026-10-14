from memory import retrieval, composer
from memory import database as db

def build_context(project_id, request, code_context="", categories=None):
    """Returns (prompt, used_ids). The ids are useful for evaluation logging."""
    retrieved = retrieval.retrieve(project_id, request, categories)
    prompt, used = composer.compose(request, retrieved, code_context)
    db.mark_used(used)   # refreshes recency only for entries actually injected
    return prompt, used

def get_context(project_id, request, code_context="", categories=None):
    """The integration point: called by the agent before a task."""
    return build_context(project_id, request, code_context, categories)[0]