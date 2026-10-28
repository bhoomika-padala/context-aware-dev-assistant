
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import config

SKIP = {
    "__pycache__",
    ".pytest_cache",
    ".git",
    ".venv",
    ".mypy_cache",
    ".ruff_cache",
}

TOOLS = [
    {
        "name": "list_files",
        "description": "List all files in the project workspace.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "read_file",
        "description": "Read a text file from the workspace.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path",
                }
            },
            "required": ["path"],
        },
    },
    {
        "name": "edit_file",
        "description": (
            "Replace old_text with new_text in a file. "
            "old_text must match exactly once. "
            "To create a new file, use an empty old_text."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "old_text": {"type": "string"},
                "new_text": {"type": "string"},
            },
            "required": ["path", "old_text", "new_text"],
        },
    },
    {
        "name": "run_tests",
        "description": (
            "Run pytest in the workspace. "
            "Optional target is a test file or directory."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "target": {"type": "string"}
            },
            "required": [],
        },
    },
]


def _safe(root, rel):
    root = Path(root).resolve()
    p = (root / rel).resolve()

    if p != root and root not in p.parents:
        raise ValueError("path is outside the workspace")

    return p


def _clip(text):
    text = str(text)
    n = config.TOOL_OUTPUT_MAX_CHARS
    return text if len(text) <= n else text[:n] + "\n...[truncated]"


def list_files(root):
    root = Path(root).resolve()
    found = []

    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP]

        for filename in files:
            if filename.endswith((".db", ".sqlite", ".sqlite3")):
                continue

            found.append(
                (Path(dirpath) / filename).relative_to(root).as_posix()
            )

    return "\n".join(sorted(found)) or "(no files)"


def read_file(root, path):
    p = _safe(root, path)

    if not p.is_file():
        raise ValueError(f"no such file: {path}")

    return _clip(p.read_text(encoding="utf-8", errors="replace"))


def edit_file(root, path, old_text, new_text):
    p = _safe(root, path)

    if old_text == "":
        if p.exists():
            raise ValueError("file exists; give the old_text you want to replace")

        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(new_text, encoding="utf-8")
        return f"created {path}"

    if not p.is_file():
        raise ValueError(f"no such file: {path}")

    content = p.read_text(encoding="utf-8")
    n = content.count(old_text)

    if n == 0:
        raise ValueError(
            "old_text not found; read the file and copy the text exactly"
        )

    if n > 1:
        raise ValueError(
            f"old_text matches {n} places; include more surrounding lines"
        )

    p.write_text(content.replace(old_text, new_text, 1), encoding="utf-8")
    return f"edited {path}"


def run_tests(root, target=""):
    root = Path(root).resolve()

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "--no-header",
        "-p",
        "no:cacheprovider",
    ]

    if target:
        cmd.append(str(_safe(root, target)))

    env = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
    }

    try:
        p = subprocess.run(
            cmd,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=config.TEST_TIMEOUT,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return f"Error: tests timed out after {config.TEST_TIMEOUT}s"

    return _clip(
        f"exit code {p.returncode}\n{p.stdout}{p.stderr}"
    )


def execute(root, name, args):
    """Run one tool call. Never raises: errors go back to the model as text."""

    try:
        if name == "list_files":
            return list_files(root)

        if name == "read_file":
            return read_file(root, args["path"])

        if name == "edit_file":
            return edit_file(
                root,
                args["path"],
                args["old_text"],
                args["new_text"],
            )

        if name == "run_tests":
            return run_tests(root, args.get("target", ""))

        return f"Error: unknown tool {name}"

    except KeyError as e:
        return f"Error: missing argument {e}"

    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"
