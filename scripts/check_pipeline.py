"""Manual check of the memory pipeline (no agent, no API calls).

  python scripts/check_pipeline.py seed
  python scripts/check_pipeline.py query "users keep getting 401 after login"
  python scripts/check_pipeline.py probe
  python scripts/check_pipeline.py list
  python scripts/check_pipeline.py deprecate 5
  python scripts/check_pipeline.py age 1 60     # pretend entry 1 is 60 days old
"""
import sys
import time
from contextlib import closing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from memory import database as db
from memory import retrieval as r
from memory import pipeline

db.DATABASE_PATH = db.PROJECT_ROOT / "demo.db"   # separate from real data
PROJECT = "demo"

SEED = [
    ("development_experience", "Intermittent 401 errors right after login",
     "JWT expiry was not validated before authorizing requests; check token expiry first."),
    ("development_experience", "Orders page loads slowly",
     "N+1 query on customer lookup; added eager loading and an index on orders.customer_id."),
    ("development_experience", "ImportError in parse_config after refactor",
     "Circular import between config_loader and settings; moved shared constants into constants.py."),
    ("development_experience", "Flaky test_checkout failing only in CI",
     "Test depended on the system timezone; fixed by freezing time with freezegun."),
    ("decision", "Primary database choice",
     "Chose PostgreSQL over SQLite for concurrent writes and JSON column support."),
    ("decision", "Frontend state management",
     "Use Redux Toolkit instead of React Context for shared state."),
    ("decision", "Password hashing library",
     "Use argon2 rather than bcrypt; approved after security review."),
    ("convention", "API response format",
     "All endpoints return a {data, error} JSON envelope."),
    ("convention", "Python code style",
     "Format with black and type-hint all public functions."),
    ("architecture_note", "Authentication module",
     "auth/ handles login and sessions, depends on the session middleware, issues JWT access tokens."),
    ("architecture_note", "Background jobs",
     "Celery workers consume a Redis queue; job code lives in tasks/."),
    ("task", "Password reset flow",
     "Email sending is done; token generation and expiry are still unfinished."),
]

# (query, expected category or None, text the top hit should contain)
PROBES = [
    ("users keep getting 401 shortly after they sign in", "development_experience", "JWT"),
    ("why is the orders screen so slow", "development_experience", "N+1"),
    ("parse_config circular import", "development_experience", "parse_config"),
    ("tests pass locally but fail on the build server", "development_experience", "Flaky"),
    ("which database are we using", "decision", "PostgreSQL"),
    ("how should we hash passwords", "decision", "argon2"),
    ("what is left on the password reset feature", "task", "Password reset"),
    ("recipe for banana bread", None, None),
    ("weather forecast for tomorrow", None, None),
    ("best pizza places nearby", None, None),
]


def cmd_seed():
    if db.DATABASE_PATH.exists():
        db.DATABASE_PATH.unlink()
    db.initialize_database()
    for cat, d, e in SEED:
        r.index_memory(db.add_memory(PROJECT, cat, d, e))
    print(f"Seeded {len(SEED)} entries into {db.DATABASE_PATH}")


def cmd_list():
    for m in db.list_memories(PROJECT, include_deprecated=True):
        print(f"#{m['id']:<3} {m['category']:<24} {m['status']:<10} "
              f"used={m['last_used_at']}  {m['description']}")


def cmd_query(text):
    r.embed("warm up")                       # load the model before timing
    t = time.perf_counter()
    retrieved = r.retrieve(PROJECT, text)
    ms = (time.perf_counter() - t) * 1000
    print(f"\nQuery: {text}\nRetrieval time: {ms:.0f} ms")
    if not retrieved:
        print("Nothing retrieved.")
    for cat, hits in retrieved.items():
        print(f"\n[{cat}]")
        for h in hits:
            if h["score"] is None:
                print(f"  (included directly) #{h['id']} {h['description']}")
            else:
                print(f"  #{h['id']} score={h['score']:.2f} cos={h['cosine']:.2f} "
                      f"bm25={h['bm25']:.1f} recency={h['recency']:.2f}  {h['description']}")
    prompt, used = pipeline.build_context(PROJECT, text)
    print("\n===== PROMPT THE AGENT WOULD RECEIVE =====")
    print(prompt)
    print(f"\n(entries injected: {used}; last_used_at updated for these)")


def cmd_probe():
    r.embed("warm up")
    orig = (config.MIN_COSINE, config.MIN_BM25)
    config.MIN_COSINE, config.MIN_BM25 = -1.0, 0.0   # gate off: see raw numbers
    passed = 0
    try:
        for q, cat, sub in PROBES:
            res = r.retrieve(PROJECT, q, categories=config.UNBOUNDED)
            allhits = [h for hs in res.values() for h in hs]
            gate = lambda h: h["cosine"] >= orig[0] or h["bm25"] >= orig[1]
            max_cos = max((h["cosine"] for h in allhits), default=0)
            max_bm = max((h["bm25"] for h in allhits), default=0)
            if cat is None:
                ok = not any(gate(h) for h in allhits)
                detail = "(should retrieve nothing)"
            else:
                hits = res.get(cat, [])
                top = hits[0] if hits else None
                ok = bool(top) and gate(top) and \
                    sub.lower() in (top["description"] + top["experience"]).lower()
                detail = f"-> {top['description']}" if top else "-> no hit"
            passed += ok
            print(f"{'PASS' if ok else 'FAIL'}  max_cos={max_cos:.2f} max_bm25={max_bm:.1f}  "
                  f"{q!r} {detail}")
    finally:
        config.MIN_COSINE, config.MIN_BM25 = orig
    print(f"\n{passed}/{len(PROBES)} probes passed "
          f"(MIN_COSINE={orig[0]}, MIN_BM25={orig[1]})")


def cmd_age(mid, days):
    with closing(db.get_connection()) as con:
        con.execute("UPDATE memories SET updated_at = datetime('now', ?), "
                    "last_used_at = NULL WHERE id = ?", (f"-{days} days", mid))
        con.commit()
    print(f"Entry {mid} now looks {days} days old")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__)
    elif a[0] == "seed":
        cmd_seed()
    elif a[0] == "list":
        cmd_list()
    elif a[0] == "query":
        cmd_query(" ".join(a[1:]))
    elif a[0] == "probe":
        cmd_probe()
    elif a[0] == "deprecate":
        print(db.deprecate_memory(int(a[1])))
    elif a[0] == "age":
        cmd_age(int(a[1]), int(a[2]))