#!/usr/bin/env python3
"""Fix pagelayout insertions: remove duplicate margins, fix J file."""
import os, re

appdir = r'c:/Users/babaj/Documents/GitHub/kaobook/dissertation/appendices'

for fname in sorted(os.listdir(appdir)):
    if not fname.endswith('.tex'):
        continue
    path = os.path.join(appdir, fname)
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    changed = False

    # Fix duplicate \pagelayout{margin}\n\pagelayout{margin} -> single
    new = re.sub(
        r'(\\pagelayout\{margin\}\n)+\\pagelayout\{margin\}',
        r'\\pagelayout{margin}',
        content
    )
    if new != content:
        content = new
        changed = True
        print(f'dedup margin: {fname}')

    # Fix J: no \begin{document} — insert wide before \chapter
    if r'\pagelayout{wide}' not in content:
        content = content.replace(
            r'\chapter{',
            r'\pagelayout{wide}' + '\n' + r'\chapter{',
            1
        )
        changed = True
        print(f'added wide: {fname}')

    if r'\pagelayout{margin}' not in content:
        content = content.replace(
            r'\end{document}',
            r'\pagelayout{margin}' + '\n' + r'\end{document}',
            1
        )
        changed = True
        print(f'added margin: {fname}')

    if changed:
        with open(path, 'w', encoding='utf-8', errors='replace') as f:
            f.write(content)

print('done.')
