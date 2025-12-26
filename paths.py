"""
paths.py

QTS project-wide canonical path resolver.

This module defines the single source of truth for all filesystem paths
used across the QTS project, including:
- execution (main.py)
- observer / ops modules
- pytest
- local scripts

Design principles:
- Resilient to folder restructuring
- No relative depth assumptions (no parents[n])
- Project-level, not package-level
"""

from pathlib import Path
from typing import Optional


# ============================================================
# Project Root Resolver
# ============================================================

def _resolve_project_root(start: Optional[Path] = None) -> Path:
    """
    Resolve QTS project root directory.

    Resolution rules (first match wins):
    1. Directory containing '.git'
    2. Directory containing 'pyproject.toml'
    3. Directory containing both 'src' and 'tests'
    """
    current = start.resolve() if start else Path(__file__).resolve()

    for parent in [current] + list(current.parents):
        if (parent / ".git").exists():
            return parent
        if (parent / "pyproject.toml").exists():
            return parent
        if (parent / "src").exists() and (parent / "tests").exists():
            return parent

    raise RuntimeError("QTS project root could not be resolved")


# ============================================================
# Canonical QTS Paths (Single Source of Truth)
# ============================================================

def project_root() -> Path:
    """QTS project root directory"""
    return _resolve_project_root()


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
    Canonical data root directory.
    (No subdirectory creation beyond this level)
    """
    return project_root() / "data"


# ------------------------------------------------------------
# Ops subdomains
# ------------------------------------------------------------

def ops_observer_dir() -> Path:
    return ops_dir() / "observer"


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
# Observer-specific canonical paths
# ------------------------------------------------------------

def observer_data_dir() -> Path:
    """
    Canonical observer runtime data directory.

    All observer-generated jsonl files
    must be placed here.
    """
    path = data_dir() / "observer"
    path.mkdir(parents=True, exist_ok=True)
    return path


# ------------------------------------------------------------
# Test-related paths (read-only usage)
# ------------------------------------------------------------

def tests_ops_dir() -> Path:
    return tests_dir() / "ops"


def tests_ops_e2e_dir() -> Path:
    return tests_ops_dir() / "e2e"


def tests_ops_decision_dir() -> Path:
    return tests_ops_dir() / "decision"


def tests_ops_observation_dir() -> Path:
    return tests_ops_dir() / "observation"
