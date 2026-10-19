import time
from refresh import can_refresh


def test_unexpired_is_accepted():
    assert can_refresh({"user": "a", "expires_at": time.time() + 60})


def test_expired_is_rejected():
    assert not can_refresh({"user": "a", "expires_at": time.time() - 60})
