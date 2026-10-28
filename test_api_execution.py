import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

import db as task_db
import llm
import main
from memory import database as memory_db


def test_backend_execution():
    original_task_db = task_db.DATABASE_PATH
    original_memory_db = memory_db.DATABASE_PATH
    original_chat = llm.chat

    def fake_chat(_system, _messages, tools=None, **_kwargs):
        if tools is None:
            return llm.LLMResponse(text='{"candidates": []}')
        return llm.LLMResponse(text="Agent execution test completed.")

    try:
        with tempfile.TemporaryDirectory(prefix="agent-api-test-") as directory:
            task_db.DATABASE_PATH = Path(directory) / "task-runs.db"
            memory_db.DATABASE_PATH = Path(directory) / "memory.db"
            memory_db.initialize_database()
            llm.chat = fake_chat
            with TestClient(main.app) as client:
                response = client.post(
                    "/api/execute",
                    json={"task": "Verify agent integration"},
                )
            assert response.status_code == 200, (
                f"Unexpected status: {response.status_code}"
            )
            data = response.json()
            assert data["status"] == "completed"
            assert data["final_answer"] == "Agent execution test completed."
            assert "summary_report" in data
            assert "execution_trace" in data
            print(
                "\n[SUCCESS] Backend API executed the agent loop and returned its response."
            )
    finally:
        task_db.DATABASE_PATH = original_task_db
        memory_db.DATABASE_PATH = original_memory_db
        llm.chat = original_chat


if __name__ == "__main__":
    test_backend_execution()
