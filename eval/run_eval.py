import json
import tempfile
from pathlib import Path

from memory import database
from memory.retrieval import retrieve_memories


SCENARIO_FILE = Path(__file__).parent / "scenarios" / "basic.json"


def run_evaluation(scenario_file=SCENARIO_FILE):
    scenarios = json.loads(Path(scenario_file).read_text(encoding="utf-8"))
    original_database_path = database.DATABASE_PATH
    try:
        with tempfile.TemporaryDirectory(prefix="project-memory-eval-") as directory:
            database.DATABASE_PATH = Path(directory) / "evaluation.db"
            database.initialize_database()
            hits = 0
            for scenario in scenarios:
                memory = scenario["memory"]
                database.add_memory(
                    scenario["project_id"],
                    memory["category"],
                    memory["description"],
                    memory["experience"],
                )
                results = retrieve_memories(
                    scenario["project_id"], scenario["query"]
                )
                if any(
                    item["description"] == scenario["expected_description"]
                    for item in results
                ):
                    hits += 1
    finally:
        database.DATABASE_PATH = original_database_path

    return {
        "scenarios": len(scenarios),
        "hits": hits,
        "recall": hits / len(scenarios) if scenarios else 1.0,
    }


def main():
    result = run_evaluation()
    print(json.dumps(result, indent=2))
    return 0 if result["hits"] == result["scenarios"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
