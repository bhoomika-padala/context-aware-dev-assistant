from agent import tools


def run_turn(
    project_id,
    user_message,
    responder,
    memory_limit=None,
    memory_to_record=None,
):
    """Run one assistant turn using only the agent's memory tools."""
    if not callable(responder):
        raise TypeError("responder must be callable")

    if memory_limit is None:
        context = tools.get_context(project_id, user_message)
    else:
        context = tools.get_context(project_id, user_message, limit=memory_limit)

    response = responder(user_message, context)
    memory_id = None
    if memory_to_record is not None:
        memory_id = tools.record(project_id=project_id, **memory_to_record)

    return {
        "response": response,
        "context": context,
        "memory_id": memory_id,
    }
