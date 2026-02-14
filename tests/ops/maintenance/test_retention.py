import os
from datetime import datetime, timedelta
from pathlib import Path

from shared.timezone_utils import now_kst
from src.retention.policy import RetentionPolicy
from src.retention.cleaner import RetentionCleaner


def _create_file_with_mtime(
    path: Path,
    *,
    days_ago: int,
) -> None:
    path.write_text("dummy")

    target_time = now_kst() - timedelta(days=days_ago)
    ts = target_time.timestamp()

    os.utime(path, (ts, ts))


def test_retention_dry_run_identifies_expired_raw_snapshots(tmp_path: Path):
    """
    Dry-run should identify expired files
    but must NOT delete anything.
    """
    policy = RetentionPolicy(
        raw_snapshot_days=7,
        pattern_record_days=30,
        decision_snapshot_days=None,
    )
    cleaner = RetentionCleaner(policy)

    # expired raw snapshot
    raw_old = tmp_path / "raw_snapshot_001.jsonl"
    _create_file_with_mtime(raw_old, days_ago=10)

    # valid raw snapshot
    raw_new = tmp_path / "raw_snapshot_002.jsonl"
    _create_file_with_mtime(raw_new, days_ago=2)

    files = [raw_old, raw_new]

    expired = cleaner.dry_run(files)

    assert raw_old in expired
    assert raw_new not in expired

    # dry-run must not delete files
    assert raw_old.exists()
    assert raw_new.exists()


def test_retention_respects_pattern_and_decision_policies(tmp_path: Path):
    """
    Pattern records expire, decision snapshots never expire.
    """
    policy = RetentionPolicy(
        raw_snapshot_days=7,
        pattern_record_days=5,
        decision_snapshot_days=None,
    )
    cleaner = RetentionCleaner(policy)

    pattern_old = tmp_path / "pattern_record_001.jsonl"
    _create_file_with_mtime(pattern_old, days_ago=10)

    decision_old = tmp_path / "decision_snapshot_001.jsonl"
    _create_file_with_mtime(decision_old, days_ago=100)

    files = [pattern_old, decision_old]

    expired = cleaner.dry_run(files)

    assert pattern_old in expired
    assert decision_old not in expired


def test_retention_apply_deletes_only_expired_files(tmp_path: Path):
    """
    apply() should delete expired files
    ONLY when allow_delete=True.
    """
    policy = RetentionPolicy(raw_snapshot_days=3)
    cleaner = RetentionCleaner(policy)

    raw_old = tmp_path / "raw_snapshot_old.jsonl"
    _create_file_with_mtime(raw_old, days_ago=5)

    raw_new = tmp_path / "raw_snapshot_new.jsonl"
    _create_file_with_mtime(raw_new, days_ago=1)

    files = [raw_old, raw_new]

    deleted = cleaner.apply(files, allow_delete=True)

    assert raw_old in deleted
    assert raw_new not in deleted

    assert not raw_old.exists()
    assert raw_new.exists()


def test_retention_apply_without_permission_does_not_delete(tmp_path: Path):
    """
    apply() without allow_delete must:
    - identify expired files
    - NOT delete anything
    """
    policy = RetentionPolicy(raw_snapshot_days=1)
    cleaner = RetentionCleaner(policy)

    raw_old = tmp_path / "raw_snapshot_001.jsonl"
    _create_file_with_mtime(raw_old, days_ago=3)

    files = [raw_old]

    expired = cleaner.apply(files, allow_delete=False)

    # expired candidate should be returned
    assert raw_old in expired

    # but file must NOT be deleted
    assert raw_old.exists()
