from agent import tools
import config

def test_paths_cannot_escape(tmp_path):
    (tmp_path / "a.txt").write_text("x")
    assert tools.execute(tmp_path, "read_file", {"path": "../secret.txt"}).startswith("Error")
    assert tools.execute(tmp_path, "read_file",
                         {"path": str(tmp_path.parent / "x.txt")}).startswith("Error")

def test_edit_requires_exactly_one_match(tmp_path):
    (tmp_path / "f.py").write_text("a = 1\na = 1\nb = 2\n")
    assert "matches 2" in tools.execute(tmp_path, "edit_file",
                                        {"path": "f.py", "old_text": "a = 1", "new_text": "a = 9"})
    assert "not found" in tools.execute(tmp_path, "edit_file",
                                        {"path": "f.py", "old_text": "zzz", "new_text": "y"})
    assert tools.execute(tmp_path, "edit_file",
                         {"path": "f.py", "old_text": "b = 2", "new_text": "b = 3"}) == "edited f.py"
    assert "b = 3" in (tmp_path / "f.py").read_text()

def test_create_file_and_refuse_overwrite(tmp_path):
    a = {"path": "sub/new.py", "old_text": "", "new_text": "x = 1\n"}
    assert tools.execute(tmp_path, "edit_file", a) == "created sub/new.py"
    assert tools.execute(tmp_path, "edit_file", a).startswith("Error")

def test_list_files_skips_cache_dirs(tmp_path):
    (tmp_path / "a.py").write_text("")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "x.pyc").write_text("")
    assert tools.execute(tmp_path, "list_files", {}) == "a.py"

def test_missing_argument_and_unknown_tool(tmp_path):
    assert tools.execute(tmp_path, "read_file", {}).startswith("Error")
    assert tools.execute(tmp_path, "rm_rf", {}).startswith("Error")

def test_run_tests_reports_failure_then_success(tmp_path):
    (tmp_path / "test_a.py").write_text("def test_a():\n    assert 1 == 2\n")
    out = tools.execute(tmp_path, "run_tests", {})
    assert "exit code 1" in out and "assert" in out
    (tmp_path / "test_a.py").write_text("def test_a():\n    assert 1 == 1\n")
    assert "exit code 0" in tools.execute(tmp_path, "run_tests", {})

def test_run_tests_timeout(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "TEST_TIMEOUT", 1)
    (tmp_path / "test_slow.py").write_text("import time\ndef test_s():\n    time.sleep(5)\n")
    assert "timed out" in tools.execute(tmp_path, "run_tests", {})