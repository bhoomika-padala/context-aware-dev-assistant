"""  python scripts/demo_two_sessions.py reset
     python scripts/demo_two_sessions.py session1
     (close the terminal, open a new one, activate the venv)
     python scripts/demo_two_sessions.py session2
     python scripts/demo_two_sessions.py show   """
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from memory import database as db, pipeline

db.DATABASE_PATH = db.PROJECT_ROOT / "demo_sessions.db"
PROJECT = "toy"

TRAJECTORY = """User: Users get 401 right after logging in, intermittently.
Agent: Read auth/jwt.py. The token is accepted without checking expiry.
Agent: Tried refreshing the token inside the middleware. Tests still failed: expired tokens passed.
Agent: Added an expiry check before authorization in verify_token(). Ran pytest: 12 passed.
Agent: Note: the session middleware runs before verify_token, so the check belongs in auth/ not in middleware."""

REQUEST = "Users are still able to use expired refresh tokens. Find out why."

mode = sys.argv[1] if len(sys.argv) > 1 else ""
if mode == "reset":
    db.DATABASE_PATH.unlink(missing_ok=True)
    print("reset")
elif mode == "session1":
    db.initialize_database()
    print(json.dumps(pipeline.record(PROJECT, TRAJECTORY), indent=2))
elif mode == "session2":
    db.initialize_database()
    prompt, used = pipeline.build_context(PROJECT, REQUEST)
    print(prompt)
    print(f"\nentries injected: {used}")
elif mode == "show":
    db.initialize_database()
    for m in db.list_memories(PROJECT, include_deprecated=True):
        print(f"#{m['id']} {m['category']:<22} {m['status']:<10} {m['description']}")
else:
    print(__doc__)