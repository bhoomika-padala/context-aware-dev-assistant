# import io
# import json

# from api.main import application
# from memory import database


# def _request(method, path, payload=None):
#     body = json.dumps(payload).encode("utf-8") if payload is not None else b""
#     environ = {
#         "REQUEST_METHOD": method,
#         "PATH_INFO": path,
#         "CONTENT_LENGTH": str(len(body)),
#         "wsgi.input": io.BytesIO(body),
#     }
#     captured = {}

#     def start_response(status, headers):
#         captured["status"] = status

#     response = b"".join(application(environ, start_response))
#     return captured["status"], json.loads(response)


# def test_api_records_and_retrieves_memory():
#     status, created = _request(
#         "POST",
#         "/memories",
#         {
#             "project_id": "p1",
#             "category": "decision",
#             "description": "Use PostgreSQL",
#             "experience": "Provides JSON support.",
#         },
#     )
#     assert status.startswith("201")
#     assert created["memory_id"]

#     status, context = _request(
#         "POST", "/context", {"project_id": "p1", "query": "PostgreSQL JSON"}
#     )
#     assert status.startswith("200")
#     assert "Use PostgreSQL" in context["context"]


# def test_api_rejects_invalid_memory_category():
#     status, response = _request(
#         "POST",
#         "/memories",
#         {
#             "project_id": "p1",
#             "category": "not-a-category",
#             "description": "x",
#             "experience": "y",
#         },
#     )

#     assert status.startswith("400")
#     assert "Unknown category" in response["error"]
