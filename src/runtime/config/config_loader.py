from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from .config_models import (
    ConfigEntry,
    ConfigMergeResult,
    ConfigScope,
    UnifiedConfig,
)
from .local_config import load_local_config
from .sheet_config import load_sheet_config


def load_unified_config(project_root: Path, scope: ConfigScope) -> ConfigMergeResult:
    """
    Load and merge Config_Local with strategy config (Scalp or Swing).

    Unified loading orchestrator for the 3-way config system.
    Merge rules SSOT: docs/arch/13_Config_3분할_Architecture.md (Local immutable).

    Merge / Precedence (Local immutable):
    - Config_Local is protected; strategy sheet MUST NOT override Local keys.
    - Strategy config may only extend (add keys not present in Local).
    - Same key in both: Local value wins, key recorded in conflicts.

    Process:
    1. Load Config_Local from file
    2. Load Config_Scalp or Config_Swing from Sheet (via Repository)
    3. Merge with precedence (Local wins)
    4. Return UnifiedConfig

    Args:
        project_root: Project root path
        scope: ConfigScope.SCALP or ConfigScope.SWING (NOT LOCAL)

    Returns:
        ConfigMergeResult with unified_config or error
    """
    if scope == ConfigScope.LOCAL:
        return ConfigMergeResult(
            ok=False,
            unified_config=None,
            error="Cannot load unified config with scope=LOCAL. Use SCALP or SWING.",
            conflicts=[],
        )
    
    # Step 1: Load Config_Local
    local_result = load_local_config(project_root)
    if not local_result.ok:
        return ConfigMergeResult(
            ok=False,
            unified_config=None,
            error=f"Failed to load Config_Local: {local_result.error}",
            conflicts=[],
        )
    
    # Step 2: Load strategy config (Scalp or Swing)
    strategy_result = load_sheet_config(project_root, scope)
    if not strategy_result.ok:
        return ConfigMergeResult(
            ok=False,
            unified_config=None,
            error=f"Failed to load {scope.value} config: {strategy_result.error}",
            conflicts=[],
        )
    
    # Step 3: Merge with precedence (Local wins)
    config_map, conflicts = _merge_configs(
        local_entries=local_result.entries,
        strategy_entries=strategy_result.entries,
    )
    
    # Step 4: Build metadata
    metadata = {
        "local_source": local_result.source_path,
        "strategy_source": strategy_result.source_path,
        "strategy_scope": scope.value,
        "local_entry_count": len(local_result.entries),
        "strategy_entry_count": len(strategy_result.entries),
        "total_entry_count": len(config_map),
        "conflicts": conflicts,
    }
    
    # Step 5: Produce UnifiedConfig
    unified = UnifiedConfig(
        config_map=config_map,
        metadata=metadata,
    )
    
    return ConfigMergeResult(
        ok=True,
        unified_config=unified,
        error=None,
        conflicts=conflicts,
    )


def load_local_only_config(project_root: Path) -> ConfigMergeResult:
    """
    Load Config_Local only (no strategy config).
    
    Use case: Processes that only need local config (e.g., system utilities).
    
    Args:
        project_root: Project root path
    
    Returns:
        ConfigMergeResult with unified_config or error
    """
    local_result = load_local_config(project_root)
    if not local_result.ok:
        return ConfigMergeResult(
            ok=False,
            unified_config=None,
            error=f"Failed to load Config_Local: {local_result.error}",
            conflicts=[],
        )
    
    config_map = _entries_to_map(local_result.entries)
    
    metadata = {
        "local_source": local_result.source_path,
        "strategy_source": None,
        "strategy_scope": None,
        "local_entry_count": len(local_result.entries),
        "strategy_entry_count": 0,
        "total_entry_count": len(config_map),
        "conflicts": [],
    }
    
    unified = UnifiedConfig(
        config_map=config_map,
        metadata=metadata,
    )
    
    return ConfigMergeResult(
        ok=True,
        unified_config=unified,
        error=None,
        conflicts=[],
    )


def _merge_configs(
    local_entries: List[ConfigEntry],
    strategy_entries: List[ConfigEntry],
) -> tuple[Dict[str, str], List[str]]:
    """
    Merge Config_Local and strategy config. Local immutable (Local wins).

    SSOT: docs/arch/13_Config_3분할_Architecture.md §3.3 충돌 규칙.
    - Local is immutable; strategy must not override Local keys.
    - Conflict: Local value kept, key appended to conflicts.

    Returns:
        (config_map, conflicts)
        - config_map: "category.subcategory.key" -> "value"
        - conflicts: keys where Local overrode Strategy
    """
    config_map: Dict[str, str] = {}
    conflicts: List[str] = []
    
    # Step 1: Add all Local entries (immutable, highest priority)
    local_keys = set()
    for entry in local_entries:
        key = _make_key(entry.category, entry.subcategory, entry.key)
        config_map[key] = entry.value
        local_keys.add(key)
    
    # Step 2: Add Strategy entries (only if not in Local)
    for entry in strategy_entries:
        key = _make_key(entry.category, entry.subcategory, entry.key)
        if key in local_keys:
            # Conflict: Local wins
            conflicts.append(key)
        else:
            # No conflict: add Strategy entry
            config_map[key] = entry.value
    
    return config_map, conflicts


def _entries_to_map(entries: List[ConfigEntry]) -> Dict[str, str]:
    """
    Convert config entries to map.
    
    Args:
        entries: List of ConfigEntry
    
    Returns:
        Dict[str, str] mapping "category.subcategory.key" -> "value"
    """
    config_map: Dict[str, str] = {}
    for entry in entries:
        key = _make_key(entry.category, entry.subcategory, entry.key)
        config_map[key] = entry.value
    return config_map


def _make_key(category: str, subcategory: str, key: str) -> str:
    """
    Create hierarchical config key.
    
    Format: "category.subcategory.key"
    
    Args:
        category: Config category
        subcategory: Config subcategory
        key: Config key
    
    Returns:
        Hierarchical key string
    """
    return f"{category}.{subcategory}.{key}"
