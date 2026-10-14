from memory.database import add_memory


def record(
    project_id,
    category,
    description,
    experience,
    task_state=None,
    embedding=None,
):
    """Persist one explicitly supplied memory and return its database ID."""
    return add_memory(
        project_id=project_id,
        category=category,
        description=description,
        experience=experience,
        task_state=task_state,
        embedding=embedding,
    )
