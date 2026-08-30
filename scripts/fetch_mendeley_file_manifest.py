"""Fetch verified public file metadata and direct download URLs for all candidate datasets."""
import subprocess
import json
from pathlib import Path

DATASETS = [
    {"crop": "tomato", "name": "Tomato Pakistan", "id": "3mbnb82mxd", "version": 2, "doi": "10.17632/3mbnb82mxd.2"},
    {"crop": "wheat", "name": "Wheat Disease Dataset", "id": "5gc7hwydwg", "version": 1, "doi": "10.17632/5gc7hwydwg.1"},
    {"crop": "wheat", "name": "Wheat Leaf Dataset", "id": "wgd66f8n6h", "version": 1, "doi": "10.17632/wgd66f8n6h.1"},
    {"crop": "cotton", "name": "Cotton Leaf Dataset A", "id": "t9hgvk2h9p", "version": 1, "doi": "10.17632/t9hgvk2h9p.1"},
    {"crop": "cotton", "name": "Cotton Sindh Pakistan Dataset B", "id": "nmjxz73z6y", "version": 2, "doi": "10.17632/nmjxz73z6y.2"},
]

results = []

for d in DATASETS:
    url = f"https://data.mendeley.com/public-api/datasets/{d['id']}/files?folder_id=root&version={d['version']}"
    cmd = ["curl.exe", "-s", "-L", url]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode == 0:
        try:
            files_data = json.loads(proc.stdout)
            print(f"\n=======================================================")
            print(f"Crop: {d['crop'].upper()} | {d['name']} | DOI: {d['doi']}")
            print(f"Files found: {len(files_data)}")
            for f in files_data:
                fname = f.get("filename")
                fid = f.get("id")
                size = f.get("size", 0)
                details = f.get("content_details", {})
                sha256 = details.get("sha256_hash")
                dl_url = details.get("download_url") or f"https://data.mendeley.com/public-files/datasets/{d['id']}/files/{fid}/file_downloaded"
                print(f"  * {fname} ({size/1024/1024:.2f} MB)")
                print(f"    SHA256: {sha256}")
                print(f"    URL: {dl_url}")
                results.append({
                    "crop": d["crop"],
                    "dataset_name": d["name"],
                    "dataset_id": d["id"],
                    "version": d["version"],
                    "doi": d["doi"],
                    "filename": fname,
                    "file_id": fid,
                    "size_bytes": size,
                    "sha256": sha256,
                    "download_url": dl_url
                })
        except Exception as e:
            print(f"Error parsing response for {d['name']}: {e}, Raw output: {proc.stdout[:200]}")
    else:
        print(f"Error fetching {d['name']}: {proc.stderr}")

# Save manifest template
Path("data").mkdir(exist_ok=True)
with open("data/mendeley_verified_files.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"\nTotal verified files across datasets: {len(results)}")
