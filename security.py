from pathlib import Path

from fastapi import HTTPException


WORKSPACE_ROOT = Path(__file__).resolve().parent / "toy_project"


def validate_workspace_path(path: str):
    """Resolve a path and ensure it stays within the local toy_project."""
    if not isinstance(path, str) or not path.strip():
        raise HTTPException(status_code=403, detail="Invalid workspace path")

    workspace = WORKSPACE_ROOT.resolve(strict=True)
    requested = Path(path)
    candidate = requested if requested.is_absolute() else workspace / requested

    try:
        # Resolve existing parents first so symlinks cannot disguise traversal.
        resolved = candidate.resolve(strict=False)
        resolved.relative_to(workspace)
    except (OSError, RuntimeError, ValueError) as exc:
        raise HTTPException(
            status_code=403,
            detail="Path must remain inside toy_project",
        ) from exc

    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(workspace)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Workspace path not found") from exc
    except (OSError, RuntimeError, ValueError) as exc:
        raise HTTPException(
            status_code=403,
            detail="Path must remain inside toy_project",
        ) from exc

    return resolved
