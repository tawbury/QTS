#!/usr/bin/env python3
"""
Legacy main.py wrapper for backward compatibility.

This file is deprecated. Please use the new entrypoint:
    python -m src.runtime.main

This wrapper simply delegates to src.runtime.main for backward compatibility.
"""

import sys
import warnings

# Show deprecation warning
warnings.warn(
    "main.py is deprecated. Please use 'python -m src.runtime.main' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Import and run the new entrypoint
from src.runtime.main import main

if __name__ == "__main__":
    sys.exit(main())
