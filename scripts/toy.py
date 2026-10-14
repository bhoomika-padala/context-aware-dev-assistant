"""  python scripts/toy.py reset      both bugs present (start of session 1)
     python scripts/toy.py session2   tokens.py fixed, refresh.py still buggy """
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

TOKENS_BUGGY = '''import time


def is_token_valid(token):
    """token = {"user": str, "expires_at": unix seconds}. True while not expired."""
    return token["expires_at"] < time.time()
'''
TOKENS_FIXED = TOKENS_BUGGY.replace("<", ">")

REFRESH_BUGGY = '''import time


def can_refresh(refresh_token):
    """refresh_token = {"user": str, "expires_at": unix seconds}. Only unexpired tokens may refresh."""
    return refresh_token["expires_at"] < time.time()
'''

TEST = '''import time
from {mod} import {fn}


def test_unexpired_is_accepted():
    assert {fn}({{"user": "a", "expires_at": time.time() + 60}})


def test_expired_is_rejected():
    assert not {fn}({{"user": "a", "expires_at": time.time() - 60}})
'''

def write(files):
    config.WORKSPACE_DIR.mkdir(exist_ok=True)
    for name, text in files.items():
        (config.WORKSPACE_DIR / name).write_text(text, encoding="utf-8")

mode = sys.argv[1] if len(sys.argv) > 1 else ""
tests = {"test_tokens.py": TEST.format(mod="tokens", fn="is_token_valid"),
         "test_refresh.py": TEST.format(mod="refresh", fn="can_refresh")}
if mode == "reset":
    write({"tokens.py": TOKENS_BUGGY, "refresh.py": REFRESH_BUGGY, **tests})
    print("toy project reset: both bugs present")
elif mode == "session2":
    write({"tokens.py": TOKENS_FIXED, "refresh.py": REFRESH_BUGGY, **tests})
    print("toy project: tokens fixed, refresh still buggy")
else:
    print(__doc__)