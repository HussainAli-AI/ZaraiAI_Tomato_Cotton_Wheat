"""Inspect snapshot keys and structure."""
import json
from pathlib import Path

content = Path("scripts/tomato_page.html").read_text(encoding="utf-8", errors="ignore")
start = content.find("window.INITIAL_STATE = ") + len("window.INITIAL_STATE = ")
end = content.find(";</script>", start)
if end == -1: end = content.find("\n", start)
data = json.loads(content[start:end].strip())
snapshot = data.get("dataset", {}).get("snapshot", {})
print("Snapshot keys:", list(snapshot.keys()))
for k, v in snapshot.items():
    if isinstance(v, (list, dict)):
        print(f"  {k}: type={type(v)}, len={len(v)}")
    else:
        print(f"  {k}: {v}")
