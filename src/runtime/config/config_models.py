from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class ConfigScope(str, Enum):
    """
    Config scope identifier.
    
    - LOCAL: Config_Local (file-based, immutable, protected)
    - SCALP: Config_Scalp (Google Sheet)
    - SWING: Config_Swing (Google Sheet)
    """
    LOCAL = "LOCAL"
    SCALP = "SCALP"
    SWING = "SWING"


@dataclass(frozen=True)
class ConfigEntry:
    """
    Single config entry (row).
    
    Matches the finalized config structure:
    - category
    - subcategory
    - key
    - value
    - description
    - tag
    """
    category: str
    subcategory: str
    key: str
    value: str
    description: str = ""
    tag: str = ""


@dataclass(frozen=True)
class ConfigLoadResult:
    """
    Result of loading config from a single source.
    
    Similar to SchemaLoadResult pattern.
    """
    ok: bool
    scope: ConfigScope
    entries: List[ConfigEntry]
    error: Optional[str] = None
    source_path: Optional[str] = None


@dataclass(frozen=True)
class ConfigMergeResult:
    """
    Result of merging Config_Local with strategy config.
    
    Tracks merge metadata for diagnostics.
    """
    ok: bool
    unified_config: Optional[UnifiedConfig] = None
    error: Optional[str] = None
    conflicts: List[str] = None  # Keys where Local overrode Strategy


@dataclass(frozen=True)
class UnifiedConfig:
    """
    Unified config object passed to engines.
    
    Engines are source-agnostic - they only receive this object.
    
    Internal structure:
    - config_map: Dict[str, str] mapping "category.subcategory.key" -> "value"
    - metadata: Dict tracking which scope provided each key
    """
    config_map: Dict[str, str]
    metadata: Dict[str, Any]
    
    def get(self, category: str, subcategory: str, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieve config value by category/subcategory/key.
        
        Returns default if not found.
        """
        lookup_key = f"{category}.{subcategory}.{key}"
        return self.config_map.get(lookup_key, default)

    def get_flat(self, key: str, default: Any = None) -> Any:
        """
        Single-key lookup for engine use (e.g. BASE_EQUITY, KILLSWITCH_STATUS).
        config_map may use flat keys; returns default when key is missing.
        """
        if key not in self.config_map:
            return default
        return self.config_map[key]

    def get_all_in_category(self, category: str) -> Dict[str, str]:
        """
        Retrieve all config entries in a category.
        
        Returns dict mapping "subcategory.key" -> "value"
        """
        prefix = f"{category}."
        return {
            k[len(prefix):]: v
            for k, v in self.config_map.items()
            if k.startswith(prefix)
        }
