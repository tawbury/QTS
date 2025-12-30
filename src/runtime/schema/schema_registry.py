from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from .schema_models import SchemaLoadResult, SchemaSnapshot


@dataclass(frozen=True)
class SchemaRegistryConfig:
    """
    Phase F rule:
    - external code must NOT reference schema.json path directly.
    - registry is the single entrypoint.
    """
    # Prefer architecture default
    primary_path: Path
    # Optional fallbacks to tolerate transition
    fallback_paths: tuple[Path, ...] = ()


class SchemaRegistry:
    def __init__(self, cfg: SchemaRegistryConfig):
        self._cfg = cfg
        self._cached: Optional[Dict[str, Any]] = None
        self._cached_path: Optional[Path] = None

    @staticmethod
    def default(project_root: Path) -> "SchemaRegistry":
        """
        Default per Schema Auto Architecture:
          /config/schema/schema.json
        Fallbacks:
          /schema.json (repo root)  # temporary compatibility
        """
        primary = project_root / "config" / "schema" / "schema.json"
        fallback = (project_root / "schema.json",)
        return SchemaRegistry(SchemaRegistryConfig(primary_path=primary, fallback_paths=fallback))

    def load(self, force_reload: bool = False) -> SchemaLoadResult:
        if self._cached is not None and not force_reload:
            return SchemaLoadResult(ok=True, path=str(self._cached_path), schema=self._cached)

        candidates = (self._cfg.primary_path,) + self._cfg.fallback_paths
        for p in candidates:
            if p.exists() and p.is_file():
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                    self._cached = data
                    self._cached_path = p
                    return SchemaLoadResult(ok=True, path=str(p), schema=data)
                except Exception as e:
                    return SchemaLoadResult(ok=False, path=str(p), error=f"failed to parse schema json: {e}")

        return SchemaLoadResult(ok=False, path=str(self._cfg.primary_path), error="schema.json not found")

    def get_active_schema(self) -> Dict[str, Any]:
        res = self.load(force_reload=False)
        if not res.ok or res.schema is None:
            # Phase F: fail-closed. For now we raise here, but next step we will convert this into "guard result" flow.
            raise RuntimeError(f"SchemaRegistry load failed: {res.error} (path={res.path})")
        return res.schema

    def get_active_schema_path(self) -> str:
        res = self.load(force_reload=False)
        if not res.ok:
            return res.path
        return res.path

    def get_schema_version(self) -> str:
        schema = self.get_active_schema()
        v = schema.get("schema_version")
        return str(v) if v is not None else "UNKNOWN"

    def build_snapshot(self) -> SchemaSnapshot:
        schema = self.get_active_schema()
        normalized = normalize_schema_structure(schema)
        return SchemaSnapshot(schema_version=str(schema.get("schema_version", "UNKNOWN")), normalized=normalized)


def normalize_schema_structure(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize current schema.json variants into a single structural format used for hash/diff.

    Supported per your current schema.json:
      - sheets.<name>.columns  (A/B/..)
      - sheets.<name>.fields   (type/header_key)
      - sheets.R_Dash.blocks   (cells/ranges)
    """
    sheets = schema.get("sheets", {}) or {}
    norm_sheets: Dict[str, Any] = {}

    for sheet_key, spec in sheets.items():
        if not isinstance(spec, dict):
            continue

        sheet_name = spec.get("sheet_name", sheet_key)
        row_start = spec.get("row_start", None)

        mapping: Dict[str, Any] = {}
        layout: Optional[Dict[str, Any]] = None

        if "columns" in spec and isinstance(spec["columns"], dict):
            mapping = dict(spec["columns"])

        elif "fields" in spec and isinstance(spec["fields"], dict):
            # Convert fields -> mapping using header_key as the structural anchor
            # (Schema Auto engine will later remap header_key -> actual column)
            for field_name, f in spec["fields"].items():
                if isinstance(f, dict) and "header_key" in f:
                    mapping[field_name] = f["header_key"]
                else:
                    mapping[field_name] = f  # fallback

        # UI blocks
        if "blocks" in spec and isinstance(spec["blocks"], dict):
            # preserve full layout for diffing
            layout = spec["blocks"]
            # also provide a flattened mapping for deterministic hash (optional)
            # but hash will still include layout via 'layout'
            # mapping remains empty unless you want to flatten.
            if not mapping:
                mapping = {}

        norm_sheets[sheet_key] = {
            "sheet_name": sheet_name,
            "row_start": row_start,
            "mapping": mapping,
            "layout": layout,
        }

    return {"sheets": norm_sheets}
