"""
Backup module for QTS Observer datasets.

Purpose:
- Local backup of retained datasets
- Integrity verification (checksum)
- Backup manifest generation

Strategy Pattern:
- ArchiveBackupStrategy: tar.gz 아카이브 방식
- FileBackupStrategy: 파일별 복사 방식

Usage:
    from ops.backup import BackupManager, ArchiveBackupStrategy, FileBackupStrategy

    # 아카이브 방식 (기본)
    manager = BackupManager(source_root, backup_root)
    manifest = manager.run()

    # 파일 복사 방식
    manager = BackupManager(source_root, backup_root, strategy=FileBackupStrategy())
    result = manager.run_with_result()
"""
from ops.backup.manager import BackupManager, run_backup
from ops.backup.manifest import BackupManifest
from ops.backup.checksum import calculate_sha256
from ops.backup.strategy import (
    BackupStrategy,
    ArchiveBackupStrategy,
    FileBackupStrategy,
    BackupPlan,
    build_backup_plan,
)

__all__ = [
    "BackupManager",
    "BackupManifest",
    "calculate_sha256",
    "BackupStrategy",
    "ArchiveBackupStrategy",
    "FileBackupStrategy",
    "BackupPlan",
    "build_backup_plan",
    "run_backup",
]
