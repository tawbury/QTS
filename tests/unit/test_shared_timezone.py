"""
src/shared/timezone_utils.py 단위 테스트.

테스트 대상:
- KST 상수
- now_kst / get_kst_now
- to_kst
- utcnow
- utc_to_kst
- is_kst
- format_iso_kst
"""
from datetime import datetime, timezone, timedelta
from src.shared.timezone_utils import (
    KST,
    now_kst,
    get_kst_now,
    to_kst,
    utcnow,
    utc_to_kst,
    is_kst,
    format_iso_kst,
)


class TestKSTConstant:
    """KST 상수 테스트."""

    def test_kst_offset(self):
        assert KST.utcoffset(None) == timedelta(hours=9)


class TestNowKst:
    """now_kst 함수 테스트."""

    def test_returns_aware_datetime(self):
        dt = now_kst()
        assert dt.tzinfo is not None

    def test_returns_kst(self):
        dt = now_kst()
        assert dt.utcoffset() == timedelta(hours=9)

    def test_alias(self):
        """get_kst_now은 now_kst의 alias."""
        assert get_kst_now is now_kst


class TestToKst:
    """to_kst 함수 테스트."""

    def test_naive_becomes_kst(self):
        naive = datetime(2026, 1, 1, 12, 0, 0)
        result = to_kst(naive)
        assert result.tzinfo == KST
        assert result.hour == 12

    def test_utc_converts_to_kst(self):
        utc_dt = datetime(2026, 1, 1, 3, 0, 0, tzinfo=timezone.utc)
        result = to_kst(utc_dt)
        assert result.hour == 12  # UTC+9


class TestUtcnow:
    """utcnow 함수 테스트."""

    def test_returns_aware(self):
        dt = utcnow()
        assert dt.tzinfo == timezone.utc


class TestUtcToKst:
    """utc_to_kst 함수 테스트."""

    def test_aware_utc(self):
        utc_dt = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        result = utc_to_kst(utc_dt)
        assert result.hour == 9
        assert result.utcoffset() == timedelta(hours=9)

    def test_naive_assumed_utc(self):
        naive_dt = datetime(2026, 1, 1, 0, 0, 0)
        result = utc_to_kst(naive_dt)
        assert result.hour == 9


class TestIsKst:
    """is_kst 함수 테스트."""

    def test_kst_datetime(self):
        dt = datetime(2026, 1, 1, tzinfo=KST)
        assert is_kst(dt) is True

    def test_utc_datetime(self):
        dt = datetime(2026, 1, 1, tzinfo=timezone.utc)
        assert is_kst(dt) is False


class TestFormatIsoKst:
    """format_iso_kst 함수 테스트."""

    def test_with_specific_datetime(self):
        dt = datetime(2026, 6, 15, 14, 30, 0, tzinfo=KST)
        result = format_iso_kst(dt)
        assert "2026-06-15" in result
        assert "14:30" in result

    def test_without_argument(self):
        result = format_iso_kst()
        assert "+09:00" in result

    def test_converts_utc_to_kst(self):
        utc_dt = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        result = format_iso_kst(utc_dt)
        assert "09:00" in result
