# tools/structure_clean/tree_renderer.py
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Dict, List


class _TreeNode:
    def __init__(self, name: str, is_dir: bool) -> None:
        self.name = name
        self.is_dir = is_dir
        self.children: Dict[str, "_TreeNode"] = {}


def render_tree(
    *,
    project_root: Path,
    paths: Iterable[Path],
) -> List[str]:
    """
    필터링이 끝난 Path 집합을
    ASCII 트리로 표현만 한다.
    """
    root = _TreeNode("Root", True)

    for p in paths:
        rel = p.relative_to(project_root)
        current = root

        for i, part in enumerate(rel.parts):
            is_last = i == len(rel.parts) - 1
            is_dir = p.is_dir() or not is_last

            if part not in current.children:
                current.children[part] = _TreeNode(part, is_dir)

            current = current.children[part]

    lines: List[str] = ["Root/"]

    def _walk(node: _TreeNode, prefix: str) -> None:
        children = sorted(
            node.children.values(),
            key=lambda n: (not n.is_dir, n.name),
        )
        for idx, child in enumerate(children):
            connector = "└─ " if idx == len(children) - 1 else "├─ "
            lines.append(f"{prefix}{connector}{child.name}{'/' if child.is_dir else ''}")
            _walk(child, prefix + ("   " if idx == len(children) - 1 else "│  "))

    _walk(root, "")
    return lines
