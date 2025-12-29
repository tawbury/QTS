# tools/structure_clean/backup.py
from __future__ import annotations

from pathlib import Path
from typing import Iterable
import zipfile


def backup_candidates(
    *,
    project_root: Path,
    candidates: Iterable[Path],
    out_dir: Path,
) -> Path:
    """
    삭제 후보를 zip 파일로 백업한다.

    정책:
    - 항상 동일한 파일명으로 덮어쓰기
    - 구조 유지 (project_root 기준 상대 경로)
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / "cleanup_backup.zip"

    with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in candidates:
            try:
                arcname = p.relative_to(project_root)
            except ValueError:
                continue

            if p.is_dir():
                # 디렉터리는 엔트리만 추가 (구조 보존)
                zf.writestr(str(arcname) + "/", "")
            else:
                zf.write(p, arcname=str(arcname))

    return zip_path
