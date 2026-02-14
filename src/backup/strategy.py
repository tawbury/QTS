"""
Backup Strategy Pattern

두 가지 백업 전략을 제공합니다:
1. ArchiveBackupStrategy: tar.gz 아카이브 방식 (기존 ops/backup/manager.py)
2. FileBackupStrategy: 파일별 복사 방식 (기존 ops/maintenance/backup/runner.py)

Usage:
    from src.backup.strategy import ArchiveBackupStrategy, FileBackupStrategy
    from src.backup.manager import BackupManager

    # 아카이브 방식
    manager = BackupManager(strategy=ArchiveBackupStrategy())
    result = manager.run(source_root, backup_root)

    # 파일 복사 방식
    manager = BackupManager(strategy=FileBackupStrategy())
    result = manager.run(source_root, backup_root)
"""
from __future__ import annotations

import json
import shutil
import tarfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .checksum import calculate_sha256
from .manifest import BackupManifest
from ..shared.timezone_utils import now_kst


# BackupResult를 여기서 정의하여 순환 import 방지
# (src.maintenance._types.BackupResult와 호환되는 구조)
@dataclass(frozen=True)
class BackupResult:
    """백업 결과."""
    success: bool
    backup_root: Optional[Path] = None
    manifest_path: Optional[Path] = None
    error: Optional[str] = None


def _kst_stamp() -> str:
    return now_kst().strftime("%Y%m%d_%H%M%S")


def _kst_now() -> datetime:
    return now_kst()


@dataclass(frozen=True)
class BackupPlan:
    """백업 계획 정의."""
    source_files: List[Path]
    source_root: Path
    backup_root: Path


class BackupStrategy(ABC):
    """백업 전략 추상 베이스 클래스."""

    @abstractmethod
    def execute(self, plan: BackupPlan) -> BackupResult:
        """
        백업을 실행합니다.

        Args:
            plan: 백업 계획

        Returns:
            BackupResult: 백업 결과
        """
        ...

    @abstractmethod
    def get_manifest(self, plan: BackupPlan, backup_path: Path) -> BackupManifest:
        """
        백업 매니페스트를 생성합니다.

        Args:
            plan: 백업 계획
            backup_path: 백업 결과 경로

        Returns:
            BackupManifest: 백업 메타데이터
        """
        ...


class ArchiveBackupStrategy(BackupStrategy):
    """
    tar.gz 아카이브 방식 백업.

    특징:
    - 단일 압축 파일로 백업
    - SHA256 체크섬 생성
    - manifest.json 파일 생성
    """

    def execute(self, plan: BackupPlan) -> BackupResult:
        try:
            plan.backup_root.mkdir(parents=True, exist_ok=True)

            timestamp = _kst_now()
            archive_name = f"observer_backup_{timestamp.strftime('%Y%m%d_%H%M%S')}.tar.gz"
            archive_path = plan.backup_root / archive_name

            # 아카이브 생성
            with tarfile.open(archive_path, "w:gz") as tar:
                for path in plan.source_files:
                    try:
                        arcname = path.relative_to(plan.source_root)
                    except ValueError:
                        arcname = path.name
                    tar.add(path, arcname=str(arcname))

            # 체크섬 계산
            checksum = calculate_sha256(archive_path)

            # 매니페스트 생성
            manifest = BackupManifest(
                backup_at=timestamp,
                source=str(plan.source_root),
                archive_name=archive_name,
                record_count=len(plan.source_files),
                checksum=checksum,
            )

            manifest_path = archive_path.with_suffix(".manifest.json")
            self._write_manifest(manifest, manifest_path)

            return BackupResult(
                success=True,
                backup_root=archive_path,
                manifest_path=manifest_path,
            )

        except Exception as e:
            return BackupResult(success=False, error=f"{type(e).__name__}: {e}")

    def get_manifest(self, plan: BackupPlan, backup_path: Path) -> BackupManifest:
        checksum = calculate_sha256(backup_path)
        return BackupManifest(
            backup_at=_kst_now(),
            source=str(plan.source_root),
            archive_name=backup_path.name,
            record_count=len(plan.source_files),
            checksum=checksum,
        )

    def _write_manifest(self, manifest: BackupManifest, path: Path) -> None:
        data = {
            "backup_at": manifest.backup_at.isoformat(),
            "source": manifest.source,
            "archive_name": manifest.archive_name,
            "record_count": manifest.record_count,
            "checksum": manifest.checksum,
        }
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


class FileBackupStrategy(BackupStrategy):
    """
    파일별 복사 방식 백업.

    특징:
    - 개별 파일 복사 (shutil.copy2)
    - 디렉토리 구조 유지
    - manifest.json 파일 생성

    Idempotency: 같은 파일이 이미 백업돼 있으면 덮어씀.
    """

    def execute(self, plan: BackupPlan) -> BackupResult:
        try:
            stamp = _kst_stamp()
            target_root = plan.backup_root / f"backup_{stamp}"
            target_root.mkdir(parents=True, exist_ok=True)

            copied: List[str] = []
            for src in plan.source_files:
                # 상대 경로 계산 (안전 처리)
                try:
                    rel = src.relative_to(plan.source_root)
                except ValueError:
                    rel = Path(src.name)

                dst = target_root / rel.as_posix().lstrip("/\\")
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                copied.append(str(dst))

            # 매니페스트 생성
            manifest_data = {
                "schema_version": "1.0",
                "captured_at_kst": now_kst().isoformat(),
                "file_count": len(plan.source_files),
                "copied_files": copied,
            }
            manifest_path = target_root / "manifest.json"
            manifest_path.write_text(
                json.dumps(manifest_data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )

            return BackupResult(
                success=True,
                backup_root=target_root,
                manifest_path=manifest_path,
            )

        except Exception as e:
            return BackupResult(success=False, error=f"{type(e).__name__}: {e}")

    def get_manifest(self, plan: BackupPlan, backup_path: Path) -> BackupManifest:
        return BackupManifest(
            backup_at=_kst_now(),
            source=str(plan.source_root),
            archive_name=backup_path.name,
            record_count=len(plan.source_files),
            checksum=None,  # 파일 복사 방식은 개별 체크섬 없음
        )


def build_backup_plan(
    source_root: Path,
    backup_root: Path,
    include_globs: Optional[List[str]] = None,
) -> BackupPlan:
    """
    백업 계획을 생성합니다.

    Args:
        source_root: 백업 대상 소스 루트
        backup_root: 백업 결과 저장 루트
        include_globs: 포함할 파일 패턴 (None이면 전체)

    Returns:
        BackupPlan: 백업 계획
    """
    if include_globs:
        files: List[Path] = []
        for g in include_globs:
            files.extend([p for p in source_root.rglob(g) if p.is_file()])
    else:
        files = [
            p for p in source_root.rglob("*")
            if p.is_file() and not p.name.startswith(".")
        ]

    return BackupPlan(
        source_files=sorted(set(files)),
        source_root=source_root,
        backup_root=backup_root,
    )
