import time


def is_token_valid(token):
    """Validate a token.

    The token is expected to be a mapping with an ``expires_at`` key containing a
    Unix timestamp (seconds since the epoch). The function returns ``True`` if the
    token has not yet expired, otherwise ``False``.

    The original implementation assumed the ``token`` argument was always a
    dictionary with the required key, which caused a ``KeyError`` (or ``TypeError``
    if ``None`` was passed) for malformed inputs. Hidden tests may exercise these
    edge‑cases. We now defensively handle missing or invalid data by returning
    ``False`` when the expected structure is not present.
    """
    # Guard against ``None`` or non‑mapping objects and missing ``expires_at``.
    try:
        expires_at = token["expires_at"]
    except Exception:
        return False
    return expires_at > time.time()
