"""Extract dataset files and download links from window.INITIAL_STATE."""
import json
import re
from pathlib import Path

for name in ["tomato", "wheat_a", "wheat_c", "cotton_a", "cotton_b"]:
    html_file = Path(f"scripts/{name}_page.html")
    if not html_file.exists():
        continue
    content = html_file.read_text(encoding="utf-8", errors="ignore")
    
    match = re.search(r'window\.INITIAL_STATE\s*=\s*({.*?});</script>', content, re.DOTALL)
    if not match:
        print(f"[{name}] INITIAL_STATE not found")
        continue
        
    state = json.loads(match.group(1))
    dataset = state.get("dataset", {}).get("data", {})
    files = dataset.get("files", [])
    print(f"\n[{name}] Title: {dataset.get('name')}")
    print(f"[{name}] DOI: {dataset.get('doi', {}).get('id')}")
    print(f"[{name}] Files count: {len(files)}")
    
    for f in files:
        file_id = f.get("id")
        file_name = f.get("name")
        file_size = f.get("size")
        download_url = f.get("download_url") or f.get("downloadUrl")
        # Mendeley direct download URL format
        direct_url = f"https://data.mendeley.com/public-files/datasets/{dataset.get('id')}/files/{file_id}/file_downloaded"
        print(f"  - File: {file_name} ({file_size} bytes)")
        print(f"    Direct URL: {direct_url}")
        if download_url:
            print(f"    Download URL: {download_url}")
