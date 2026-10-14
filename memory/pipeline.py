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