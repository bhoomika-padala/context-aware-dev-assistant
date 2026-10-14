import config
import llm
from memory import database as db

SYSTEM = """You maintain the long-term project memory of a software-engineering agent.
You are given the transcript of one finished task. Decide what, if anything, is worth
remembering for FUTURE tasks in this project.

Categories (use exactly these names):
- development_experience: a problem, what was tried (including failed attempts) and what worked.
- decision: a technical choice and why it was made.
- convention: a project-wide coding rule or practice.
- architecture_note: a durable structural fact (which module does what, how parts depend on each other).
- task: unfinished or follow-up work. Add "task_state": open | in_progress | resolved.

Rules:
- Return at most 3 candidates. Fewer is better. Return an empty list if nothing is reusable.
- Keep only knowledge that would help on a different, future task. Skip one-off details,
  small talk, and anything obvious from the code itself.
- "description": the situation or topic BEFORE the resolution, one sentence.
  "experience": the reusable insight, one or two sentences.
- Do not copy raw logs, stack traces, line numbers or temporary paths. Keep module or
  directory names when they matter (for example in architecture notes).
- Record failed attempts as development_experience and say that the approach failed and why.
- Only record what the transcript supports. If it does not show that the fix worked, say so.
- Never include secrets, tokens or API keys.
- Record each fact ONCE, in the single best-fitting category. Never restate the same
  insight as an experience, a decision and an architecture note.
- Do not record routine successful work (a migration, an install, a rename) unless the
  transcript shows a failed attempt, a surprise, or a rule worth keeping.
- A development_experience needs a problem and what actually happened, especially failures
  or surprises. Prefer an architecture_note when the lesson is a structural fact.

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