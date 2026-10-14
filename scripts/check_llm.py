"""  python scripts/check_llm.py ping | extract | judge  """
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import llm
from memory import extract, judge

TRAJECTORIES = {
"bugfix": """User: Users get 401 right after logging in, intermittently.
Agent: Read auth/jwt.py. The token is accepted without checking expiry.
Agent: Tried refreshing the token inside the middleware. Tests still failed: expired tokens passed.
Agent: Added an expiry check before authorization in verify_token(). Ran pytest: 12 passed.
Agent: Note: the session middleware runs before verify_token, so the check belongs in auth/ not in middleware.""",
"decision": """User: We keep fighting SQLite write locks. Let's use PostgreSQL instead.
Agent: Updated the connection settings and migration scripts for PostgreSQL. Tests pass.
User: Good. From now on all new tables need an explicit created_at column.""",
"trivial": """User: What does the len function do?
Agent: It returns the number of items in a container.""",
}

PAIRS = [
    ("same", {"category": "decision", "description": "Primary database",
              "experience": "Use PostgreSQL because it handles concurrent writes and JSON."},
     {"description": "Primary database", "experience": "Chose PostgreSQL for JSON support"}),
    ("contradicts", {"category": "decision", "description": "Primary database",
                     "experience": "Switched to SQLite for simplicity"},
     {"description": "Primary database", "experience": "Chose PostgreSQL for JSON support"}),
    ("unrelated", {"category": "convention", "description": "Code style",
                   "experience": "Format with black"},
     {"description": "Primary database", "experience": "Chose PostgreSQL for JSON support"}),
]

cmd = sys.argv[1] if len(sys.argv) > 1 else ""
if cmd == "ping":
    print(llm.chat("Reply with one word.", [{"role": "user", "content": "Say ok"}]))
elif cmd == "extract":
    for name, traj in TRAJECTORIES.items():
        print(f"\n=== {name} ===")
        print(json.dumps(extract.extract_candidates(traj), indent=2))
elif cmd == "judge":
    for expected, cand, existing in PAIRS:
        print(f"expected={expected:<12} got={judge.judge(cand, existing)}")
else:
    print(__doc__)