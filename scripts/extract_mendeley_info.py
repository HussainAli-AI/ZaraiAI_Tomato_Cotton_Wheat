"""Parse Mendeley dataset HTML pages to extract download URLs and metadata."""
import subprocess
import json
import re
from pathlib import Path

DATASETS = {
    "tomato": {"id": "3mbnb82mxd", "version": 2, "url": "https://data.mendeley.com/datasets/3mbnb82mxd/2"},
    "wheat_a": {"id": "5gc7hwydwg", "version": 1, "url": "https://data.mendeley.com/datasets/5gc7hwydwg/1"},
    "wheat_c": {"id": "wgd66f8n6h", "version": 1, "url": "https://data.mendeley.com/datasets/wgd66f8n6h/1"},
    "cotton_a": {"id": "t9hgvk2h9p", "version": 1, "url": "https://data.mendeley.com/datasets/t9hgvk2h9p/1"},
    "cotton_b": {"id": "nmjxz73z6y", "version": 2, "url": "https://data.mendeley.com/datasets/nmjxz73z6y/2"},
}

for name, meta in DATASETS.items():
    print(f"=== Processing {name} ({meta['id']}) ===")
    html_file = Path(f"scripts/{name}_page.html")
    # Fetch with curl
    cmd = ["curl.exe", "-s", "-L", meta["url"], "-o", str(html_file)]
    subprocess.run(cmd, check=True)
    
    content = html_file.read_text(encoding="utf-8", errors="ignore")
    print(f"Downloaded HTML size: {len(content)} bytes")
    
    # 1. Look for public-files links
    public_files = re.findall(r'href="(/public-files/datasets/[^"]+)"', content)
    print(f"Public file links found: {len(public_files)}")
    for pf in public_files[:5]:
        print(f"  https://data.mendeley.com{pf}")
        
    # 2. Look for zip / s3 links
    zips = re.findall(r'https://[^\s"\'<>]+\.zip[^\s"\'<>]*', content)
    print(f"Zip links: {zips}")
    
    # 3. Look for direct download buttons or api links
    downloads = re.findall(r'https://data\.mendeley\.com/public-files/[^\s"\'<>]+', content)
    print(f"Full download links: {downloads[:5]}")
    
    # 4. Check for embedded state
    state_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});</script>', content, re.DOTALL)
    if state_match:
        try:
            state = json.loads(state_match.group(1))
            # navigate to files
            files_obj = state.get("dataset", {}).get("files", [])
            print(f"Files from INITIAL_STATE: {len(files_obj)}")
            for f in files_obj[:5]:
                print(f"  File: {f.get('name')}, Size: {f.get('size')}, DownloadUrl: {f.get('download_url')}")
        except Exception as e:
            print(f"Error parsing INITIAL_STATE JSON: {e}")
