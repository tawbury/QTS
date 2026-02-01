#!/usr/bin/env python3
"""
Legacy main.py wrapper for backward compatibility.

This file is deprecated. Please use the new entrypoint:
    python -m app.main

This wrapper simply delegates to app.main for backward compatibility.
"""

import sys
import warnings

# Show deprecation warning
warnings.warn(
    "main.py is deprecated. Please use 'python -m app.main' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Import and run the new entrypoint
from app.main import main

if __name__ == "__main__":
    sys.exit(main())
