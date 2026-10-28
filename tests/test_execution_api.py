import json
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing

import numpy as np
import pytest
from fastapi.testclient import TestClient

import config
import db as task_db
import llm
import main
from agent import loop
from memory import database as memory_db
from memory import retrieval


@pytest.fixture
def task_run_database(tmp_path, monkeypatch):
    path = tmp_path / "task-runs.db"
    monkeypatch.setattr(task_db, "DATABASE_PATH", path)
    task_db.initialize_database()
    return path


def test_health_endpoint_initializes_task_and_memory_databases(task_run_database):
    with TestClient(main.app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert task_run_database.exists()


def test_execute_runs_agent_tools_and_retains_memory_between_tasks(
    task_run_database, monkeypatch
):
    project_id = config.PROJECT_ROOT.name
    memory_vector = np.array([1.0, 0.0], dtype=np.float32)
    memory_id = memory_db.add_memory(
        project_id,
        "decision",
        "Testing convention",
        "Run focused pytest checks for changes.",
        embedding=memory_vector.tobytes(),
    )
    monkeypatch.setattr(retrieval, "embed", lambda _text: memory_vector)
    agent_calls = 0

    def fake_chat(_system, _messages, tools=None, **kwargs):
        nonlocal agent_calls
        if tools is None:
            return llm.LLMResponse(text='{"candidates": []}')
        agent_calls += 1
        if agent_calls == 1:
            return llm.LLMResponse(
                tool_calls=[llm.ToolCall("list-files", "list_files", {})]
            )
        if agent_calls == 3:
            return llm.LLMResponse(
                tool_calls=[llm.ToolCall("tests", "run_tests", {})]
            )
        return llm.LLMResponse(text="Reviewed the workspace and completed the task.")

    monkeypatch.setattr(llm, "chat", fake_chat)

    with TestClient(main.app) as client:
        first = client.post(
            "/api/execute",
            json={"task": "Review the project test convention"},
        )
        second = client.post(
            "/api/execute",
            json={"task": "Verify the existing project tests"},
        )

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    first_data, second_data = first.json(), second.json()
    assert first_data["status"] == "completed"
    assert first_data["final_answer"].startswith("Reviewed the workspace")
    assert first_data["retrieved_memory_ids"] == [memory_id]
    assert any("list_files" in item["event"] for item in first_data["execution_trace"])
    assert second_data["retrieved_memory_ids"] == [memory_id]
    assert second_data["test_results"]["runs"][0]["exit_code"] == 0
    assert second_data["test_results"]["passed"] >= 1
    assert first.headers["x-run-id"] == first_data["run_id"]

    assert memory_db.get_memory(memory_id)["last_used_at"] is not None
    with closing(sqlite3.connect(task_run_database)) as connection:
        rows = connection.execute(
            "SELECT request, status, retrieved_memory_ids FROM task_runs ORDER BY timestamp, rowid"
        ).fetchall()
    assert len(rows) == 2
    assert [row[1] for row in rows] == ["completed", "completed"]
    assert all(memory_id in json.loads(row[2]) for row in rows)


def test_execute_rejects_a_second_active_task(task_run_database, monkeypatch):
    entered_agent = threading.Event()
    release_agent = threading.Event()

    def blocking_agent(*_args, **_kwargs):
        entered_agent.set()
        assert release_agent.wait(timeout=10)
        return {
            "answer": "Completed.",
            "steps": 1,
            "trace": ["User: task", "Agent: Completed."],
            "tool_events": [],
            "test_results": [],
            "injected": [],
            "memory_updates": [],
            "memory_error": None,
        }

    monkeypatch.setattr(loop, "run_task", blocking_agent)
    with TestClient(main.app) as client:
        with ThreadPoolExecutor(max_workers=1) as pool:
            first_request = pool.submit(
                client.post,
                "/api/execute",
                json={"task": "First task"},
            )
            try:
                assert entered_agent.wait(timeout=5)
                second = client.post(
                    "/api/execute",
                    json={"task": "Second task"},
                )
                assert second.status_code == 429
                assert second.headers["retry-after"] == "2"
            finally:
                release_agent.set()
            first = first_request.result(timeout=10)

    assert first.status_code == 200


def test_execute_rejects_blank_task(task_run_database):
    with TestClient(main.app) as client:
        response = client.post("/api/execute", json={"task": "   "})

    assert response.status_code == 422
    assert response.json()["detail"] == "Task must not be blank"


def test_agent_errors_are_persisted_without_exposing_exception_details(
    task_run_database, monkeypatch
):
    def fail_agent(*_args, **_kwargs):
        raise RuntimeError("provider details and credentials must not leak")

    monkeypatch.setattr(loop, "run_task", fail_agent)
    with TestClient(main.app) as client:
        response = client.post("/api/execute", json={"task": "Fail safely"})

    assert response.status_code == 502
    assert "credentials" not in response.text
    assert response.headers.get("x-run-id")
    with closing(sqlite3.connect(task_run_database)) as connection:
        status = connection.execute(
            "SELECT status FROM task_runs WHERE id = ?",
            (response.headers["x-run-id"],),
        ).fetchone()[0]
    assert status == "failed"
