import json

with open("observer_test.jsonl") as f:
    for line in f:
        r = json.loads(line)
        md = r["metadata"]
        schema_ver = md.get("_schema", {}).get("record_schema_version", "v1.0.0")
        print(schema_ver)
