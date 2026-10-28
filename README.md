# Context-Aware Software Development Assistant

An AI-based software engineering assistant with persistent project
memory designed to improve continuity across development sessions.

## Components

- SQLite-backed project memory with validated categories and task state
- Hybrid BM25 and Sentence Transformers memory retrieval and context composition
- Agent turn orchestration with a narrow memory-tool interface
- FastAPI API for agent execution, health checks, and project memory
- React/Vite workspace for task submission and execution results
- Retrieval evaluation scenarios and an isolated evaluation runner

## Current Progress

- [x] Git repository initialized
- [x] Persistent memory storage
- [x] Memory retrieval and context composition
- [x] Memory pipeline integration
- [x] Agent tool integration
- [x] Evaluation

See [SPEC.md](SPEC.md) for the memory interface and run instructions.

## Run locally

Configure `GROQ_API_KEY` in the ignored `.env` file, then start the backend and
frontend in separate terminals:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
npm run dev
```

The frontend runs at `http://localhost:5173` and calls the backend at
`http://localhost:8000`. Set `VITE_API_BASE_URL` only to use a different local
backend address.

Run checks with:

```powershell
npm run build
.\.venv\Scripts\python.exe -m pytest -q
```
