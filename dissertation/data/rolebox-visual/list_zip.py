#!/usr/bin/env python
"""List contents of screenshots zip"""

import zipfile
from pathlib import Path

zip_path = Path(__file__).parent / "data" / "raw" / "eit_screenshots.zip"

print(f"Opening: {zip_path}")
print(f"Size: {zip_path.stat().st_size / 1024 / 1024:.1f} MB")
print()

with zipfile.ZipFile(zip_path, 'r') as zf:
    entries = zf.namelist()
    print(f"Total files: {len(entries)}")
    print()

    # Count by directory
    dirs = {}
    for e in entries:
        parts = e.split('/')
        if len(parts) > 1:
            d = parts[0]
            dirs[d] = dirs.get(d, 0) + 1

    print("Files by directory:")
    for d, count in sorted(dirs.items(), key=lambda x: -x[1]):
        print(f"  {d}: {count}")

    print()
    print("Sample files:")
    for e in entries[:20]:
        info = zf.getinfo(e)
        print(f"  {e} ({info.file_size / 1024:.1f} KB)")
