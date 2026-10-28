# Project Memory

## Scope

Project Memory is a SQLite-backed store for project decisions, conventions,
architecture notes, development experience, and task state. The database schema
and category validation are implemented in `memory/database.py`.

## Memory interface

- `memory.retrieval.retrieve(...)` returns active memories for one project,
  ranked with BM25, Sentence Transformers embeddings, and recency.
- `memory.pipeline.build_context(...)` retrieves, expands, composes, and marks
  memory entries used before an agent turn.
- `memory.pipeline.record(...)` extracts and consolidates memory updates after
  an agent turn.

## Agent and API

Run the FastAPI application from the repository root with
`python -m uvicorn main:app --reload --port 8000`. `POST /api/execute` invokes
the existing `agent.loop.run_task(...)` against the configured toy-project
workspace, persists the task run, and returns the real agent trace, test runs,
and memory IDs and updates. `GET /api/health` checks the API. The memory API
also exposes `POST /context` and `POST /memories`.

Run the React application with `npm run dev` at the default Vite address,
`http://localhost:5173`. It uses `VITE_API_BASE_URL` when set, otherwise it
calls `http://localhost:8000`.

## Evaluation and tests

Run `python -m eval.run_eval` to measure retrieval recall for the bundled
scenarios. Run `python -m pytest -q` and `npm run build` to check the backend
and frontend. Evaluation uses a temporary SQLite database and does not write
to the project's persistent database.

## Configuration

Runtime defaults and retrieval thresholds are in `config.py`. Set `GROQ_API_KEY`
in the ignored local `.env` file. Do not commit API keys or other secrets.
