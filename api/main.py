import json
from http import HTTPStatus
from wsgiref.simple_server import make_server

from memory.retrieval import get_context
from memory.update import record


def _json_response(start_response, status, payload):
    body = json.dumps(payload).encode("utf-8")
    start_response(
        f"{status.value} {status.phrase}",
        [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(body))),
        ],
    )
    return [body]


def _read_json(environ):
    try:
        length = int(environ.get("CONTENT_LENGTH") or "0")
    except ValueError as exc:
        raise ValueError("Invalid Content-Length") from exc
    if length <= 0:
        raise ValueError("A JSON request body is required")
    raw_body = environ["wsgi.input"].read(length)
    try:
        payload = json.loads(raw_body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Request body must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object")
    return payload


def application(environ, start_response):
    method = environ.get("REQUEST_METHOD", "GET").upper()
    path = environ.get("PATH_INFO", "/")

    if method == "GET" and path == "/health":
        return _json_response(start_response, HTTPStatus.OK, {"status": "ok"})
    if method != "POST":
        return _json_response(
            start_response,
            HTTPStatus.METHOD_NOT_ALLOWED,
            {"error": "Only POST is supported for this route"},
        )

    try:
        payload = _read_json(environ)
        project_id = payload.get("project_id")
        if not isinstance(project_id, str) or not project_id.strip():
            raise ValueError("project_id must be a non-empty string")

        if path == "/context":
            query = payload.get("query")
            if not isinstance(query, str):
                raise ValueError("query must be a string")
            limit = payload.get("limit")
            if limit is not None and (not isinstance(limit, int) or limit < 1):
                raise ValueError("limit must be a positive integer")
            context = get_context(project_id, query, **(
                {"limit": limit} if limit is not None else {}
            ))
            return _json_response(
                start_response,
                HTTPStatus.OK,
                {"context": context},
            )

        if path == "/memories":
            required = ("category", "description", "experience")
            missing = [key for key in required if not isinstance(payload.get(key), str)]
            if missing:
                raise ValueError(f"Required string fields: {', '.join(missing)}")
            memory_id = record(
                project_id,
                payload["category"],
                payload["description"],
                payload["experience"],
                task_state=payload.get("task_state"),
            )
            return _json_response(
                start_response,
                HTTPStatus.CREATED,
                {"memory_id": memory_id},
            )

        return _json_response(
            start_response,
            HTTPStatus.NOT_FOUND,
            {"error": "Route not found"},
        )
    except (TypeError, ValueError) as exc:
        return _json_response(
            start_response,
            HTTPStatus.BAD_REQUEST,
            {"error": str(exc)},
        )


def main():
    with make_server("127.0.0.1", 8000, application) as server:
        print("Project memory API listening on http://127.0.0.1:8000")
        server.serve_forever()


if __name__ == "__main__":
    main()
