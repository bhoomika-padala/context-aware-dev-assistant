
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent

# Load local environment variables before reading settings.
load_dotenv(PROJECT_ROOT / ".env")

# Embedding model
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "all-MiniLM-L6-v2",
)

# Hybrid retrieval weights
ALPHA = float(os.getenv("ALPHA", "0.5"))
BETA = float(os.getenv("BETA", "0.4"))
GAMMA = float(os.getenv("GAMMA", "0.1"))

# Recency and relevance thresholds
RECENCY_LAMBDA = float(os.getenv("RECENCY_LAMBDA", "0.02"))
MIN_COSINE = float(os.getenv("MIN_COSINE", "0.30"))
MIN_BM25 = float(os.getenv("MIN_BM25", "1.0"))

# Retrieval limits
TOP_N = int(os.getenv("TOP_N", "5"))
BOUNDED_CAP = int(os.getenv("BOUNDED_CAP", "20"))

# Memory categories
UNBOUNDED = (
    "development_experience",
    "decision",
    "task",
)

BOUNDED = (
    "convention",
    "architecture_note",
)

# Persistent database location
DATABASE_PATH = Path(
    os.getenv("DATABASE_PATH", str(PROJECT_ROOT / "memory.db"))
)

CATEGORY_BUDGET_TOKENS = {
    "development_experience": 600,
    "decision": 400,
    "task": 300,
    "convention": 300,
    "architecture_note": 300,
}
CHARS_PER_TOKEN = 4   # rough estimate, good enough for budgeting
