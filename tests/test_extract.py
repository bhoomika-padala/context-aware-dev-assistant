import json
import config
from memory import extract

def reply(*cands):
    return json.dumps({"candidates": list(cands)})

GOOD = {"category": "development_experience", "description": "Login returned 401 intermittently",
        "experience": "Token expiry was not checked before authorizing; validate expiry first."}

def test_valid_output_is_parsed(fake_llm):
    fake_llm(reply(GOOD))
    assert extract.extract_candidates("transcript") == [GOOD]

def test_code_fenced_output_is_parsed(fake_llm):
    fake_llm("```json\n" + reply(GOOD) + "\n```")
    assert len(extract.extract_candidates("t")) == 1

def test_invalid_categories_and_empty_fields_are_dropped(fake_llm):
    fake_llm(reply({"category": "bogus", "description": "x", "experience": "y"},
                   {"category": "decision", "description": "", "experience": "y"}, GOOD))
    assert extract.extract_candidates("t") == [GOOD]

def test_candidate_cap(fake_llm):
    many = [{"category": "decision", "description": f"d{i}", "experience": "e"} for i in range(6)]
    fake_llm(reply(*many))
    assert len(extract.extract_candidates("t")) == config.MAX_CANDIDATES

def test_bad_json_is_retried_once(fake_llm):
    calls = fake_llm("not json at all", reply(GOOD))
    assert extract.extract_candidates("t") == [GOOD]
    assert len(calls) == 2 and len(calls[1]) == 3     # original + bad reply + correction

def test_gives_up_after_one_retry_without_raising(fake_llm):
    calls = fake_llm("nope", "still nope")
    assert extract.extract_candidates("t") == [] and len(calls) == 2

def test_nothing_worth_remembering(fake_llm):
    fake_llm(reply())
    assert extract.extract_candidates("what is 2+2") == []

def test_task_state_defaults_and_validates(fake_llm):
    fake_llm(reply({"category": "task", "description": "Add reset", "experience": "wip",
                    "task_state": "banana"}))
    assert extract.extract_candidates("t")[0]["task_state"] == "open"

def test_long_trajectory_is_clipped(fake_llm, monkeypatch):
    monkeypatch.setattr(config, "TRAJECTORY_MAX_CHARS", 100)
    calls = fake_llm(reply())
    extract.extract_candidates("A" * 500 + "Z" * 500)
    prompt = calls[0][0]["content"]
    assert "middle omitted" in prompt and len(prompt) < 400