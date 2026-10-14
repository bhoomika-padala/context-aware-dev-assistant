import sqlite3
from contextlib import closing
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "memory.db"

MEMORY_CATEGORIES = {
    "development_experience", "decision", "convention",
    "architecture_note", "task",
}
TASK_STATES = {"open", "in_progress", "resolved"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id TEXT NOT NULL,
  category TEXT NOT NULL CHECK (category IN
    ('development_experience','decision','convention',
     'architecture_note','task')),
  description TEXT NOT NULL,
  experience TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active'
    CHECK (status IN ('active','deprecated')),
  task_state TEXT CHECK (task_state IN ('open','in_progress','resolved')),
  embedding BLOB,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_used_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_mem_lookup
  ON memories (project_id, category, status);
"""

def get_connection():
    con = sqlite3.connect(DATABASE_PATH)
    con.row_factory = sqlite3.Row
    return con

def initialize_database():
    with closing(get_connection()) as con:
        con.executescript(SCHEMA)
        con.commit()

def add_memory(project_id, category, description, experience,
               task_state=None, embedding=None):
    if category not in MEMORY_CATEGORIES:
        raise ValueError(f"Unknown category: {category}")
    if category == "task":
        task_state = task_state or "open"
        if task_state not in TASK_STATES:
            raise ValueError(f"Invalid task_state: {task_state}")
    else:
        task_state = None
    with closing(get_connection()) as con:
        cur = con.execute(
            """INSERT INTO memories
               (project_id, category, description, experience,
                task_state, embedding)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (project_id, category, description, experience,
             task_state, embedding),
        )
        con.commit()
        return cur.lastrowid

def get_memory(memory_id):
    with closing(get_connection()) as con:
        row = con.execute(
            "SELECT * FROM memories WHERE id = ?", (memory_id,)
        ).fetchone()
        return dict(row) if row else None

def list_memories(project_id, category=None, include_deprecated=False):
    query = "SELECT * FROM memories WHERE project_id = ?"
    params = [project_id]
    if category:
        query += " AND category = ?"
        params.append(category)
    if not include_deprecated:
        query += " AND status = 'active'"
    with closing(get_connection()) as con:
        return [dict(r) for r in con.execute(query, params).fetchall()]

def deprecate_memory(memory_id):
    with closing(get_connection()) as con:
        cur = con.execute(
            """UPDATE memories
               SET status = 'deprecated', updated_at = CURRENT_TIMESTAMP
               WHERE id = ? AND status = 'active'""",
            (memory_id,),
        )
        con.commit()
        return cur.rowcount == 1