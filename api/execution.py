import logging
import threading

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

import config
import db
from agent import loop


router = APIRouter()
_task_lock = threading.Lock()
logger = logging.getLogger(__name__)


class ExecuteRequest(BaseModel):
    task: str = Field(min_length=1, max_length=20_000)
    use_memory: bool = True


@router.post("/api/execute")
async def execute_task(payload: ExecuteRequest, response: Response):
    task = payload.task.strip()
    if not task:
        raise HTTPException(
            status_code=422,
            detail="Task must not be blank",
        )

    if not _task_lock.acquire(blocking=False):
        raise HTTPException(
            status_code=429,
            detail="Another task is currently running",
            headers={"Retry-After": "2"},
        )

    try:
        try:
            result = await run_in_threadpool(
                loop.run_task,
                config.PROJECT_ROOT.name,
                task,
                use_memory=payload.use_memory,
                workspace=config.WORKSPACE_DIR,
            )
        except Exception as exc:
            logger.exception("Agent task failed")
            run_id = db.save_task_run(
                request=task,
                status="failed",
                final_answer="The agent could not complete this task.",
                step_count=0,
                execution_trace=[],
                test_results=None,
                retrieved_memory_ids=[],
                memory_updates=[],
                summary_report="## Task failed\nThe agent could not complete this task.",
            )
            response.headers["X-Run-ID"] = run_id
            raise HTTPException(
                status_code=502,
                detail="The coding agent could not complete the task.",
                headers={"X-Run-ID": run_id},
            ) from exc

        execution_trace = [
            {"step": index, "event": event}
            for index, event in enumerate(result["trace"], start=1)
        ]
        tool_events = result.get("tool_events", [])
        test_runs = result.get("test_results", [])
        test_results = None
        if test_runs:
            test_results = {
                "runs": test_runs,
                "passed": sum(run["passed"] for run in test_runs),
                "failed": sum(run["failed"] for run in test_runs),
                "errors": sum(run["errors"] for run in test_runs),
                "total": sum(
                    run["passed"] + run["failed"] + run["errors"]
                    for run in test_runs
                ),
            }

        changed_files = []
        for event in tool_events:
            outcome = event.get("result", "")
            if event.get("tool") == "edit_file" and outcome.startswith(
                ("created ", "edited ")
            ):
                changed_files.append(outcome.split(" ", 1)[1])
        changed_files = list(dict.fromkeys(changed_files))

        report = [
            "## Task result",
            result["answer"] or "The agent returned no final answer.",
            "",
            "### Files changed",
            *(
                [f"- `{path}`" for path in changed_files]
                if changed_files
                else ["- No file changes were reported by the agent."]
            ),
            "",
            "### Tests run",
        ]
        if test_runs:
            report.extend(
                f"- `{run['target']}`: {run['summary']}"
                for run in test_runs
            )
        else:
            report.append("- The agent did not run tests during this task.")
        report.extend(["", "### Memory"])
        if result.get("memory_error"):
            report.append("- The task completed, but memory updates were unavailable.")
        else:
            report.append(
                f"- Retrieved {len(result.get('injected') or [])} memories; "
                f"recorded {len(result.get('memory_updates') or [])} memory updates."
            )

        updates = result.get("memory_updates") or []
        memory_updates = [
            {
                "action": update.get("action"),
                "id": update.get("id"),
                "category": update.get("candidate", {}).get("category"),
                "description": update.get("candidate", {}).get("description"),
                "experience": update.get("candidate", {}).get("experience"),
                "task_state": update.get("candidate", {}).get("task_state"),
            }
            for update in updates
        ]
        run_id = db.save_task_run(
            request=task,
            status="completed",
            final_answer=result["answer"],
            step_count=result["steps"],
            execution_trace=execution_trace,
            test_results=test_results,
            retrieved_memory_ids=result.get("injected") or [],
            memory_updates=memory_updates,
            summary_report="\n".join(report),
        )
        response.headers["X-Run-ID"] = run_id
        return {
            "run_id": run_id,
            "status": "completed",
            "final_answer": result["answer"],
            "step_count": result["steps"],
            "execution_trace": execution_trace,
            "test_results": test_results,
            "retrieved_memory_ids": result.get("injected") or [],
            "memory_updates": memory_updates,
            "memory_error": (
                "Memory updates could not be completed."
                if result.get("memory_error")
                else None
            ),
            "summary_report": "\n".join(report),
        }
    finally:
        _task_lock.release()
