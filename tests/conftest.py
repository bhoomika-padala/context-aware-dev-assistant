import pytest
from memory import database as db

@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATABASE_PATH", tmp_path / "test.db")
    db.initialize_database()

@pytest.fixture
def fake_llm(monkeypatch):
    import llm
    def install(*texts):
        calls, it = [], iter(texts)
        def _chat(system, messages, **kw):
            calls.append(list(messages))
            return llm.LLMResponse(text=next(it))
        monkeypatch.setattr(llm, "chat", _chat)
        return calls
    return install