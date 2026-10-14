import config

# bounded, stable knowledge first, then the scored categories
ORDER = ("convention", "architecture_note", "decision",
         "development_experience", "task")
LABELS = {
    "convention": "Project conventions",
    "architecture_note": "Architecture notes",
    "decision": "Past decisions",
    "development_experience": "Relevant past experiences",
    "task": "Related tasks",
}

def est_tokens(text):
    return max(1, len(text) // config.CHARS_PER_TOKEN)

def _line(h):
    return f"- {h['description']}: {h['experience']}"

def compose(request, retrieved, code_context=""):
    """Build the prompt. Returns (prompt, ids_of_entries_included).
    Entries that don't fit a category budget are dropped from this prompt only."""
    sections, used = [], []
    for cat in ORDER:
        hits = retrieved.get(cat)
        if not hits:
            continue
        budget, spent, lines = config.CATEGORY_BUDGET_TOKENS[cat], 0, []
        for h in hits:  # already in score order (or recency for bounded)
            line = _line(h)
            cost = est_tokens(line)
            if spent + cost > budget:
                continue          # skip this one, a shorter later entry may still fit
            lines.append(line)
            spent += cost
            used.append(h["id"])
        if lines:
            sections.append(f"### {LABELS[cat]}\n" + "\n".join(lines))

    parts = []
    if sections:
        parts.append("## Project memory (from earlier sessions)\n"
                     + "\n\n".join(sections))
    if code_context:
        parts.append("## Current code context\n" + code_context)
    parts.append("## Developer request\n" + request)
    return "\n\n".join(parts), used