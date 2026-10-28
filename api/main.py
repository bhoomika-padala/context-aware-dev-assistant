from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from memory import database as memory_database
from memory.pipeline import build_context


router = APIRouter()


class ContextRequest(BaseModel):
    project_id: str = Field(min_length=1, max_length=200)
    query: str = Field(min_length=1, max_length=20_000)


class MemoryRequest(BaseModel):
    project_id: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1)
    description: str = Field(min_length=1, max_length=300)
    experience: str = Field(min_length=1, max_length=600)
    task_state: str | None = None


@router.get("/health")
@router.get("/api/health")
def health():
    return {"status": "ok"}


@router.post("/context")
def get_project_context(payload: ContextRequest):
    try:
        context, memory_ids = build_context(
            payload.project_id,
            payload.query,
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"context": context, "retrieved_memory_ids": memory_ids}


@router.post("/memories", status_code=201)
def create_memory(payload: MemoryRequest):
    try:
        memory_id = memory_database.add_memory(
            payload.project_id,
            payload.category,
            payload.description,
            payload.experience,
            task_state=payload.task_state,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"memory_id": memory_id}
