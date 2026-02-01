"""
한국 표준시(KST, Asia/Seoul) 공용 유틸리티.

프로젝트 전역에서 타임스탬프는 KST 기준으로 통일합니다.
stdlib만 사용하여 Python 3.8 및 모든 플랫폼에서 동작합니다.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

# KST = UTC+9 (한국 표준시)
KST = timezone(timedelta(hours=9))


def now_kst() -> datetime:
    """현재 시각을 KST(한국 표준시) 기준으로 반환합니다."""
    return datetime.now(KST)


# Alias for backward compatibility
get_kst_now = now_kst


def to_kst(dt: datetime) -> datetime:
    """datetime을 KST로 변환합니다. naive면 KST로 간주하고 localize."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=KST)
    return dt.astimezone(KST)
