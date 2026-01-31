"""
Retention Policy 모듈 (통합 버전)

이 모듈은 두 가지 보관 정책을 정의합니다:
1. DataRetentionPolicy: 데이터 유형별 보관 기간 (Observer 출력용)
2. FileRetentionPolicy: 파일 시스템 패턴 기반 TTL (Maintenance용)

Refactoring Note:
- 기존 ops/retention/policy.py (RetentionPolicy) → DataRetentionPolicy
- 기존 ops/maintenance/retention/policy.py (RetentionPolicy) → FileRetentionPolicy
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import List, Optional


@dataclass(frozen=True)
class DataRetentionPolicy:
    """
    데이터 유형별 보관 기간 정책.

    Observer 출력 데이터(raw_snapshot, pattern_record, decision_snapshot)의
    보관 기간을 정의합니다.

    All durations are expressed in days.
    None means 'keep forever'.
    """

    raw_snapshot_days: Optional[int] = 7
    pattern_record_days: Optional[int] = 30
    decision_snapshot_days: Optional[int] = None  # keep forever

    def is_infinite(self, days: Optional[int]) -> bool:
        return days is None


@dataclass(frozen=True)
class FileRetentionPolicy:
    """
    파일 시스템 패턴 기반 TTL 정책.

    Maintenance 작업에서 파일 만료 판단에 사용됩니다.
    glob 패턴으로 대상 파일을 지정하고, mtime 기준으로 만료를 판단합니다.

    Args:
        ttl_days: mtime 기준 만료 일수 (기본 7일)
        include_globs: 스캔 포함 패턴 (None이면 전체)
        exclude_globs: 제외 패턴
    """
    ttl_days: int = 7
    include_globs: Optional[List[str]] = None
    exclude_globs: Optional[List[str]] = None

    @property
    def ttl(self) -> timedelta:
        return timedelta(days=int(self.ttl_days))


# ============================================================
# Backward Compatibility Aliases (Deprecation Warning)
# ============================================================
# 기존 코드 호환을 위한 별칭. 향후 제거 예정.
# TODO: 다음 마이너 버전에서 제거
RetentionPolicy = DataRetentionPolicy
