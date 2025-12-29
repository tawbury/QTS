# tools/structure_clean/scanner.py
from __future__ import annotations

from pathlib import Path
from typing import Set, List


EXCLUDED_DIR_NAMES: Set[str] = {
    ".git",
    ".idea",
    ".vscode",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
}

INCLUDED_FILE_SUFFIXES: Set[str] = {
    ".py",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
}


def scan_full_tree(*, project_root: Path) -> List[Path]:
    """
    구조 인식 목적의 전체 스캔.
    - 의미 없는 디렉터리는 스캔 단계에서 차단
    - 파일은 화이트리스트 기반
    """
    paths: List[Path] = []

    for p in project_root.rglob("*"):
        rel = p.relative_to(project_root)

        if any(part in EXCLUDED_DIR_NAMES for part in rel.parts):
            continue

        if p.is_dir():
            paths.append(p)
            continue

        if p.suffix not in INCLUDED_FILE_SUFFIXES:
            continue

        paths.append(p)

    return paths
