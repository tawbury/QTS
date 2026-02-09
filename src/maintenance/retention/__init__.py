"""
ops/maintenance/retention 모듈

파일 시스템 기반 retention 스캔 및 정책을 제공합니다.
"""
from src.retention.policy import FileRetentionPolicy
from src.maintenance.retention.scanner import scan_expired

# Backward compatibility
RetentionPolicy = FileRetentionPolicy

__all__ = ["RetentionPolicy", "FileRetentionPolicy", "scan_expired"]
