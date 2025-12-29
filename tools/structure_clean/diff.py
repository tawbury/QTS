# tools/structure_clean/diff.py
from __future__ import annotations

from pathlib import Path
from typing import Tuple


def diff_tree_reports(
    *,
    before: Path,
    after: Path,
) -> Tuple[int, int]:
    """
    두 트리 리포트를 비교한다.

    Returns
    -------
    (removed_count, added_count)
    """
    if not before.exists():
        # 이전 기준 파일이 없으면 전부 신규로 간주
        after_lines = set(after.read_text(encoding="utf-8").splitlines())
        return 0, len(after_lines)

    before_lines = set(before.read_text(encoding="utf-8").splitlines())
    after_lines = set(after.read_text(encoding="utf-8").splitlines())

    removed = before_lines - after_lines
    added = after_lines - before_lines

    return len(removed), len(added)
