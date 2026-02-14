from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from .schema_models import VersionBump


@dataclass(frozen=True)
class DiffItem:
    sheet: str
    kind: str  # "FIELD_ADDED" | "FIELD_REMOVED" | "FIELD_MOVED" | "STRUCT_CHANGED"
    key: str
    before: Any = None
    after: Any = None


@dataclass(frozen=True)
class SchemaDiffReport:
    changed: bool
    items: List[DiffItem]


def classify_version_bump(report: SchemaDiffReport) -> VersionBump:
    """
    Phase F enforced policy:
    - any removal -> major
    - any other change -> minor
    - none -> none
    """
    if not report.changed:
        return VersionBump(bump="none", reason="no schema structure change")

    if any(i.kind == "FIELD_REMOVED" for i in report.items):
        return VersionBump(bump="major", reason="required or mapped field removed")

    return VersionBump(bump="minor", reason="schema structure changed (non-removal)")


def diff_normalized(before: Dict[str, Any], after: Dict[str, Any]) -> SchemaDiffReport:
    """
    Compare normalized schema structures.
    Normalized schema shape:
      {
        "sheets": {
          "<sheet_key>": {
            "sheet_name": "...",
            "row_start": 2,
            "mapping": { "<field>": "<col_or_cell_or_header_key>" },
            "layout": {... optional ...}  # for blocks (R_Dash)
          }
        }
      }
    """
    items: List[DiffItem] = []

    b_sheets = before.get("sheets", {})
    a_sheets = after.get("sheets", {})

    all_sheet_keys = sorted(set(b_sheets.keys()) | set(a_sheets.keys()))

    for sk in all_sheet_keys:
        b = b_sheets.get(sk)
        a = a_sheets.get(sk)

        if b is None:
            items.append(DiffItem(sheet=sk, kind="STRUCT_CHANGED", key="__sheet__", before=None, after="added"))
            continue
        if a is None:
            items.append(DiffItem(sheet=sk, kind="STRUCT_CHANGED", key="__sheet__", before="removed", after=None))
            continue

        b_map = b.get("mapping", {}) or {}
        a_map = a.get("mapping", {}) or {}

        b_keys = set(b_map.keys())
        a_keys = set(a_map.keys())

        for k in sorted(b_keys - a_keys):
            items.append(DiffItem(sheet=sk, kind="FIELD_REMOVED", key=k, before=b_map.get(k), after=None))

        for k in sorted(a_keys - b_keys):
            items.append(DiffItem(sheet=sk, kind="FIELD_ADDED", key=k, before=None, after=a_map.get(k)))

        for k in sorted(b_keys & a_keys):
            if b_map.get(k) != a_map.get(k):
                items.append(DiffItem(sheet=sk, kind="FIELD_MOVED", key=k, before=b_map.get(k), after=a_map.get(k)))

        # Compare row_start and sheet_name as structural changes
        for meta_key in ("sheet_name", "row_start"):
            if b.get(meta_key) != a.get(meta_key):
                items.append(DiffItem(sheet=sk, kind="STRUCT_CHANGED", key=meta_key, before=b.get(meta_key), after=a.get(meta_key)))

        # Optional: blocks/layout changes (R_Dash)
        if (b.get("layout") or {}) != (a.get("layout") or {}):
            if (b.get("layout") is not None) or (a.get("layout") is not None):
                items.append(DiffItem(sheet=sk, kind="STRUCT_CHANGED", key="layout", before=b.get("layout"), after=a.get("layout")))

    return SchemaDiffReport(changed=len(items) > 0, items=items)
