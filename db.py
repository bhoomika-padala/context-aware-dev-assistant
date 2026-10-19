import json
import sqlite3
import uuid
from contextlib import closing
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parent / "task_runs.db"


def initialize_database():
    """Create the task-run database and table when they do not yet exist."""
    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS task_runs (
                id TEXT PRIMARY KEY,
                request TEXT NOT NULL,
                timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL,
                final_answer TEXT,
                step_count INTEGER NOT NULL DEFAULT 0,
                execution_trace JSON NOT NULL DEFAULT '[]',
                test_results JSON NOT NULL DEFAULT '{}',
                retrieved_memory_ids JSON NOT NULL DEFAULT '[]',
                memory_updates JSON NOT NULL DEFAULT '[]',
                summary_report TEXT
            )
            """
        )
        connection.commit()


def save_task_run(
    *,
    request,
    status,
    final_answer,
    step_count,
    execution_trace,
    test_results,
    retrieved_memory_ids=None,
    memory_updates=None,
    summary_report=None,
):
    """Persist a completed task run and return its UUID."""
    run_id = str(uuid.uuid4())
    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        connection.execute(
            """
            INSERT INTO task_runs (
                id, request, status, final_answer, step_count,
                execution_trace, test_results, retrieved_memory_ids,
                memory_updates, summary_report
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                request,
                status,
                final_answer,
                step_count,
                json.dumps(execution_trace),
                json.dumps(test_results),
                json.dumps(retrieved_memory_ids or []),
                json.dumps(memory_updates or []),
                summary_report,
            ),
        )
        connection.commit()
    return run_id
