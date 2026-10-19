import time
from tokens import is_token_valid


def test_unexpired_is_accepted():
    assert is_token_valid({"user": "a", "expires_at": time.time() + 60})


def test_expired_is_rejected():
    assert not is_token_valid({"user": "a", "expires_at": time.time() - 60})
