import re
from datetime import datetime, timezone

import numpy as np
from rank_bm25 import BM25Okapi

import config
from memory import database as db

_model = None

def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(config.EMBEDDING_MODEL)  # ~90 MB first download
    return _model

def embed(text):
    # normalized vectors, so a dot product equals cosine similarity
    return _get_model().encode(text, normalize_embeddings=True).astype("float32")

def to_blob(vec):
    return vec.astype("float32").tobytes()

def from_blob(blob):
    return np.frombuffer(blob, dtype="float32")

def entry_text(m):
    return f"{m['description']} {m['experience']}"

def index_memory(memory_id):
    """Compute and store the embedding for one entry. Call after add or edit."""
    m = db.get_memory(memory_id)
    db.set_embedding(memory_id, to_blob(embed(entry_text(m))))

def tokenize(text):
    # keeps identifiers such as parse_config as single tokens
    return re.findall(r"[a-z0-9_]+", text.lower())

def _age_days(m):
    ts = m["last_used_at"] or m["updated_at"]
    t = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    return max((datetime.now(timezone.utc) - t).total_seconds() / 86400, 0.0)

def _score_category(entries, query, q_vec):
    texts = [entry_text(m) for m in entries]
    mat = np.vstack([
        from_blob(m["embedding"]) if m["embedding"] else embed(t)
        for m, t in zip(entries, texts)
    ])
    cos = mat @ q_vec

    bm25_raw = np.clip(
        BM25Okapi([tokenize(t) for t in texts]).get_scores(tokenize(query)),
        0, None)
    top = bm25_raw.max()
    bm25_norm = bm25_raw / top if top > 0 else np.zeros_like(bm25_raw)

    recency = np.exp(-config.RECENCY_LAMBDA * np.array([_age_days(m) for m in entries]))
    score = config.ALPHA * cos + config.BETA * bm25_norm + config.GAMMA * recency
    state = np.array([config.RESOLVED_TASK_FACTOR if m["task_state"] == "resolved" else 1.0
                      for m in entries])
    score = score * state

    hits = []
    for i, m in enumerate(entries):
        if cos[i] >= config.MIN_COSINE or bm25_raw[i] >= config.MIN_BM25:
            hits.append({
                "id": m["id"], "category": m["category"],
                "description": m["description"], "experience": m["experience"],
                "score": float(score[i]), "cosine": float(cos[i]),
                "bm25": float(bm25_raw[i]), "recency": float(recency[i]),
            })
    hits.sort(key=lambda h: h["score"], reverse=True)
    return hits[:config.TOP_N]

def retrieve(project_id, query, categories=None):
    """Return {category: [entries]}. Categories with nothing relevant are omitted."""
    cats = categories or (*config.UNBOUNDED, *config.BOUNDED)
    q_vec = None
    out = {}
    for cat in cats:
        entries = db.list_memories(project_id, category=cat)  # active only
        if not entries:
            continue
        if cat in config.BOUNDED:
            # small and stable: included directly, no scoring
            entries.sort(key=lambda m: m["updated_at"], reverse=True)
            out[cat] = [{"id": m["id"], "category": cat,
                         "description": m["description"],
                         "experience": m["experience"], "score": None}
                        for m in entries[:config.BOUNDED_CAP]]
        else:
            if q_vec is None:
                q_vec = embed(query)
            hits = _score_category(entries, query, q_vec)
            if hits:
                out[cat] = hits
    return out