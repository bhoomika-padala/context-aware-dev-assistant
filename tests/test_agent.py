# from agent.loop import run_turn
# from memory import database


# def test_agent_supplies_context_and_records_only_explicit_memory():
#     database.add_memory(
#         "p1", "convention", "Use pytest", "Run tests with pytest."
#     )
#     seen = {}

#     def responder(message, context):
#         seen["message"] = message
#         seen["context"] = context
#         return "Tests are run with pytest."

#     result = run_turn(
#         "p1",
#         "How do I run tests?",
#         responder,
#         memory_to_record={
#             "category": "task",
#             "description": "Add tests",
#             "experience": "Write focused regression tests.",
#         },
#     )

#     assert seen["message"] == "How do I run tests?"
#     assert "Run tests with pytest." in seen["context"]
#     assert result["response"] == "Tests are run with pytest."
#     assert result["memory_id"] is not None
#     assert database.get_memory(result["memory_id"])["task_state"] == "open"
