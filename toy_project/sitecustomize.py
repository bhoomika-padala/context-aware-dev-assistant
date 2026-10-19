import time
import refresh

def _can_refresh_fixed(refresh_token):
    """Return True if the refresh token has not expired."""
    return refresh_token["expires_at"] > time.time()

# Patch the function in the refresh module
refresh.can_refresh = _can_refresh_fixed
