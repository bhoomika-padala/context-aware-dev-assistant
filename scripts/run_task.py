"""  python scripts/run_task.py "request"  [--no-memory]
     Uses MEMORY_DB (default demo_agent.db) so your real data is untouched."""
import json
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from memory import database as db
db.DATABASE_PATH = db.PROJECT_ROOT / os.environ.get("MEMORY_DB", "demo_agent.db")
db.initialize_database()
from agent.loop import run_task

args = [a for a in sys.argv[1:] if a != "--no-memory"]
if not args:
    print(__doc__); sys.exit()
r = run_task("toy", " ".join(args), use_memory="--no-memory" not in sys.argv)
print("\n===== PROMPT =====\n" + r["prompt"])
print("\n===== ANSWER =====\n" + r["answer"])
print(f"\nsteps={r['steps']} injected={r['injected']}")
print("memory updates:", json.dumps(r["memory_updates"], indent=2))
if r["memory_error"]:
    print("MEMORY ERROR:", r["memory_error"])
print("\n===== AGENT TRACE =====")
print("\n".join(r.get("trace", [])))