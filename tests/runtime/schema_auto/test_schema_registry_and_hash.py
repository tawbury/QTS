from __future__ import annotations

from pathlib import Path

from runtime.schema.schema_registry import SchemaRegistry
from runtime.schema.schema_hash import compute_schema_hash


def test_schema_registry_loads_schema_and_builds_snapshot(tmp_path: Path):
    # Arrange
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(
        """
        {
          "schema_version": "1.0.0",
          "sheets": {
            "Position": {
              "sheet_name": "Position",
              "row_start": 2,
              "columns": { "symbol": "A", "qty": "B" }
            }
          }
        }
        """.strip(),
        encoding="utf-8",
    )

    reg = SchemaRegistry.default(project_root=tmp_path)

    # Act
    schema = reg.get_active_schema()
    snap = reg.build_snapshot()
    h = compute_schema_hash(snap.normalized)

    # Assert
    assert schema["schema_version"] == "1.0.0"
    assert snap.schema_version == "1.0.0"
    assert "sheets" in snap.normalized
    assert isinstance(h, str)
    assert len(h) == 64


def test_schema_hash_is_deterministic(tmp_path: Path):
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(
        """
        {
          "schema_version": "1.0.0",
          "sheets": {
            "Position": {
              "sheet_name": "Position",
              "row_start": 2,
              "columns": { "symbol": "A", "qty": "B" }
            }
          }
        }
        """.strip(),
        encoding="utf-8",
    )

    reg = SchemaRegistry.default(project_root=tmp_path)

    snap1 = reg.build_snapshot()
    h1 = compute_schema_hash(snap1.normalized)

    reg.load(force_reload=True)
    snap2 = reg.build_snapshot()
    h2 = compute_schema_hash(snap2.normalized)

    assert h1 == h2
