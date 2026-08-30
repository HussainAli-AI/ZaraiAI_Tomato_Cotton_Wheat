"""Accurately extract files, sizes, DOIs, and download links for all datasets."""
import json
from pathlib import Path

for name in ["tomato", "wheat_a", "wheat_c", "cotton_a", "cotton_b"]:
    html_file = Path(f"scripts/{name}_page.html")
    if not html_file.exists():
        continue
    content = html_file.read_text(encoding="utf-8", errors="ignore")
    idx = content.find("window.INITIAL_STATE = ")
    if idx == -1:
        print(f"[{name}] INITIAL_STATE not found")
        continue
    
    start = idx + len("window.INITIAL_STATE = ")
    end = content.find(";</script>", start)
    if end == -1:
        end = content.find("\n", start)
        
    json_str = content[start:end].strip()
    try:
        data = json.loads(json_str)
        snapshot = data.get("dataset", {}).get("snapshot", {})
        files = snapshot.get("files", [])
        print(f"\n=======================================================")
        print(f"Dataset: {name.upper()}")
        print(f"Title: {snapshot.get('name')}")
        print(f"DOI: {snapshot.get('doi', {}).get('id') if isinstance(snapshot.get('doi'), dict) else snapshot.get('doi')}")
        print(f"License: {snapshot.get('licence', {}).get('name') if isinstance(snapshot.get('licence'), dict) else snapshot.get('licence')}")
        print(f"Categories / Topics: {snapshot.get('categories')}")
        print(f"Total Files in Repository: {len(files)}")
        for f in files:
            file_id = f.get("id")
            fname = f.get("name")
            fsize = f.get("size")
            download_url = f.get("downloadUrl") or f"https://data.mendeley.com/public-files/datasets/{snapshot.get('id')}/files/{file_id}/file_downloaded"
            print(f"  * File: {fname} | Size: {fsize/1024/1024:.2f} MB | ID: {file_id}")
            print(f"    Download: {download_url}")
    except Exception as e:
        print(f"[{name}] JSON error: {e}")
