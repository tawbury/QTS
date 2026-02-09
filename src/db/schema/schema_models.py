from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class SchemaLoadResult:
    ok: bool
    path: str
    schema: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass(frozen=True)
class SchemaSnapshot:
    """
    Snapshot is a normalized, deterministic representation of schema structure.
    - Designed for hashing/diffing only (no live data).
    """
    schema_version: str
    normalized: Dict[str, Any]


@dataclass(frozen=True)
class VersionBump:
    """
    Recommended bump derived from diff classification.
    """
    bump: str  # "major" | "minor" | "none"
    reason: str
