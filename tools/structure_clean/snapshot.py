# tools/structure_clean/snapshot.py
from __future__ import annotations

from pathlib import Path
from datetime import datetime
from typing import Iterable, Tuple

from .tree_renderer import render_tree


def tree_reports(
    *,
    project_root: Path,
    paths: Iterable[Path],
    out_dir: Path,
) -> Tuple[Path, Path]:
    """
    구조 리포트 생성
    - tree_report.txt        : 최신 상태
    - tree_YYYYMMDD_HHMMSS.txt : 히스토리 로그
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    lines = render_tree(project_root=project_root, paths=paths)
    content = "\n".join(lines)

    latest = out_dir / "tree_report.txt"
    latest.write_text(content, encoding="utf-8")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    history = out_dir / f"tree_{ts}.txt"
    history.write_text(content, encoding="utf-8")

    return latest, history
