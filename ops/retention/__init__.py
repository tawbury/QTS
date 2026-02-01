"""
Retention module for QTS Observer outputs.

Purpose:
- Define data retention rules
- Scan persisted datasets
- Apply retention cleanup (dry-run by default)

Observer-Core is NOT imported here.

Policy Classes:
- DataRetentionPolicy: 데이터 유형별 보관 기간 (raw, pattern, decision)
- FileRetentionPolicy: 파일 시스템 패턴 기반 TTL (maintenance용)
- RetentionPolicy: DataRetentionPolicy의 별칭 (하위 호환)
"""
from ops.retention.policy import (
    DataRetentionPolicy,
    FileRetentionPolicy,
    RetentionPolicy,  # backward compat alias
)

__all__ = [
    "DataRetentionPolicy",
    "FileRetentionPolicy",
    "RetentionPolicy",
]
