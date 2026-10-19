import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from db import save_task_run


router = APIRouter()
_task_running = False


class ExecuteRequest(BaseModel):
    task: str = Field(min_length=1)


@router.post("/api/execute")
async def execute_task(payload: ExecuteRequest):
    global _task_running
    if _task_running:
        raise HTTPException(
            status_code=429,
            detail="Another task is currently running",
            headers={"Retry-After": "2"},
        )

    _task_running = True
    try:
        await asyncio.sleep(2)

        execution_trace = [
            {"step": 1, "action": "inspect_workspace", "status": "completed"},
            {"step": 2, "action": "implement_requested_change", "status": "completed"},
            {"step": 3, "action": "run_tests", "status": "completed"},
        ]
        test_results = {
            "passed": 3,
            "failed": 0,
            "total": 3,
            "details": [
                {"name": "test_task_request", "status": "passed"},
                {"name": "test_execution_trace", "status": "passed"},
                {"name": "test_workspace_boundary", "status": "passed"},
            ],
        }
        final_answer = "Task execution completed successfully (mock run)."
        summary_report = (
            "## Summary\n"
            "Mock execution completed successfully.\n\n"
            "### Files changed\n"
            "- `toy_project/example.py` (mock change; no file was modified)\n\n"
            "### Tests run\n"
            "- 3 mock tests: 3 passed, 0 failed\n\n"
            "### Next steps\n"
            "- Review the proposed change.\n"
            "- Replace the mock executor with the coding agent implementation."
        )
        run_id = save_task_run(
            request=payload.task,
            status="success",
            final_answer=final_answer,
            step_count=len(execution_trace),
            execution_trace=execution_trace,
            test_results=test_results,
            retrieved_memory_ids=[],
            memory_updates=[],
            summary_report=summary_report,
        )
        return {
            "run_id": run_id,
            "status": "success",
            "final_answer": final_answer,
            "step_count": len(execution_trace),
            "execution_trace": execution_trace,
            "test_results": test_results,
            "retrieved_memory_ids": [],
            "memory_updates": [],
            "summary_report": summary_report,
        }
    finally:
        _task_running = False
