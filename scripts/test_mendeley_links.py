"""Test fetching Mendeley dataset metadata and direct download URLs."""
import requests
import json
import re

DATASETS = {
    "tomato": {"id": "3mbnb82mxd", "version": 2, "doi": "10.17632/3mbnb82mxd.2"},
    "wheat_a": {"id": "5gc7hwydwg", "version": 1, "doi": "10.17632/5gc7hwydwg.1"},
    "wheat_c": {"id": "wgd66f8n6h", "version": 1, "doi": "10.17632/wgd66f8n6h.1"},
    "cotton_a": {"id": "t9hgvk2h9p", "version": 1, "doi": "10.17632/t9hgvk2h9p.1"},
    "cotton_b": {"id": "nmjxz73z6y", "version": 2, "doi": "10.17632/nmjxz73z6y.2"},
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

for name, meta in DATASETS.items():
    url = f"https://data.mendeley.com/datasets/{meta['id']}/{meta['version']}"
    try:
        r = requests.get(url, headers=headers, timeout=15)
        print(f"[{name}] Page Status: {r.status_code}, Length: {len(r.text)}")
        
        # Look for download links in page or S3 zip
        # Common pattern: href="/public-files/datasets/..." or direct s3 zip
        s3_url = f"https://prod-dcd-datasets-cache-zipfiles.s3.eu-west-1.amazonaws.com/{meta['id']}_{meta['version']}.zip"
        s3_res = requests.head(s3_url, headers=headers, timeout=10)
        print(f"[{name}] Direct S3 Zip Status: {s3_res.status_code}, Content-Length: {s3_res.headers.get('Content-Length')}")
        
        # Extract files from JSON embedded in HTML if present
        # Mendeley embeds initialState in window.__INITIAL_STATE__
        match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});</script>', r.text, re.DOTALL)
        if match:
            state_json = match.group(1)
            print(f"[{name}] Found INITIAL_STATE JSON (length {len(state_json)})")
    except Exception as e:
        print(f"[{name}] Error: {e}")
