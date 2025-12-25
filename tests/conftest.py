# QTS/tests/conftest.py

import sys
from pathlib import Path

# Add src/ to PYTHONPATH for tests
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
