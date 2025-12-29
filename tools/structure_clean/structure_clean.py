# 명령어 : python -m tools.structure_clean.structure_clean
# tools/structure_clean/structure_clean.py
from __future__ import annotations
from pathlib import Path

from .scanner import scan_full_tree
from .cleanup import find_cleanup_candidates, execute_cleanup
from .snapshot import tree_reports
from .backup import backup_candidates

def _ask_yes_no(msg: str) -> bool:
    while True:
        ans = input(f"{msg} (y/n): ").strip().lower()
        if ans in {"y", "n"}:
            return ans == "y"

def main() -> None:
    project_root = Path.cwd()
    tool_dir = Path(__file__).resolve().parent
    report_dir = tool_dir / "reports"

    # [1] 전체 스캔
    print("[1] Scanning full project structure...")
    paths = scan_full_tree(project_root=project_root)

    # [2] 삭제 후보 검출 및 필터링 출력
    print("[2] Detecting cleanup candidates...")
    candidates = find_cleanup_candidates(project_root=project_root)

    if candidates:
        # 캐시 파일과 그 외 파일을 분리
        caches = [c for c in candidates if c.name == "__pycache__" or c.suffix in {".pyc", ".pyo"}]
        others = [c for c in candidates if c not in caches]

        print(f" - Found {len(candidates)} items to clean.")
        print(f"   - Python compiled caches: {len(caches)} items (Hidden from list)")

        if others:
            print(f"   - Other unexpected items ({len(others)}):")
            for o in others:
                # [수정 완료] 'o' 변수명을 추가했습니다.
                print(f"     ! {o.relative_to(project_root)}")
        else:
            print("   - No other suspicious files detected. All items are standard caches.")
    else:
        print(" - No cleanup candidates found.")
        return

    # [3] 백업 실행
    print("\n[3] Backup cleanup candidates?")
    if _ask_yes_no("Do you want to create a backup ZIP file?"):
        print(" - Creating backup...")
        zip_path = backup_candidates(
            project_root=project_root,
            candidates=candidates,
            out_dir=report_dir
        )
        print(f" - SUCCESS: Backup created at {zip_path.relative_to(project_root)}")
    else:
        print(" - Skipping backup.")

    # [4] 실제 삭제 실행
    print("\n[4] Delete cleanup candidates?")
    if _ask_yes_no("Proceed with ACTUAL DELETION of all listed items?"):
        print(" - Status: Starting deletion...")
        deleted_count = execute_cleanup(candidates)
        print(f" - SUCCESS: {deleted_count} items have been deleted from disk.")
    else:
        print(" - Deletion cancelled.")

    # [5] 구조 리포트 생성
    print("\n[5] Generate structure tree reports?")
    if _ask_yes_no("Generate tree_report.txt?"):
        latest, history = tree_reports(
            project_root=project_root,
            paths=paths,
            out_dir=report_dir
        )
        print(f" - Reports generated in {report_dir.relative_to(project_root)}")

if __name__ == "__main__":
    main()