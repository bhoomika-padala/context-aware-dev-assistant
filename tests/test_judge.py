from memory import judge

C = {"category": "decision", "description": "Primary database", "experience": "Switched to SQLite"}
E = {"description": "Primary database", "experience": "Chose PostgreSQL"}

def test_verdicts_parse(fake_llm):
    fake_llm('{"verdict": "contradicts"}')
    assert judge.judge(C, E) == "contradicts"

def test_verdict_is_case_insensitive_and_fence_tolerant(fake_llm):
    fake_llm('```json\n{"verdict": "SAME"}\n```')
    assert judge.judge(C, E) == "same"

def test_unusable_output_defaults_to_unrelated(fake_llm):
    calls = fake_llm("garbage", '{"verdict": "maybe"}')
    assert judge.judge(C, E) == "unrelated" and len(calls) == 2