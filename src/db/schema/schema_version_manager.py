from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .schema_diff import SchemaDiffReport, classify_version_bump


@dataclass(frozen=True)
class VersionUpdateResult:
    updated: bool
    old_version: str
    new_version: str
    bump: str
    reason: str
    backup_path: Path | None


class SchemaVersionManager:
    """
    Phase F rules:
    - Humans do not edit schema_version.
    - Diff drives version bump.
    - Backup is mandatory before overwrite.
    """

    def __init__(self, schema_path: Path, backup_dir: Path, changelog_path: Path):
        self.schema_path = schema_path
        self.backup_dir = backup_dir
        self.changelog_path = changelog_path

    @staticmethod
    def default(project_root: Path) -> "SchemaVersionManager":
        return SchemaVersionManager(
            schema_path=project_root / "config" / "schema" / "schema.json",
            backup_dir=project_root / "backup" / "schema",
            changelog_path=project_root / "backup" / "schema" / "schema_changes.jsonl",
        )

    def apply_diff(self, diff: SchemaDiffReport) -> VersionUpdateResult:
        bump = classify_version_bump(diff)

        if bump.bump == "none":
            return VersionUpdateResult(
                updated=False,
                old_version=self._read_version(),
                new_version=self._read_version(),
                bump="none",
                reason=bump.reason,
                backup_path=None,
            )

        self.backup_dir.mkdir(parents=True, exist_ok=True)

        schema = json.loads(self.schema_path.read_text(encoding="utf-8"))
        old_version = str(schema.get("schema_version", "0.0.0"))

        new_version = self._bump_version(old_version, bump.bump)
        schema["schema_version"] = new_version

        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"schema_{old_version}_{ts}.json"
        backup_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")

        self.schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")

        self._append_changelog(diff, old_version, new_version, bump)

        return VersionUpdateResult(
            updated=True,
            old_version=old_version,
            new_version=new_version,
            bump=bump.bump,
            reason=bump.reason,
            backup_path=backup_path,
        )

    # ---------------- internals ----------------

    def _read_version(self) -> str:
        schema = json.loads(self.schema_path.read_text(encoding="utf-8"))
        return str(schema.get("schema_version", "0.0.0"))

    @staticmethod
    def _bump_version(v: str, kind: str) -> str:
        major, minor, *_ = (v.split(".") + ["0", "0"])[:2]
        major_i, minor_i = int(major), int(minor)

        if kind == "major":
            return f"{major_i + 1}.0"
        if kind == "minor":
            return f"{major_i}.{minor_i + 1}"
        return v

    def _append_changelog(
        self,
        diff: SchemaDiffReport,
        old_v: str,
        new_v: str,
        bump,
    ) -> None:
        entry = {
            "ts": datetime.utcnow().isoformat(),
            "old_version": old_v,
            "new_version": new_v,
            "bump": bump.bump,
            "reason": bump.reason,
            "items": [i.__dict__ for i in diff.items],
        }
        with self.changelog_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
