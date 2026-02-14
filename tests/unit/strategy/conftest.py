"""Strategy test conftest — engines 패키지의 heavy __init__.py 우회.

engines/__init__.py가 PortfolioEngine → gspread 체인을 트리거하므로,
가벼운 모듈(scalp_engine, swing_engine)만 import할 때는 빈 패키지로 대체.
"""
import sys
import types
from pathlib import Path

_engines_pkg_key = "src.strategy.engines"

if _engines_pkg_key not in sys.modules:
    _pkg = types.ModuleType(_engines_pkg_key)
    _pkg.__path__ = [str(Path(__file__).resolve().parents[3] / "src" / "strategy" / "engines")]
    _pkg.__package__ = _engines_pkg_key
    sys.modules[_engines_pkg_key] = _pkg
