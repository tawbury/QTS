"""
paths.py (shared)

QTS project-wide canonical path resolver with deployment mode switching.

This module defines the single source of truth for all filesystem paths
used across the QTS project, including:
- execution
- ops modules
- pytest
- local scripts
- K8s/Docker deployment paths

Location: src/shared/paths.py (project root resolved via __file__).
Design principles:
- Resilient to folder restructuring
- No relative depth assumptions (no parents[n])
- Project-level, not package-level
- Environment variable overrides for deployment flexibility
- Observer pattern: deployment mode switching (local/docker/kubernetes)
"""

import os
from pathlib import Path
from typing import Dict, List, Optional

# ============================================================
# Platform Constants (K8s/Docker)
# ============================================================
PLATFORM_CODE_ROOT = Path(os.environ.get("PLATFORM_CODE_ROOT", "/opt/platform/qts"))
PLATFORM_RUNTIME_ROOT = Path(os.environ.get("PLATFORM_RUNTIME_ROOT", "/opt/platform/runtime/qts"))


# ============================================================
# Deployment Mode Detection
# ============================================================
def get_deployment_mode() -> str:
    """
    QTS_DEPLOYMENT_MODE 환경 변수 기반 배포 모드 결정.

    Returns:
        str: "local" | "dev" | "docker" | "kubernetes"
    """
    return os.environ.get("QTS_DEPLOYMENT_MODE", "local")


def is_container_mode() -> bool:
    """Check if running in container (docker or kubernetes)."""
    return get_deployment_mode() in ("docker", "kubernetes", "container")


def load_env_by_run_mode() -> Dict[str, str]:
    """
    계층적 환경 변수 로딩 (Observer 패턴).

    로딩 순서 (first match wins):
    1. OS 환경 변수 (항상 최우선)
    2. config/.env.{mode} (환경별 경로/호스트)
    3. config/.env.shared (공통 설정: TZ, MARKET_CODE)
    4. config/.env (시크릿, LOCAL 모드만)

    모드 매핑:
      "dev"       → .env.local
      "docker"    → .env.container
      "kubernetes"→ .env.container
      "local"     → .env.local

    Returns:
        Dict[str, str]: Loaded environment variables
    """
    from dotenv import dotenv_values

    mode = get_deployment_mode()
    env_suffix_map = {
        "dev": "local",
        "local": "local",
        "docker": "container",
        "kubernetes": "container",
        "container": "container",
    }
    suffix = env_suffix_map.get(mode, "local")

    result: Dict[str, str] = {}
    config_path = config_dir()

    # Load in reverse priority order (later values override earlier)
    env_files = [
        config_path / ".env.shared",
        config_path / f".env.{suffix}",
    ]

    # Only load .env (secrets) in local mode
    if mode in ("local", "dev"):
        env_files.insert(0, config_path / ".env")

    for env_file in env_files:
        if env_file.exists():
            result.update(dotenv_values(env_file))

    # OS environment variables always win
    for key in result:
        if key in os.environ:
            result[key] = os.environ[key]

    return result


# ============================================================
# Project Root Resolver
# ============================================================

def _resolve_project_root(start: Optional[Path] = None) -> Path:
    """
    Resolve QTS project root directory.

    Resolution rules (first match wins):
    1. Container mode: Use PLATFORM_CODE_ROOT environment variable
    2. Directory containing '.git'
    3. Directory containing 'pyproject.toml'
    4. Directory containing both 'src' and 'tests'
    5. Directory containing 'src' (container fallback)
    """

    # Container mode: use PLATFORM_CODE_ROOT directly
    if is_container_mode():
        code_root = PLATFORM_CODE_ROOT
        if code_root.exists() and (code_root / "src").exists():
            return code_root

    # Normal QTS project resolution
    current = start.resolve() if start else Path(__file__).resolve()

    for parent in [current] + list(current.parents):
        if (parent / ".git").exists():
            return parent
        if (parent / "pyproject.toml").exists():
            return parent
        if (parent / "src").exists() and (parent / "tests").exists():
            return parent
        if (parent / "app").exists() and (parent / "shared").exists():
            return parent

    # Container fallback: directory containing 'src'
    if is_container_mode():
        for parent in [current] + list(current.parents):
            if (parent / "src").exists():
                return parent

    raise RuntimeError("QTS project root could not be resolved")


# ============================================================
# Canonical QTS Paths (Single Source of Truth)
# ============================================================

def project_root() -> Path:
    """QTS project root directory"""
    return _resolve_project_root()


# Alias for backward compatibility
get_project_root = project_root


# ------------------------------------------------------------
# Core directories
# ------------------------------------------------------------

def src_dir() -> Path:
    return project_root() / "src"


def ops_dir() -> Path:
    return src_dir() / "ops"


def runtime_dir() -> Path:
    """
    Canonical runtime engine directory.
    (Non-ops execution core)
    """
    return src_dir() / "runtime"


def tests_dir() -> Path:
    return project_root() / "tests"


def data_dir() -> Path:
    """
    Canonical data root directory with environment override.

    Resolution order:
    1. QTS_DATA_DIR environment variable
    2. PLATFORM_RUNTIME_ROOT/data (container mode)
    3. project_root()/data (local mode)

    Phase F:
    - This directory is reserved for ephemeral / runtime-only artifacts.
    - Long-lived JSON / JSONL assets MUST NOT be placed here.
    """
    env_path = os.environ.get("QTS_DATA_DIR")
    if env_path:
        return Path(env_path).resolve()
    if is_container_mode():
        return PLATFORM_RUNTIME_ROOT / "data"
    return project_root() / "data"


def log_dir() -> Path:
    """
    Canonical log root directory with environment override.

    Resolution order:
    1. QTS_LOG_DIR environment variable
    2. PLATFORM_RUNTIME_ROOT/logs (container mode)
    3. project_root()/logs (local mode)
    """
    env_path = os.environ.get("QTS_LOG_DIR")
    if env_path:
        return Path(env_path).resolve()
    if is_container_mode():
        return PLATFORM_RUNTIME_ROOT / "logs"
    return project_root() / "logs"


def config_dir() -> Path:
    """
    Canonical config root directory with environment override.

    Resolution order:
    1. QTS_CONFIG_DIR environment variable
    2. PLATFORM_RUNTIME_ROOT/config (container mode)
    3. project_root()/config (local mode)

    Phase F:
    - Long-lived operational assets live here.
    """
    env_path = os.environ.get("QTS_CONFIG_DIR")
    if env_path:
        return Path(env_path).resolve()
    if is_container_mode():
        return PLATFORM_RUNTIME_ROOT / "config"
    path = project_root() / "config"
    # Only auto-create in local mode
    if not is_container_mode():
        path.mkdir(parents=True, exist_ok=True)
    return path


def observer_data_dir() -> Path:
    """
    Observer 데이터 소스 디렉토리 (읽기 전용 마운트).

    Resolution order:
    1. OBSERVER_DATA_SOURCE_DIR environment variable
    2. Default: /opt/platform/runtime/observer/data

    This directory is mounted read-only from Observer's data PVC
    via hostPath in Kubernetes.
    """
    return Path(os.environ.get(
        "OBSERVER_DATA_SOURCE_DIR",
        "/opt/platform/runtime/observer/data"
    ))


def observer_asset_dir() -> Path:
    """
    Canonical Observer ASSET directory for JSON/JSONL artifacts.
    """
    return observer_data_dir() / "assets"


# ------------------------------------------------------------
# Ops subdomains
# ------------------------------------------------------------

def ops_decision_pipeline_dir() -> Path:
    return ops_dir() / "decision_pipeline"


def ops_retention_dir() -> Path:
    return ops_dir() / "retention"


def ops_runtime_dir() -> Path:
    """
    Runtime bridge / runner layer under ops.
    """
    return ops_dir() / "runtime"


def ops_backup_dir() -> Path:
    return ops_dir() / "backup"


# ------------------------------------------------------------
# Test-related paths (read-only usage)
# ------------------------------------------------------------

def tests_ops_dir() -> Path:
    return tests_dir() / "ops"


def tests_ops_decision_dir() -> Path:
    return tests_ops_dir() / "decision"


# ============================================================
# Schema / Asset canonical paths
# ============================================================

def schema_dir() -> Path:
    """
    Canonical schema root directory.

    This directory contains:
    - structural schemas
    - json definitions
    - external interface assets
    - secrets (non-versioned)

    This directory itself is NOT auto-created.
    """
    return project_root() / "schema"


def schema_secrets_dir() -> Path:
    """
    Canonical secrets directory under schema.

    This directory contains non-versioned secret assets
    such as credentials, tokens, and private keys.

    IMPORTANT:
    - This directory MUST NOT be auto-created.
    - Existence is considered an operational responsibility.
    """
    return schema_dir() / "secrets"


# ------------------------------------------------------------
# External service credentials (read-only, no auto-create)
# ------------------------------------------------------------

def google_credentials_path() -> Path:
    """
    Canonical Google API credentials path.

    Expected location:
    schema/secrets/google_credentials.json

    This function DOES NOT validate existence.
    Validation is responsibility of the consumer.
    """
    return schema_secrets_dir() / "google_credentials.json"


# ============================================================
# Execution Contract Validation (K8s)
# ============================================================

def validate_execution_contract() -> List[str]:
    """
    K8s 실행 계약 검증 (Observer 패턴).

    확인 사항:
    - 필수 디렉토리 존재
    - 필수 환경 변수 설정
    - Observer 데이터 소스 접근 가능 (kubernetes 모드)

    Returns:
        List[str]: 오류 메시지 리스트 (빈 리스트 = 성공)

    Usage:
        errors = validate_execution_contract()
        if errors:
            for error in errors:
                logger.error(error)
            sys.exit(1)
    """
    errors: List[str] = []

    # Required directories check
    required_dirs = [
        ("data", data_dir),
        ("logs", log_dir),
        ("config", config_dir),
    ]

    for name, dir_func in required_dirs:
        path = dir_func()
        if not path.exists():
            errors.append(f"Required directory missing: {name} at {path}")

    # Observer data source check (kubernetes mode only)
    if get_deployment_mode() == "kubernetes":
        obs_dir = observer_data_dir()
        if not obs_dir.exists():
            errors.append(f"Observer data source missing: {obs_dir}")

    # Required environment variables check (container mode)
    if is_container_mode():
        required_env_vars = ["DB_HOST", "DB_PORT", "DB_NAME"]
        for var in required_env_vars:
            if not os.environ.get(var):
                errors.append(f"Required environment variable not set: {var}")

    return errors


def log_path_summary() -> None:
    """
    현재 경로 설정 요약 로깅 (디버그용).

    Logs all resolved paths and deployment mode for debugging.
    """
    import logging
    logger = logging.getLogger(__name__)

    mode = get_deployment_mode()
    logger.info(f"QTS Deployment Mode: {mode}")
    logger.info(f"  project_root: {project_root()}")
    logger.info(f"  data_dir:     {data_dir()}")
    logger.info(f"  log_dir:      {log_dir()}")
    logger.info(f"  config_dir:   {config_dir()}")

    if is_container_mode():
        logger.info(f"  observer_data_dir: {observer_data_dir()}")
