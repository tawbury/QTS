from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from src.maintenance._types import MaintenanceReport
from src.maintenance.backup.runner import build_backup_plan, run_backup
from src.maintenance.cleanup.executor import execute_cleanup
from src.retention.policy import FileRetentionPolicy
from src.maintenance.retention.scanner import scan_expired


def run_maintenance(
    *,
    data_root: Path,
    backup_root: Path,
    policy: Optional[FileRetentionPolicy] = None,
    include_backup_globs: Optional[List[str]] = None,
) -> MaintenanceReport:
    """
    Phase 6.5 단일 진입점.
    - backup 먼저
    - backup 성공시에만 retention/cleanup 의미가 생김
    - 실패하면 삭제 0 보장
    """
    policy = policy or FileRetentionPolicy()

    backup_plan = build_backup_plan(data_root=data_root, backup_root=backup_root, include_globs=include_backup_globs)
    backup_result = run_backup(backup_plan)

    candidates = scan_expired(data_root=data_root, policy=policy)

    cleanup_result = execute_cleanup(
        candidates=candidates,
        backup_success=backup_result.success,
    )

    return MaintenanceReport(
        backup=backup_result,
        candidates=candidates,
        cleanup=cleanup_result,
    )
