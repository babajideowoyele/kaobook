#!/usr/bin/env python3
"""Add \pagelayout{wide} to all appendix files."""
import os

appdir = r'c:/Users/babaj/Documents/GitHub/kaobook/dissertation/appendices'

for fname in sorted(os.listdir(appdir)):
    if not fname.endswith('.tex'):
        continue
    path = os.path.join(appdir, fname)
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception as e:
        print(f'ERROR reading {fname}: {e}')
        continue

    if r'\pagelayout{wide}' in content:
        print(f'skip (already done): {fname}')
        continue

    content = content.replace(
        r'\begin{document}',
        r'\begin{document}' + '\n' + r'\pagelayout{wide}',
        1
    )
    content = content.replace(
        r'\end{document}',
        r'\pagelayout{margin}' + '\n' + r'\end{document}',
        1
    )

    with open(path, 'w', encoding='utf-8', errors='replace') as f:
        f.write(content)
    print(f'done: {fname}')
