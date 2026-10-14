
import sqlite3
from contextlib import closing
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "memory.db"

MEMORY_CATEGORIES = {
    "development_experience",
    "decision",
    "convention",
    "architecture_note",
    "task",
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
  last_used_at TEXT,
  CHECK (
    (category = 'task') OR (task_state IS NULL)
  )
);

CREATE INDEX IF NOT EXISTS idx_mem_lookup
  ON memories (project_id, category, status);
CREATE TABLE IF NOT EXISTS links (
  a_id INTEGER NOT NULL,
  b_id INTEGER NOT NULL,
  similarity REAL NOT NULL,
  PRIMARY KEY (a_id, b_id)
);
"""


def get_connection():
    con = sqlite3.connect(DATABASE_PATH)
    con.row_factory = sqlite3.Row
    return con


def initialize_database():
    with closing(get_connection()) as con:
        con.executescript(SCHEMA)
        con.commit()


def add_memory(
    project_id,
    category,
    description,
    experience,
    task_state=None,
    embedding=None,
):
    if category not in MEMORY_CATEGORIES:
        raise ValueError(f"Unknown category: {category}")

    if category == "task":
        task_state = task_state or "open"
        if task_state not in TASK_STATES:
            raise ValueError(f"Invalid task_state: {task_state}")
    else:
        if task_state is not None:
            raise ValueError("Only task memories can have a task_state.")

    with closing(get_connection()) as con:
        cur = con.execute(
            """INSERT INTO memories
               (project_id, category, description, experience,
                task_state, embedding)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                project_id,
                category,
                description,
                experience,
                task_state,
                embedding,
            ),
        )
        con.commit()
        return cur.lastrowid


def get_memory(memory_id):
    with closing(get_connection()) as con:
        row = con.execute(
            "SELECT * FROM memories WHERE id = ?",
            (memory_id,),
        ).fetchone()
        return dict(row) if row else None


def list_memories(
    project_id,
    category=None,
    include_deprecated=False,
):
    if category is not None and category not in MEMORY_CATEGORIES:
        raise ValueError(f"Unknown category: {category}")

    query = "SELECT * FROM memories WHERE project_id = ?"
    params = [project_id]

    if category is not None:
        query += " AND category = ?"
        params.append(category)

    if not include_deprecated:
        query += " AND status = 'active'"

    with closing(get_connection()) as con:
        rows = con.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def deprecate_memory(memory_id):
    with closing(get_connection()) as con:
        cur = con.execute(
            """UPDATE memories
               SET status = 'deprecated', updated_at = CURRENT_TIMESTAMP
               WHERE id = ? AND status = 'active'""",
            (memory_id,),
        )
        if cur.rowcount == 1:
            con.execute("DELETE FROM links WHERE a_id = ? OR b_id = ?",
                        (memory_id, memory_id))
        con.commit()
        return cur.rowcount == 1


def set_embedding(memory_id, embedding_bytes):
    """Store a serialized float32 embedding for a memory."""
    with closing(get_connection()) as con:
        cur = con.execute(
            """UPDATE memories
               SET embedding = ?,
                   updated_at = CURRENT_TIMESTAMP
               WHERE id = ? AND status = 'active'""",
            (sqlite3.Binary(embedding_bytes), memory_id),
        )
        con.commit()
        return cur.rowcount == 1


def mark_used(memory_ids):
    """Update last_used_at for memories actually added to context."""
    ids = list(set(memory_ids))
    if not ids:
        return

    placeholders = ",".join("?" for _ in ids)

    with closing(get_connection()) as con:
        con.execute(
            f"""UPDATE memories
                SET last_used_at = CURRENT_TIMESTAMP
                WHERE id IN ({placeholders})
                  AND status = 'active'
                  """,
            ids,
        )
        con.commit()

def edit_memory(memory_id, description, experience, embedding=None):
    with closing(get_connection()) as con:
        cur = con.execute(
            """UPDATE memories SET description = ?, experience = ?, embedding = ?,
               updated_at = CURRENT_TIMESTAMP
               WHERE id = ? AND status = 'active'""",
            (description, experience, embedding, memory_id))
        con.commit()
        return cur.rowcount == 1

_TRANSITIONS = {
    "open": {"in_progress", "resolved"},
    "in_progress": {"open", "resolved"},
    "resolved": {"open"},            # reopen only
}

def set_task_state(memory_id, new_state):
    m = get_memory(memory_id)
    if m is None or m["category"] != "task":
        raise ValueError("Not a task entry")
    if new_state not in _TRANSITIONS.get(m["task_state"], set()):
        raise ValueError(f"Invalid transition {m['task_state']} -> {new_state}")
    with closing(get_connection()) as con:
        con.execute("""UPDATE memories SET task_state = ?, updated_at = CURRENT_TIMESTAMP
                       WHERE id = ?""", (new_state, memory_id))
        con.commit()

def _enforce_cap(con, node, max_links):
    rows = con.execute(
        "SELECT b_id FROM links WHERE a_id = ? ORDER BY similarity DESC, b_id",
        (node,)).fetchall()
    for row in rows[max_links:]:                    # drop the lowest-similarity links
        other = row["b_id"]
        con.execute("DELETE FROM links WHERE (a_id=? AND b_id=?) OR (a_id=? AND b_id=?)",
                    (node, other, other, node))

def add_link(a_id, b_id, similarity, max_links):
    if a_id == b_id:
        return
    with closing(get_connection()) as con:
        for x, y in ((a_id, b_id), (b_id, a_id)):
            con.execute("INSERT OR REPLACE INTO links (a_id, b_id, similarity) VALUES (?,?,?)",
                        (x, y, similarity))
        _enforce_cap(con, a_id, max_links)
        _enforce_cap(con, b_id, max_links)
        con.commit()

def get_links(memory_id):
    with closing(get_connection()) as con:
        rows = con.execute(
            "SELECT b_id, similarity FROM links WHERE a_id = ? ORDER BY similarity DESC",
            (memory_id,)).fetchall()
        return [(row["b_id"], row["similarity"]) for row in rows]

def clear_links(memory_id):
    with closing(get_connection()) as con:
        con.execute("DELETE FROM links WHERE a_id = ? OR b_id = ?", (memory_id, memory_id))
        con.commit()

def linked_entries(seed_ids):
    """One hop: active entries linked to any seed, strongest link first."""
    if not seed_ids:
        return []
    marks = ",".join("?" * len(seed_ids))
    with closing(get_connection()) as con:
        rows = con.execute(
            f"""SELECT m.*, MAX(l.similarity) AS link_sim
                FROM links l JOIN memories m ON m.id = l.b_id
                WHERE l.a_id IN ({marks}) AND m.status = 'active'
                GROUP BY m.id ORDER BY link_sim DESC""",
            list(seed_ids)).fetchall()
        return [dict(row) for row in rows]