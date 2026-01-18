#!/usr/bin/env python3
"""Fix fontawesome5 icon commands for LuaLaTeX compatibility.

Converts \faIconName\ to \faIcon{icon-name}\ format.
"""
import re
from pathlib import Path

def camel_to_kebab(name):
    """Convert CamelCase to kebab-case."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()

# Pattern to match \faIconName followed by backslash or space
# This matches things like \faCheck\ or \faCheck
pattern = re.compile(r'\\fa([A-Z][a-zA-Z]+)(\\\\|\\ )')

def replace_icon(match):
    icon_name = match.group(1)
    suffix = match.group(2)
    kebab_name = camel_to_kebab(icon_name)
    return f'\\faIcon{{{kebab_name}}}{suffix}'

# Process all .tex files in chapters directory
chapters_dir = Path('dissertation/chapters')
for tex_file in chapters_dir.glob('*.tex'):
    if '.backup' not in str(tex_file):
        content = tex_file.read_text(encoding='utf-8')
        new_content = pattern.sub(replace_icon, content)
        if content != new_content:
            tex_file.write_text(new_content, encoding='utf-8')
            print(f'Updated: {tex_file}')

# Also process intermezzos
intermezzos_dir = Path('dissertation/intermezzos')
for tex_file in intermezzos_dir.glob('*.tex'):
    content = tex_file.read_text(encoding='utf-8')
    new_content = pattern.sub(replace_icon, content)
    if content != new_content:
        tex_file.write_text(new_content, encoding='utf-8')
        print(f'Updated: {tex_file}')

print("Done!")
