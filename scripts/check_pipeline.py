
"""Manual check of the memory pipeline (no agent, no API calls).

Usage:
  python scripts/check_pipeline.py seed
  python scripts/check_pipeline.py query "users keep getting 401 after login"
  python scripts/check_pipeline.py probe
  python scripts/check_pipeline.py list
  python scripts/check_pipeline.py links
  python scripts/check_pipeline.py sims
  python scripts/check_pipeline.py deprecate 5
  python scripts/check_pipeline.py age 1 60
"""
import sys
import time
from contextlib import closing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from memory import database as db
from memory import retrieval as r
from memory import pipeline, links, update


# Use a separate database for manual testing.
db.DATABASE_PATH = db.PROJECT_ROOT / "demo.db"
PROJECT = "demo"


SEED = [
    (
        "development_experience",
        "Intermittent 401 errors right after login",
        "JWT expiry was not validated before authorizing requests; "
        "check token expiry first.",
    ),
    (
        "development_experience",
        "Orders page loads slowly",
        "N+1 query on customer lookup; added eager loading and "
        "an index on orders.customer_id.",
    ),
    (
        "development_experience",
        "ImportError in parse_config after refactor",
        "Circular import between config_loader and settings; "
        "moved shared constants into constants.py.",
    ),
    (
        "development_experience",
        "Flaky test_checkout failing only in CI",
        "Test depended on the system timezone; "
        "fixed by freezing time with freezegun.",
    ),
    (
        "decision",
        "Primary database choice",
        "Chose PostgreSQL over SQLite for concurrent writes "
        "and JSON column support.",
    ),
    (
        "decision",
        "Frontend state management",
        "Use Redux Toolkit instead of React Context "
        "for shared state.",
    ),
    (
        "decision",
        "Password hashing library",
        "Use argon2 rather than bcrypt; approved after "
        "security review.",
    ),
    (
        "convention",
        "API response format",
        "All endpoints return a {data, error} JSON envelope.",
    ),
    (
        "convention",
        "Python code style",
        "Format with black and type-hint all public functions.",
    ),
    (
        "architecture_note",
        "Authentication module",
        "auth/ handles login and sessions, depends on the "
        "session middleware, issues JWT access tokens.",
    ),
    (
        "architecture_note",
        "Background jobs",
        "Celery workers consume a Redis queue; job code "
        "lives in tasks/.",
    ),
    (
        "task",
        "Password reset flow",
        "Email sending is done; token generation and expiry "
        "are still unfinished.",
    ),
]


# (query, expected category or None, expected text in top hit)
PROBES = [
    (
        "users keep getting 401 shortly after they sign in",
        "development_experience",
        "JWT",
    ),
    (
        "why is the orders screen so slow",
        "development_experience",
        "N+1",
    ),
    (
        "parse_config circular import",
        "development_experience",
        "parse_config",
    ),
    (
        "tests pass locally but fail on the build server",
        "development_experience",
        "Flaky",
    ),
    (
        "which database are we using",
        "decision",
        "PostgreSQL",
    ),
    (
        "how should we hash passwords",
        "decision",
        "argon2",
    ),
    (
        "what is left on the password reset feature",
        "task",
        "Password reset",
    ),
    ("recipe for banana bread", None, None),
    ("weather forecast for tomorrow", None, None),
    ("best pizza places nearby", None, None),
]


def cmd_seed():
    """Reset the demo database, seed memories, and create links."""
    if db.DATABASE_PATH.exists():
        db.DATABASE_PATH.unlink()

    db.initialize_database()

    seeded = 0
    total_links = 0

    for cat, description, experience in SEED:
        memory_id = db.add_memory(
            PROJECT,
            cat,
            description,
            experience,
        )

        r.index_memory(memory_id)
        seeded += 1

        # Create cross-category links for this memory.
        created = links.create_links(PROJECT, memory_id)
        total_links += len(created)

        if created:
            print(
                f"Memory #{memory_id}: "
                f"created {len(created)} link(s)"
            )

    print(f"\nSeeded {seeded} entries into {db.DATABASE_PATH}")
    print(f"Link creation operations: {total_links}")


def cmd_list():
    """List all memories, including deprecated entries."""
    memories = db.list_memories(
        PROJECT,
        include_deprecated=True,
    )

    if not memories:
        print("No memories found. Run seed first.")
        return

    for m in memories:
        print(
            f"#{m['id']:<3} "
            f"{m['category']:<24} "
            f"{m['status']:<10} "
            f"used={m['last_used_at']}  "
            f"{m['description']}"
        )


def cmd_query(text):
    """Retrieve relevant memories and expand one hop through links."""
    r.embed("warm up")

    start = time.perf_counter()

    retrieved = r.retrieve(PROJECT, text)
    retrieved = links.expand(retrieved)

    elapsed_ms = (time.perf_counter() - start) * 1000

    print(f"\nQuery: {text}")
    print(f"Retrieval time: {elapsed_ms:.0f} ms")

    if not retrieved or not any(retrieved.values()):
        print("Nothing retrieved.")

    for category, hits in retrieved.items():
        if not hits:
            continue

        print(f"\n[{category}]")

        for hit in hits:
            # Linked entries were added during one-hop expansion.
            if hit.get("linked"):
                print(
                    f"  (linked, "
                    f"sim={hit['link_similarity']:.2f}) "
                    f"#{hit['id']} {hit['description']}"
                )
                continue

            if hit.get("score") is None:
                print(
                    f"  (included directly) "
                    f"#{hit['id']} {hit['description']}"
                )
            else:
                print(
                    f"  #{hit['id']} "
                    f"score={hit['score']:.2f} "
                    f"cos={hit['cosine']:.2f} "
                    f"bm25={hit['bm25']:.1f} "
                    f"recency={hit['recency']:.2f}  "
                    f"{hit['description']}"
                )

    # Build the final prompt using pipeline.py.
    # pipeline.build_context must also support link expansion.
    prompt, used = pipeline.build_context(PROJECT, text)

    print("\n===== PROMPT THE AGENT WOULD RECEIVE =====")
    print(prompt)
    print(f"\n(entries injected: {used}; last_used_at updated for these)")


def cmd_probe():
    """Check retrieval relevance using the existing probe cases."""
    r.embed("warm up")

    orig = (config.MIN_COSINE, config.MIN_BM25)

    # Disable the normal thresholds temporarily to inspect raw scores.
    config.MIN_COSINE = -1.0
    config.MIN_BM25 = 0.0

    passed = 0

    try:
        for query, expected_category, expected_text in PROBES:
            results = r.retrieve(
                PROJECT,
                query,
                categories=config.UNBOUNDED,
            )

            all_hits = [
                hit
                for hits in results.values()
                for hit in hits
            ]

            def passes_gate(hit):
                return (
                    hit["cosine"] >= orig[0]
                    or hit["bm25"] >= orig[1]
                )

            max_cosine = max(
                (hit["cosine"] for hit in all_hits),
                default=0,
            )
            max_bm25 = max(
                (hit["bm25"] for hit in all_hits),
                default=0,
            )

            if expected_category is None:
                ok = not any(
                    passes_gate(hit) for hit in all_hits
                )
                detail = "(should retrieve nothing)"
            else:
                hits = results.get(expected_category, [])
                top = hits[0] if hits else None

                ok = (
                    bool(top)
                    and passes_gate(top)
                    and expected_text.lower()
                    in (
                        top["description"] + " " + top["experience"]
                    ).lower()
                )

                detail = (
                    f"-> {top['description']}"
                    if top
                    else "-> no hit"
                )

            passed += bool(ok)

            print(
                f"{'PASS' if ok else 'FAIL'}  "
                f"max_cos={max_cosine:.2f} "
                f"max_bm25={max_bm25:.1f}  "
                f"{query!r} {detail}"
            )

    finally:
        config.MIN_COSINE, config.MIN_BM25 = orig

    print(
        f"\n{passed}/{len(PROBES)} probes passed "
        f"(MIN_COSINE={orig[0]}, MIN_BM25={orig[1]})"
    )


def cmd_links():
    """Print each stored memory link once."""
    memories = db.list_memories(
        PROJECT,
        include_deprecated=True,
    )
    by_id = {m["id"]: m for m in memories}
    seen = set()

    print("\n===== MEMORY LINKS =====")

    for memory in memories:
        for other_id, similarity in db.get_links(memory["id"]):
            pair = tuple(sorted((memory["id"], other_id)))

            if pair in seen:
                continue

            seen.add(pair)

            other = by_id.get(other_id)

            if other is None:
                continue

            print(
                f"{similarity:.2f}  "
                f"#{memory['id']} {memory['description']} "
                f"<-> "
                f"#{other_id} {other['description']}"
            )

    if not seen:
        print("No links found. Run seed first.")


def cmd_test_expansion():
    query = "users keep getting 401 after login"

    # Restrict initial retrieval to the bug category.
    initial = r.retrieve(
        PROJECT,
        query,
        categories=("development_experience",),
    )

    print("\n===== BEFORE LINK EXPANSION =====")
    for category, hits in initial.items():
        for hit in hits:
            print(f"[{category}] #{hit['id']} {hit['description']}")

    # Expand one hop through stored links.
    expanded = links.expand(initial)

    print("\n===== AFTER LINK EXPANSION =====")
    for category, hits in expanded.items():
        for hit in hits:
            label = (
                f"linked, sim={hit['link_similarity']:.2f}"
                if hit.get("linked")
                else "direct"
            )
            print(
                f"[{category}] ({label}) "
                f"#{hit['id']} {hit['description']}"
            )

def cmd_sims():
    """Show the strongest cross-category embedding similarities."""
    memories = db.list_memories(PROJECT)
    pairs = []

    for i, first in enumerate(memories):
        for second in memories[i + 1:]:
            if first["category"] == second["category"]:
                continue

            if (
                not first.get("embedding")
                or not second.get("embedding")
            ):
                continue

            vec_a = r.from_blob(first["embedding"])
            vec_b = r.from_blob(second["embedding"])

            similarity = float(vec_a @ vec_b)

            pairs.append((similarity, first, second))

    print("\n===== TOP CROSS-CATEGORY SIMILARITIES =====")

    for similarity, first, second in sorted(
        pairs,
        key=lambda item: -item[0],
    )[:20]:
        print(
            f"{similarity:.2f}  "
            f"#{first['id']} [{first['category']}] "
            f"{first['description']} "
            f"| "
            f"#{second['id']} [{second['category']}] "
            f"{second['description']}"
        )

    if not pairs:
        print("No comparable pairs found. Run seed first.")


def cmd_age(memory_id, days):
    """Make an entry appear older for testing recency scoring."""
    with closing(db.get_connection()) as con:
        con.execute(
            "UPDATE memories "
            "SET updated_at = datetime('now', ?), "
            "last_used_at = NULL "
            "WHERE id = ?",
            (f"-{days} days", memory_id),
        )
        con.commit()

    print(f"Entry {memory_id} now looks {days} days old")


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        print(__doc__)
    elif args[0] == "seed":
        cmd_seed()
    elif args[0] == "list":
        cmd_list()
    elif args[0] == "query":
        cmd_query(" ".join(args[1:]))
    elif args[0] == "probe":
        cmd_probe()
    elif args[0] == "links":
        cmd_links()
    elif args[0] == "sims":
        cmd_sims()
    elif args[0] == "deprecate":
        print(db.deprecate_memory(int(args[1])))
    elif args[0] == "age":
        cmd_age(int(args[1]), int(args[2]))
    elif args[0] == "test-expansion":
        cmd_test_expansion()
    else:
        print(__doc__)
