from __future__ import annotations

import hashlib
import json
from typing import Any, Dict


def _canonical_json(obj: Any) -> str:
    """
    Deterministic JSON for hashing.
    - sort_keys=True
    - compact separators
    """
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def compute_schema_hash(snapshot_normalized: Dict[str, Any]) -> str:
    """
    Hash is based on normalized structure only (not schema_version).
    """
    payload = _canonical_json(snapshot_normalized).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
