from __future__ import annotations

from pathlib import Path

from .schema_registry import SchemaRegistry
from .schema_guard import SchemaGuardResult


def check_schema_before_extract(project_root: Path, expected_version: str) -> SchemaGuardResult:
    """
    Phase F rule:
    - mismatch => BLOCK (no exception)
    - caller decides how to halt execution
    """
    registry = SchemaRegistry.default(project_root)
    current_version = registry.get_schema_version()

    if current_version != expected_version:
        return SchemaGuardResult(
            allowed=False,
            reason="schema_version_mismatch",
            expected_version=expected_version,
            current_version=current_version,
        )

    return SchemaGuardResult(
        allowed=True,
        reason="schema_ok",
        expected_version=expected_version,
        current_version=current_version,
    )
