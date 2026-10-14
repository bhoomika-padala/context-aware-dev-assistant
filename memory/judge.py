import llm
import config

VERDICTS = {"same", "contradicts", "unrelated"}

SYSTEM = """You compare two pieces of project knowledge from the same software project.
Give one verdict for how NEW relates to EXISTING:
- same: essentially the same knowledge; NEW only rewords, refines or adds detail. (merge)
- contradicts: NEW replaces or reverses EXISTING (a decision changed, a rule no longer
  applies, a previously recommended approach is now known to be wrong). (retire the old one)
- unrelated: different knowledge, or both can be true at the same time. (keep both)
When unsure, answer unrelated.
Output ONLY JSON: {"verdict": "same" | "contradicts" | "unrelated"}"""


def judge(candidate, existing):
    """Plugs into update.consolidate(judge=...). Defaults to 'unrelated' (a plain ADD) when
    the model gives no usable answer, because that never destroys information."""
    user = (f"Category: {candidate['category']}\n\n"
            f"EXISTING:\n{existing['description']}: {existing['experience']}\n\n"
            f"NEW:\n{candidate['description']}: {candidate['experience']}")
    for _ in range(2):
        resp = llm.chat(SYSTEM, [{"role": "user", "content": user}],
                        json_mode=config.LLM_JSON_MODE)
        try:
            data = llm.parse_json(resp.text)
            verdict = str(data.get("verdict", "")).strip().lower()
        except (ValueError, AttributeError):
            continue
        if verdict in VERDICTS:
            return verdict
    return "unrelated"