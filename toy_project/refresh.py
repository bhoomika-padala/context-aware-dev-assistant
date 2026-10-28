import time


def can_refresh(refresh_token):
    """Validate a refresh token.

    The ``refresh_token`` is expected to be a mapping with an ``expires_at`` key
    containing a Unix timestamp (seconds since the epoch). Only unexpired tokens
    may be used to obtain a new access token. If the input is malformed or the
    token has expired, the function returns ``False``.
    """
    try:
        expires_at = refresh_token["expires_at"]
    except Exception:
        return False
    return expires_at > time.time()
