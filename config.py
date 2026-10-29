
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

# links (A-MEM-style, one hop)
THETA_LINK = 0.45          # min cosine to link two entries in different categories
MAX_LINKS = 5              # degree cap per entry
MAX_LINKED_IN_PROMPT = 4   # how many linked entries one request may add

# consolidation (Mem0-style)
THETA_DUP = 0.85           # no judge: at or above this, EDIT the existing entry
THETA_JUDGE = 0.55        # with a judge: at or above this, ask it (same / contradicts / unrelated)

RESOLVED_TASK_FACTOR = 0.5 # resolved tasks stay stored but rank lower

# LLM (development provider)
LLM_PROVIDER = "groq"
LLM_MODEL = "openai/gpt-oss-120b"
LLM_MAX_TOKENS = 2048          # reasoning models spend part of this on thinking
LLM_REASONING_EFFORT = None    # "low" | "medium" | "high" if the model supports it
LLM_JSON_MODE = False          # try True later if the model supports json_object
LLM_RETRIES = 3

# write path
MAX_CANDIDATES = 3
TRAJECTORY_MAX_CHARS = 12000

# agent
WORKSPACE_DIR = Path(__file__).resolve().parent / "toy_project"
MAX_AGENT_STEPS = 20
TEST_TIMEOUT = 60
TOOL_OUTPUT_MAX_CHARS = 4000