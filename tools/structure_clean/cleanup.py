# tools/structure_clean/cleanup.py
from __future__ import annotations
from pathlib import Path
from typing import List
import shutil

# 공통 제외 목록: 이 폴더들 내부의 파일은 절대 건드리지 않습니다.
EXCLUDED_DIR_NAMES = {".git", ".idea", ".vscode", ".venv", "venv", "env"}

def find_cleanup_candidates(*, project_root: Path) -> List[Path]:
    """
    삭제 후보를 탐색합니다:
    - __pycache__ 디렉터리
    - *.pyc / *.pyo 파일
    (단, EXCLUDED_DIR_NAMES에 포함된 경로는 제외)
    """
    candidates: List[Path] = []

    for p in project_root.rglob("*"):
        # 경로 중에 제외할 폴더 이름이 하나라도 포함되어 있으면 건너뜁니다.
        if any(part in EXCLUDED_DIR_NAMES for part in p.parts):
            continue

        # __pycache__ 폴더 포착
        if p.is_dir() and p.name == "__pycache__":
            candidates.append(p)
            continue

        # 컴파일된 파이썬 파일 포착
        if p.is_file() and p.suffix in {".pyc", ".pyo"}:
            candidates.append(p)

    return candidates

def execute_cleanup(candidates: List[Path]) -> int:
    """
    전달받은 후보 목록을 루프 돌며 실제로 디스크에서 삭제합니다.
    - 삭제에 성공한 항목의 개수를 반환합니다.
    """
    count = 0
    for p in candidates:
        if not p.exists():
            continue
        try:
            if p.is_dir():
                shutil.rmtree(p) # 폴더와 그 내부를 모두 삭제
            else:
                p.unlink()       # 단일 파일 삭제
            count += 1
        except Exception as e:
            print(f"   ! Error deleting {p}: {e}")
    return count