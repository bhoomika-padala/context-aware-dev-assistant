import time


def can_refresh(refresh_token):
    """refresh_token = {"user": str, "expires_at": unix seconds}. Only unexpired tokens may refresh."""
    return refresh_token["expires_at"] > time.time()
