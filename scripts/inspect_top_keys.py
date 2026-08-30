"""Inspect top-level keys in INITIAL_STATE data."""
import json
from pathlib import Path

content = Path("scripts/tomato_page.html").read_text(encoding="utf-8", errors="ignore")
start = content.find("window.INITIAL_STATE = ") + len("window.INITIAL_STATE = ")
end = content.find(";</script>", start)
if end == -1: end = content.find("\n", start)
data = json.loads(content[start:end].strip())
print("Top keys in INITIAL_STATE:", list(data.keys()))
for k, v in data.items():
    print(f"Key: {k}, type={type(v)}")
    if isinstance(v, dict):
        print(f"   subkeys: {list(v.keys())}")
