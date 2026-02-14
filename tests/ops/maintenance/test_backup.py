import json
import tarfile
from pathlib import Path

from src.backup.manager import BackupManager


def _create_dummy_files(root: Path) -> None:
    """
    Create dummy dataset files under root.
    """
    (root / "raw").mkdir(parents=True, exist_ok=True)
    (root / "pattern").mkdir(parents=True, exist_ok=True)

    (root / "raw" / "raw_001.jsonl").write_text("raw-1")
    (root / "raw" / "raw_002.jsonl").write_text("raw-2")
    (root / "pattern" / "pattern_001.jsonl").write_text("pattern-1")


def test_backup_manager_creates_archive_and_manifest(tmp_path: Path):
    """
    BackupManager should:
    - create tar.gz archive
    - create manifest.json
    - include all files
    """
    dataset_root = tmp_path / "dataset"
    backup_root = tmp_path / "backup"

    dataset_root.mkdir()
    backup_root.mkdir()

    _create_dummy_files(dataset_root)

    manager = BackupManager(
        source_root=dataset_root,
        backup_root=backup_root,
    )

    manifest = manager.run()

    # -------------------------------------------------
    # 1. archive exists
    # -------------------------------------------------
    archive_path = backup_root / manifest.archive_name
    assert archive_path.exists()
    assert archive_path.suffixes[-2:] == [".tar", ".gz"]

    # -------------------------------------------------
    # 2. manifest file exists
    # -------------------------------------------------
    manifest_path = archive_path.with_suffix(".manifest.json")
    assert manifest_path.exists()

    with manifest_path.open("r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    assert manifest_data["archive_name"] == manifest.archive_name
    assert manifest_data["record_count"] == 3
    assert manifest_data["checksum"] is not None

    # -------------------------------------------------
    # 3. tar contents (relative paths)
    # -------------------------------------------------
    with tarfile.open(archive_path, "r:gz") as tar:
        names = tar.getnames()

    assert "raw/raw_001.jsonl" in names
    assert "raw/raw_002.jsonl" in names
    assert "pattern/pattern_001.jsonl" in names
