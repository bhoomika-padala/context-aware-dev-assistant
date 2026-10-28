from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.execution import router as execution_router
from api.main import router as memory_router
from db import initialize_database
from memory.database import initialize_database as initialize_memory_database


@asynccontextmanager
async def lifespan(app):
    initialize_database()
    initialize_memory_database()
    yield


app = FastAPI(title="Coding Agent API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(execution_router)
app.include_router(memory_router)
