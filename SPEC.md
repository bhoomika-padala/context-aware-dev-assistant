# Project Memory

## Scope

Project Memory is a SQLite-backed store for project decisions, conventions,
architecture notes, development experience, and task state. The database schema
and category validation are implemented in `memory/database.py`.

## Memory interface

- `memory.update.record(...)` explicitly records a memory and returns its ID.
- `memory.retrieval.retrieve_memories(...)` returns active memories for one
  project, ranked by lexical overlap and category weight.
- `memory.retrieval.get_context(...)` formats those matches for an agent turn.
- `memory.composer.compose_context(...)` formats retrieved items within a
  character limit.
- Retrieval uses lexical matching and does not require a model or network call.

## Agent and API

The agent accesses memory only through `agent.tools.get_context()` and
`agent.tools.record()`. The standard-library WSGI API exposes `GET /health`,
`POST /context`, and `POST /memories`; run it with `python -m api.main`.

## Evaluation and tests

Run `python -m eval.run_eval` to measure retrieval recall for the bundled
scenarios. Run `pytest` to execute the test suite. Evaluation uses a temporary
SQLite database and does not write to the project's persistent database.

## Configuration

Runtime defaults and retrieval thresholds are in `config.py`. Copy
`.env.example` to `.env` when using environment-based configuration; `.env` is
ignored by Git and must not contain checked-in secrets.
