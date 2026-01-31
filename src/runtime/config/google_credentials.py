from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from shared import paths


@dataclass(frozen=True)
class GoogleCredentialsRef:
    path: Path


def resolve_google_credentials() -> GoogleCredentialsRef:
    """
    Resolve canonical google credentials path from paths.py.

    Does not create files.
    Existence validation is explicit.
    """
    p = paths.google_credentials_path()

    # Fail fast: operational misconfiguration should be loud.
    if not p.exists():
        raise FileNotFoundError(
            f"Google credentials not found at canonical path: {p}. "
            f"Expected: schema/secrets/google_credentials.json"
        )

    return GoogleCredentialsRef(path=p)
