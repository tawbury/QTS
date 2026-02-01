from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SchemaGuardResult:
    allowed: bool
    reason: str
    expected_version: str
    current_version: str
