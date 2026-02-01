"""
Runtime Checks

실행 환경 검증 및 사전 조건 확인 유틸리티.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

_log = logging.getLogger(__name__)


def check_python_version(min_version: tuple = (3, 11)) -> bool:
    """
    Python 버전 확인.

    Args:
        min_version: 최소 요구 버전 (major, minor)

    Returns:
        bool: 요구 버전 이상이면 True
    """
    current = sys.version_info[:2]
    if current < min_version:
        _log.error(
            f"Python {min_version[0]}.{min_version[1]}+ required, "
            f"but {current[0]}.{current[1]} found"
        )
        return False
    return True


def check_project_structure(project_root: Path) -> Dict[str, bool]:
    """
    프로젝트 구조 확인.

    Args:
        project_root: 프로젝트 루트 경로

    Returns:
        Dict[str, bool]: 각 필수 경로의 존재 여부
    """
    required_paths = {
        "src": project_root / "src",
        "config": project_root / "config",
        "config/local": project_root / "config" / "local",
        "config/schema": project_root / "config" / "schema",
        "tests": project_root / "tests",
    }

    results = {}
    for name, path in required_paths.items():
        exists = path.exists()
        results[name] = exists
        if not exists:
            _log.warning(f"Required path not found: {name} ({path})")

    return results


def check_required_files(project_root: Path) -> Dict[str, bool]:
    """
    필수 파일 확인.

    Args:
        project_root: 프로젝트 루트 경로

    Returns:
        Dict[str, bool]: 각 필수 파일의 존재 여부
    """
    required_files = {
        "config_local.json": project_root / "config" / "local" / "config_local.json",
        "credentials.json": project_root / "config" / "schema" / "credentials.json",
    }

    results = {}
    for name, path in required_files.items():
        exists = path.exists()
        results[name] = exists
        if not exists:
            _log.warning(f"Required file not found: {name} ({path})")

    return results


def preflight_check(project_root: Path, verbose: bool = False) -> bool:
    """
    전체 사전 검증 실행.

    Args:
        project_root: 프로젝트 루트 경로
        verbose: 상세 로그 출력 여부

    Returns:
        bool: 모든 검증 통과 시 True
    """
    checks_passed = True

    # Python 버전
    if not check_python_version():
        checks_passed = False

    # 프로젝트 구조
    structure = check_project_structure(project_root)
    if not all(structure.values()):
        checks_passed = False
        if verbose:
            _log.warning(f"Project structure check failed: {structure}")

    # 필수 파일
    files = check_required_files(project_root)
    if not files.get("config_local.json"):
        checks_passed = False
        _log.error("config_local.json is required but not found")

    if verbose:
        _log.info(f"Preflight check: {'PASSED' if checks_passed else 'FAILED'}")

    return checks_passed
