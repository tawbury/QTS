#!/usr/bin/env python3
"""
Debug paths issue.
"""

import sys
import os

# Add src to path
sys.path.insert(0, 'src')

try:
    from paths import observer_asset_dir, observer_asset_file
    print("✓ paths import successful")
    
    print(f"observer_asset_dir(): {observer_asset_dir()}")
    print(f"observer_asset_file('test.jsonl'): {observer_asset_file('test.jsonl')}")
    print(f"Directory exists: {os.path.exists(observer_asset_dir())}")
    
    # Try to create directory
    if not os.path.exists(observer_asset_dir()):
        os.makedirs(observer_asset_dir(), exist_ok=True)
        print(f"Created directory: {observer_asset_dir()}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
