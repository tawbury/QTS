import json
from pathlib import Path

# ------------------------------------------------------------
# Project root resolution (tests/e2e 기준)
# ------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = PROJECT_ROOT / "data" / "observer" / "observer_test.jsonl"


def main():
    print("project_root:", PROJECT_ROOT)
    print("data_file:", DATA_FILE)

    assert DATA_FILE.exists(), f"NOT FOUND: {DATA_FILE}"

    versions = set()

    with DATA_FILE.open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            md = r.get("metadata", {})
            ver = md.get("_schema", {}).get("record_schema_version", "v1.0.0")
            versions.add(ver)

    print("Detected schema versions:", versions)

    assert "v1.0.0" in versions, "Missing v1.0.0 records"
    assert "v1.1.0" in versions, "Missing v1.1.0 records"

    print("[PASS] Phase 3 / Phase 4 schema coexistence confirmed")


if __name__ == "__main__":
    main()
