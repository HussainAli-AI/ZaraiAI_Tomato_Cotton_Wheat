"""Inspect downloaded HTML to locate file download references without bs4."""
import re
from pathlib import Path

content = Path("scripts/tomato_page.html").read_text(encoding="utf-8", errors="ignore")
print("Total characters:", len(content))

# Look for links
for link in re.findall(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', content):
    if "download" in link[0].lower() or "file" in link[0].lower() or "zip" in link[0].lower() or "download" in link[1].lower():
        print("Link:", link)

# Look for script blocks
for script in re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL):
    if "3mbnb82mxd" in script or "files" in script or "download" in script or "json" in script:
        # print snippet
        if len(script.strip()) > 0:
            print("Script snippet:", script[:300].strip())
            print("===")
