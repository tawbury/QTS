# QTS/tests/conftest.py

import sys
from pathlib import Path

# --------------------------------------------------
# QTS Project Root Injection (Canonical)
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"

# 프로젝트 루트 (paths.py 등)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# src 패키지
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
