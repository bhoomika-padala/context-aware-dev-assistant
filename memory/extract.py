import config
import llm
from memory import database as db


SYSTEM = """You maintain the long-term project memory of a software-engineering agent.

You receive either user-provided project information or a completed coding-task
transcript. Extract reusable knowledge for future tasks.

Categories:
- development_experience: a problem, what was tried, and what happened.
- decision: an explicitly stated technical choice and its reason.
- convention: an explicitly stated project-wide coding rule or practice.
- architecture_note: a stated structural fact about modules and dependencies.
- task: unfinished or follow-up work. Include task_state: open | in_progress | resolved.

Rules:
- Return at most 3 candidates. Fewer is better. Return [] if nothing is reusable.
- For user-provided project information, preserve the facts and classify them
  into the most appropriate categories.
- Do not require the user to explicitly say "remember" or "store".
- Do not invent decisions, reasons, architecture, or conventions.
- An implementation detail is not automatically a team decision.
- A coding convention must be supported by an explicit project rule or practice.
- Record each fact once, in its single best-fitting category.
- Keep knowledge useful for future tasks.
- Do not copy logs, stack traces, temporary paths, secrets, tokens or API keys.
- For development experiences, only claim a fix worked when the transcript
  supports that conclusion.
- Description: one sentence describing the topic or situation.
- Experience: one or two sentences describing the reusable knowledge.

Output ONLY a JSON object:
{"candidates": [{"category": "...", "description": "...", "experience": "..."}]}"""


def _clip(text):
    n = config.TRAJECTORY_MAX_CHARS
    if len(text) <= n:
        return text
    return text[: n // 2] + "\n...[middle omitted]...\n" + text[-n // 2:]


def _validate(data):
    items = data.get("candidates") if isinstance(data, dict) else None
    if not isinstance(items, list):
        raise ValueError("'candidates' must be a list")
    out, seen = [], set()
    for it in items:
        if not isinstance(it, dict):
            continue
        cat = str(it.get("category", "")).strip()
        desc = str(it.get("description", "")).strip()
        exp = str(it.get("experience", "")).strip()
        if cat not in db.MEMORY_CATEGORIES or not desc or not exp:
            continue
        key = (cat, desc.lower())
        if key in seen:
            continue
        seen.add(key)
        cand = {"category": cat, "description": desc[:300], "experience": exp[:600]}
        if cat == "task":
            state = str(it.get("task_state", "open")).strip()
            cand["task_state"] = state if state in db.TASK_STATES else "open"
        out.append(cand)
        if len(out) >= config.MAX_CANDIDATES:
            break
    return out


def extract_candidates(trajectory):
    """Trajectory text -> list of validated candidates. One retry on invalid output;
    returns [] if the model still fails (nothing is written)."""
    messages = [{"role": "user",
                 "content": "Task transcript:\n" + _clip(trajectory) + "\n\nReturn the JSON now."}]
    for _ in range(2):
        resp = llm.chat(SYSTEM, messages, json_mode=config.LLM_JSON_MODE)
        try:
            return _validate(llm.parse_json(resp.text))
        except ValueError as err:
            messages += [
                {"role": "assistant", "content": resp.text or "(empty)"},
                {"role": "user", "content": f"That was not valid ({err}). "
                                            "Reply with only the JSON object."},
            ]
    return []