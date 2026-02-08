import os
import json
import time
import pytest
from pathlib import Path

def test_observer_data_access():
    """
    Verify that QTS container can access Observer's generated data.
    """
    # 1. Get the mounted directory from env
    assets_dir_str = os.environ.get("OBSERVER_ASSETS_DIR")
    if not assets_dir_str:
        pytest.skip("OBSERVER_ASSETS_DIR not set. Skipping integration test.")
    
    assets_dir = Path(assets_dir_str)
    print(f"Checking assets directory: {assets_dir}")

    # 2. Wait for data to appear (Observer container needs time to generate)
    timeout = 30
    start_time = time.time()
    found_files = []

    print("Waiting for observer data files...")
    while time.time() - start_time < timeout:
        # Check recursively for jsonl files
        found_files = list(assets_dir.rglob("*.jsonl"))
        if found_files:
            break
        time.sleep(1)
    
    if not found_files:
        pytest.fail(f"Timeout waiting for .jsonl files in {assets_dir} after {timeout} seconds.")
    
    print(f"Found {len(found_files)} files: {[f.name for f in found_files]}")

    # 3. Verify content of at least one file
    target_file = found_files[0]
    print(f"Verifying content of {target_file}...")
    
    count = 0
    with open(target_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                assert "symbol" in data, "Missing 'symbol' field in JSONL"
                count += 1
            except json.JSONDecodeError:
                pytest.fail(f"Invalid JSON in {target_file}: {line[:50]}...")
    
    assert count > 0, f"File {target_file} is empty or invalid."
    print(f"Successfully read {count} lines from {target_file}.")
