import json
from pathlib import Path

import config
import llm
from agent import tools
from memory import pipeline

SYSTEM = """You are a software engineering agent working in a project workspace.
- Read the relevant code before editing, and make the smallest change that fixes the problem.
- After a change, run the tests. Never claim a fix works unless the tests passed.
- If an attempt fails, say so and say what you tried.
- When done, reply with a short plain-text summary: what was wrong, what you changed,
  and whether the tests passed.
If background from earlier sessions is included in the request, use what is relevant,
ignore what is not, and verify it against the actual code."""


def _clip(text, n=500):
    text = str(text)
    return text if len(text) <= n else text[:n] + " ...[truncated]"


def run_task(project_id, request, use_memory=True, workspace=None, max_steps=None):
    """Host agent for the memory layer. The memory layer is used only through
    pipeline.build_context() before the task and pipeline.record() after it."""
    root = Path(workspace) if workspace else config.WORKSPACE_DIR
    max_steps = max_steps or config.MAX_AGENT_STEPS
    code_context = "Files in the workspace:\n" + tools.list_files(root)

    if use_memory:
        prompt, injected = pipeline.build_context(project_id, request, code_context=code_context)
    else:   # identical layout minus the memory section, so memory is the only variable
        prompt = f"## Current code context\n{code_context}\n\n## Developer request\n{request}"
        injected = []

    messages = [{"role": "user", "content": prompt}]
    trace = [f"User: {request}"]
    answer, steps = "", 0
    for steps in range(1, max_steps + 1):
        resp = llm.chat(SYSTEM, messages, tools=tools.TOOLS)
        messages.append(llm.assistant_message(resp))
        if not resp.tool_calls:
            answer = resp.text.strip() or "(no answer)"
            break
        for call in resp.tool_calls:
            if "_parse_error" in call.args:
                result = "Error: tool arguments were not valid JSON. Send a JSON object."
            else:
                result = tools.execute(root, call.name, call.args)
            trace.append(f"Agent: {call.name}({_clip(json.dumps(call.args), 200)})")
            trace.append(f"Tool result: {_clip(result)}")
            messages.append(llm.tool_result_message(call.id, result))
    else:
        answer = f"Stopped after {max_steps} steps without a final answer."
    trace.append(f"Agent: {answer}")

    updates, memory_error = None, None
    if use_memory:
        try:
            updates = pipeline.record(project_id, "\n".join(trace))
        except Exception as e:      # a memory problem must not lose the agent's answer
            memory_error = f"{type(e).__name__}: {e}"
    return {"answer": answer, "prompt": prompt, "injected": injected,
            "memory_updates": updates, "memory_error": memory_error, "steps": steps,"trace": trace}

