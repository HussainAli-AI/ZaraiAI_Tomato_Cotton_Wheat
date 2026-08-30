"""Inspect files list and folders in INITIAL_STATE."""
import json
from pathlib import Path

for name in ["tomato", "wheat_a", "wheat_c", "cotton_a", "cotton_b"]:
    content = Path(f"scripts/{name}_page.html").read_text(encoding="utf-8", errors="ignore")
    start = content.find("window.INITIAL_STATE = ") + len("window.INITIAL_STATE = ")
    end = content.find(";</script>", start)
    if end == -1: end = content.find("\n", start)
    data = json.loads(content[start:end].strip())
    
    files_list = data.get("files", {}).get("list", [])
    folders = data.get("files", {}).get("folders", [])
    s3_base = data.get("s3")
    dataset_id = data.get("dataset", {}).get("snapshot", {}).get("id")
    version = data.get("dataset", {}).get("snapshot", {}).get("version")
    
    print(f"\n==================== {name.upper()} ({dataset_id} v{version}) ====================")
    print(f"S3 Base: {s3_base}")
    print(f"Folders count: {len(folders)}")
    for fld in folders[:10]:
        print(f"  Folder: {fld.get('name')} (id: {fld.get('id')})")
    print(f"Files count: {len(files_list)}")
    for f in files_list[:15]:
        fid = f.get("id")
        fname = f.get("name")
        fsize = f.get("size", 0)
        # Mendeley direct download URL
        dl_url = f"https://data.mendeley.com/public-files/datasets/{dataset_id}/files/{fid}/file_downloaded"
        print(f"  File: {fname} | Size: {fsize/1024/1024:.2f} MB | ID: {fid}")
        print(f"    Direct DL: {dl_url}")
