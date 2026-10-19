import time


def is_token_valid(token):
    """token = {"user": str, "expires_at": unix seconds}. True while not expired."""
    return token["expires_at"] > time.time()
