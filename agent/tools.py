from memory.retrieval import get_context as _get_context
from memory.update import record as _record


def get_context(project_id, query, limit=None):
    if limit is None:
        return _get_context(project_id, query)
    return _get_context(project_id, query, limit=limit)


def record(
    project_id,
    category,
    description,
    experience,
    task_state=None,
):
    return _record(
        project_id,
        category,
        description,
        experience,
        task_state=task_state,
    )
