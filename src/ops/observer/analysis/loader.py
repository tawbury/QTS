from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

from .contracts.pattern_record_contract import PatternRecordContract


class Phase5LoadError(Exception):
    """Raised when Phase 5 loader cannot read or parse input records."""


@dataclass(frozen=True)
class LoadResult:
    records: List[PatternRecordContract]
    total_lines: int
    loaded: int
    skipped: int


def load_pattern_records(
    input_path: Union[str, Path],
    *,
    strict: bool = True,
    max_records: Optional[int] = None,
    encoding: str = "utf-8",
) -> LoadResult:
    """
    Load Phase 4 output into Phase 5 PatternRecordContract.

    Canonical rules:
    - Phase 4 is treated as external producer.
    - metadata is REQUIRED.
    - observation is OPTIONAL:
        * if present, used directly
        * if absent, synthesized from top-level fields
    - _schema / _quality / _interpretation are OPTIONAL.
    """
    path = Path(input_path)

    if not path.exists():
        raise Phase5LoadError(f"Input file not found: {path}")

    suffix = path.suffix.lower()
    if suffix not in {".jsonl", ".json"}:
        raise Phase5LoadError(
            f"Unsupported input format: {suffix} (expected .jsonl or .json)"
        )

    records: List[PatternRecordContract] = []
    total_lines = 0
    loaded = 0
    skipped = 0

    try:
        if suffix == ".jsonl":
            for total_lines, raw in enumerate(
                _iter_jsonl(path, encoding=encoding), start=1
            ):
                rec = _parse_one(raw, strict=strict, idx=total_lines)
                if rec is None:
                    skipped += 1
                else:
                    records.append(rec)
                    loaded += 1

                if max_records is not None and loaded >= max_records:
                    break

        else:
            data = _read_json(path, encoding=encoding)
            if not isinstance(data, list):
                raise Phase5LoadError("JSON input must be a list of records.")

            total_lines = len(data)

            for idx, raw in enumerate(data, start=1):
                rec = _parse_one(raw, strict=strict, idx=idx)
                if rec is None:
                    skipped += 1
                else:
                    records.append(rec)
                    loaded += 1

                if max_records is not None and loaded >= max_records:
                    break

    except Phase5LoadError:
        raise
    except Exception as e:
        raise Phase5LoadError(f"Failed to load records from {path}: {e}") from e

    if strict and loaded == 0:
        raise Phase5LoadError("No valid records loaded in strict mode.")

    return LoadResult(
        records=records,
        total_lines=total_lines,
        loaded=loaded,
        skipped=skipped,
    )


# =====================================================================
# Internal helpers
# =====================================================================

def _iter_jsonl(path: Path, *, encoding: str) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding=encoding) as f:
        for line_no, line in enumerate(f, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                obj = json.loads(text)
            except json.JSONDecodeError as e:
                raise Phase5LoadError(
                    f"Invalid JSON at line {line_no}: {e}"
                ) from e

            if not isinstance(obj, dict):
                raise Phase5LoadError(
                    f"JSONL record must be an object at line {line_no}"
                )
            yield obj


def _read_json(path: Path, *, encoding: str) -> Any:
    with path.open("r", encoding=encoding) as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            raise Phase5LoadError(f"Invalid JSON file: {e}") from e


def _parse_one(
    raw: Any,
    *,
    strict: bool,
    idx: Optional[int] = None,
) -> Optional[PatternRecordContract]:
    prefix = f"[record {idx}] " if idx is not None else ""

    if not isinstance(raw, dict):
        if strict:
            raise Phase5LoadError(prefix + "Record is not an object/dict.")
        return None

    metadata = raw.get("metadata")
    if not isinstance(metadata, dict):
        if strict:
            raise Phase5LoadError(prefix + "Missing or invalid 'metadata' dict.")
        return None

    # --------------------------------------------------
    # Observation handling (Phase 4 compatible)
    # --------------------------------------------------
    if "observation" in raw:
        observation = raw.get("observation")
        if not isinstance(observation, dict):
            if strict:
                raise Phase5LoadError(prefix + "Invalid 'observation' field.")
            return None
    else:
        # Synthesize observation from top-level fields
        observation = {
            k: v
            for k, v in raw.items()
            if k not in {"metadata", "_schema", "_quality", "_interpretation"}
        }

    try:
        return PatternRecordContract(
            session_id=metadata.get("session_id", ""),
            generated_at=metadata.get("generated_at", ""),
            observation=observation,
            schema=raw.get("_schema", {}) or {},
            quality=raw.get("_quality", {}) or {},
            interpretation=raw.get("_interpretation", {}) or {},
        )
    except Exception as e:
        if strict:
            raise Phase5LoadError(prefix + f"Failed to parse record: {e}") from e
        return None
