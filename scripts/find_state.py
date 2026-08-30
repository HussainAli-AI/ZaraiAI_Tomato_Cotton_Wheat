"""Find exact INITIAL_STATE format in tomato_page.html."""
from pathlib import Path
import re

content = Path("scripts/tomato_page.html").read_text(encoding="utf-8", errors="ignore")
idx = content.find("window.INITIAL_STATE")
print("Index:", idx)
if idx != -1:
    snippet = content[idx:idx+1000]
    print("Snippet:")
    print(snippet)
