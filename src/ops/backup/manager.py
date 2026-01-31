"""
Backup Manager (Strategy Pattern 적용)

Local backup manager for observer datasets.

Usage:
    from ops.backup.manager import BackupManager
    from ops.backup.strategy import ArchiveBackupStrategy, FileBackupStrategy

    # 기본 (아카이브 방식)
    manager = BackupManager(source_root, backup_root)
    manifest = manager.run()

    # Strategy 지정
    manager = BackupManager(source_root, backup_root, strategy=FileBackupStrategy())
    result = manager.run_with_result()
"""
from __future__ import annotations

import json
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

from .checksum import calculate_sha256
from .manifest import BackupManifest
from .strategy import (
    BackupStrategy,
    ArchiveBackupStrategy,
    FileBackupStrategy,
    BackupPlan,
    build_backup_plan,
)

if TYPE_CHECKING:
    from ops.maintenance._types import BackupResult


class BackupManager:
    """
    Local backup manager for observer datasets.

    This manager:
    - creates a tar.gz archive (default) or file copies
    - generates a manifest
    - calculates checksum (archive mode only)

    Strategy Pattern:
    - ArchiveBackupStrategy: tar.gz 아카이브 (기본)
    - FileBackupStrategy: 파일별 복사
    """

    def __init__(
        self,
        source_root: Path,
        backup_root: Path,
        *,
        strategy: Optional[BackupStrategy] = None,
    ):
        self.source_root = source_root
        self.backup_root = backup_root
        self.strategy = strategy or ArchiveBackupStrategy()

    # -------------------------
    # helpers
    # -------------------------

    def _now(self) -> datetime:
        return datetime.now(tz=timezone.utc)

    def _collect_files(self) -> List[Path]:
        if not self.source_root.exists():
            return []

        return [
            p
            for p in self.source_root.rglob("*")
            if p.is_file() and not p.name.startswith(".")
        ]

    def _ensure_backup_root(self) -> None:
        self.backup_root.mkdir(parents=True, exist_ok=True)

    def _archive_name(self, timestamp: datetime) -> str:
        return f"observer_backup_{timestamp.strftime('%Y%m%d_%H%M%S')}.tar.gz"

    # -------------------------
    # public API
    # -------------------------

    def dry_run(self) -> List[Path]:
        """
        Returns files that WOULD be included in backup.
        """
        return self._collect_files()

    def run(self) -> BackupManifest:
        """
        Execute backup using legacy API (returns BackupManifest).

        Creates:
        - tar.gz archive (or file copies depending on strategy)
        - manifest.json
        """
        # Legacy 호환: ArchiveBackupStrategy 사용 시 기존 동작 유지
        if isinstance(self.strategy, ArchiveBackupStrategy):
            return self._run_archive_legacy()

        # Strategy 패턴 사용
        plan = build_backup_plan(self.source_root, self.backup_root)
        result = self.strategy.execute(plan)

        if not result.success:
            raise RuntimeError(f"Backup failed: {result.error}")

        return self.strategy.get_manifest(plan, result.backup_root)

    def run_with_result(self) -> "BackupResult":
        """
        Execute backup using Strategy pattern (returns BackupResult).

        Returns:
            BackupResult: 백업 결과 (success, backup_root, manifest_path, error)
        """
        plan = build_backup_plan(self.source_root, self.backup_root)
        return self.strategy.execute(plan)

    def _run_archive_legacy(self) -> BackupManifest:
        """기존 아카이브 방식 백업 (하위 호환성)."""
        self._ensure_backup_root()

        files = self._collect_files()
        timestamp = self._now()
        archive_name = self._archive_name(timestamp)
        archive_path = self.backup_root / archive_name

        # 1. create archive
        with tarfile.open(archive_path, "w:gz") as tar:
            for path in files:
                arcname = path.relative_to(self.source_root)
                tar.add(path, arcname=str(arcname))

        # 2. checksum
        checksum = calculate_sha256(archive_path)

        # 3. manifest
        manifest = BackupManifest(
            backup_at=timestamp,
            source=str(self.source_root),
            archive_name=archive_name,
            record_count=len(files),
            checksum=checksum,
        )

        manifest_path = archive_path.with_suffix(".manifest.json")
        self._write_manifest(manifest, manifest_path)

        return manifest

    def _write_manifest(self, manifest: BackupManifest, path: Path) -> None:
        data = {
            "backup_at": manifest.backup_at.isoformat(),
            "source": manifest.source,
            "archive_name": manifest.archive_name,
            "record_count": manifest.record_count,
            "checksum": manifest.checksum,
        }

        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


# ============================================================
# Convenience Functions (ops/maintenance/backup/runner.py 호환)
# ============================================================

def run_backup(plan: BackupPlan, strategy: Optional[BackupStrategy] = None) -> "BackupResult":
    """
    백업을 실행합니다.

    Args:
        plan: 백업 계획
        strategy: 백업 전략 (기본: FileBackupStrategy)

    Returns:
        BackupResult: 백업 결과
    """
    from ops.maintenance._types import BackupResult as BR
    strategy = strategy or FileBackupStrategy()
    return strategy.execute(plan)
