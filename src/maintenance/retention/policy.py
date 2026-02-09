"""
ops/maintenance/retention/policy.py

DEPRECATED: 이 파일은 호환성을 위해 유지됩니다.
실제 구현은 src.retention.policy.FileRetentionPolicy로 이동했습니다.

Migration:
    # Before
    from src.maintenance.retention.policy import RetentionPolicy

    # After
    from src.retention.policy import FileRetentionPolicy
"""
from __future__ import annotations

# Re-export from canonical location
from src.retention.policy import FileRetentionPolicy

# Backward compatibility alias
RetentionPolicy = FileRetentionPolicy

__all__ = ["RetentionPolicy", "FileRetentionPolicy"]
