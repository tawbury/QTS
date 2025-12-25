from pathlib import Path
import pytest

from ops.observer.analysis.loader import (
    load_pattern_records,
    Phase5LoadError,
)

# ---------------------------------------------------------------------
# Test data path (Phase 4 output)
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "observer"
TEST_FILE = DATA_DIR / "observer_test.jsonl"


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------

def test_loader_smoke_success():
    """
    Loader should successfully load valid Phase 4 PatternRecords.
    """
    result = load_pattern_records(
        TEST_FILE,
        strict=True,
        max_records=5,
    )

    assert result.loaded > 0
    assert result.skipped == 0
    assert len(result.records) == result.loaded

    first = result.records[0]
    assert first.observation is not None
    assert isinstance(first.observation, dict)
    assert isinstance(first.schema, dict)
    assert isinstance(first.quality, dict)
    assert isinstance(first.interpretation, dict)


def test_loader_missing_file():
    """
    Missing input file should raise Phase5LoadError.
    """
    with pytest.raises(Phase5LoadError):
        load_pattern_records(
            Path("QTS/data/observer/not_exist.jsonl"),
            strict=True,
        )


def test_loader_invalid_extension():
    """
    Unsupported file extension should raise error.
    """
    with pytest.raises(Phase5LoadError):
        load_pattern_records(
            Path("QTS/data/observer/observer_test.txt"),
            strict=True,
        )


def test_loader_strict_fail_on_invalid_record(tmp_path):
    """
    Invalid JSONL content must fail-fast in strict mode.
    """
    bad_file = tmp_path / "bad.jsonl"
    bad_file.write_text(
        '{"not": "valid"}\n',
        encoding="utf-8"
    )

    with pytest.raises(Phase5LoadError):
        load_pattern_records(
            bad_file,
            strict=True,
        )


def test_loader_non_strict_skips_invalid_record(tmp_path):
    """
    In non-strict mode, invalid records are skipped.
    """
    bad_file = tmp_path / "mixed.jsonl"
    bad_file.write_text(
        '{"not": "valid"}\n'
        '{"metadata": {"_schema": {}, "_quality": {}, "_interpretation": {}},'
        '"observation": {"timestamp": 1.0}}\n',
        encoding="utf-8"
    )

    result = load_pattern_records(
        bad_file,
        strict=False,
    )

    assert result.loaded == 1
    assert result.skipped == 1
