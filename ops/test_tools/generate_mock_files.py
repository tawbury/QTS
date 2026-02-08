import os
import json
import time
from datetime import datetime
from pathlib import Path

def main():
    # OBSERVER_ASSETS_DIR should be /opt/platform/runtime/qts/data/observer_assets inside container
    assets_dir = os.environ.get("OBSERVER_ASSETS_DIR", "/opt/platform/runtime/qts/data/observer_assets")
    target_dir = Path(assets_dir) / "scalp"
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a unique file name
    file_path = target_dir / f"scalp_{int(time.time())}.jsonl"
    print(f"Generating mock data to {file_path}")
    
    symbols = ["005930", "000660"]
    base_prices = {"005930": 70000, "000660": 120000}
    
    with open(file_path, "w", encoding="utf-8") as f:
        for i in range(20):
            for sym in symbols:
                data = {
                    "symbol": sym,
                    "price": base_prices[sym] + i * 100,
                    "volume": 100 + i,
                    "timestamp": datetime.now().isoformat()
                }
                f.write(json.dumps(data) + "\n")
            print(f"Wrote batch {i+1}")
            time.sleep(0.2)

    print("Done generating data. Sleeping to keep container alive.")
    time.sleep(3600)

if __name__ == "__main__":
    main()
