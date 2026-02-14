import os
from datetime import datetime, timedelta
from pathlib import Path

from shared.timezone_utils import now_kst
from src.retention.policy import RetentionPolicy
from src.retention.cleaner import RetentionCleaner
from src.backup.manager import BackupManager


def _create_dataset(root: Path) -> None:
    (root / "raw").mkdir(parents=True, exist_ok=True)
    (root / "raw" / "raw_old.jsonl").write_text("old-data")
    (root / "raw" / "raw_new.jsonl").write_text("new-data")


def _set_mtime_days_ago(path: Path, *, days_ago: int) -> None:
    target_time = now_kst() - timedelta(days=days_ago)
    ts = target_time.timestamp()
    os.utime(path, (ts, ts))


def test_maintenance_automation_backup_then_retention(tmp_path: Path):
    """
    E2E (Maintenance):
    1. Identify expired dataset
    2. Backup expired dataset
    3. Delete only after backup success
    """
    # -------------------------------------------------
    # Setup paths
    # -------------------------------------------------
    dataset_root = tmp_path / "dataset"
    backup_root = tmp_path / "backup"

    dataset_root.mkdir()
    backup_root.mkdir()

    _create_dataset(dataset_root)

    raw_old = dataset_root / "raw" / "raw_old.jsonl"
    raw_new = dataset_root / "raw" / "raw_new.jsonl"

    # simulate expiration
    _set_mtime_days_ago(raw_old, days_ago=10)

    # -------------------------------------------------
    # Retention phase (dry-run)
    # -------------------------------------------------
    retention_policy = RetentionPolicy(raw_snapshot_days=1)
    cleaner = RetentionCleaner(retention_policy)

    expired = cleaner.dry_run([raw_old, raw_new])

    assert raw_old in expired
    assert raw_new not in expired

    # -------------------------------------------------
    # Backup phase
    # -------------------------------------------------
    backup_manager = BackupManager(
        source_root=dataset_root,
        backup_root=backup_root,
    )

    manifest = backup_manager.run()

    archive_path = backup_root / manifest.archive_name
    assert archive_path.exists()

    # -------------------------------------------------
    # Retention apply (delete only after backup)
    # -------------------------------------------------
    deleted = cleaner.apply(expired, allow_delete=True)

    assert raw_old in deleted
    assert not raw_old.exists()

    # safety check
    assert raw_new.exists()
