"""
한국 표준시(KST, Asia/Seoul) 공용 유틸리티.

프로젝트 전역에서 타임스탬프는 KST 기준으로 통일합니다.
stdlib만 사용하여 Python 3.8 및 모든 플랫폼에서 동작합니다.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

# KST = UTC+9 (한국 표준시)
KST = timezone(timedelta(hours=9))


def now_kst() -> datetime:
    """현재 시각을 KST(한국 표준시) 기준으로 반환합니다."""
    return datetime.now(KST)


# Alias for backward compatibility
get_kst_now = now_kst


def to_kst(dt: datetime) -> datetime:
    """
    datetime을 KST로 변환합니다.
    - naive: KST로 간주하고 localize (주의: 시스템 로컬 타임이 아님을 가정)
    - aware: KST로 astimezone 변환
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=KST)
    return dt.astimezone(KST)


def utcnow() -> datetime:
    """현재 시각을 UTC 기준으로 반환합니다 (timezone-aware)."""
    return datetime.now(timezone.utc)


def utc_to_kst(dt: datetime) -> datetime:
    """UTC 시간을 KST로 변환합니다."""
    if dt.tzinfo is None:
        # Naive datetime is assumed to be UTC if passed to this function
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(KST)


def is_kst(dt: datetime) -> bool:
    """datetime 객체가 KST인지 확인합니다."""
    return dt.tzinfo == KST


def format_iso_kst(dt: Optional[datetime] = None) -> str:
    """datetime을 ISO 8601 형식의 문자열로 반환합니다 (KST 기준)."""
    if dt is None:
        dt = now_kst()
    else:
        dt = to_kst(dt)
    return dt.isoformat()
