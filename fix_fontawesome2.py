#!/usr/bin/env python3
"""Revert faIcon{} back to direct fa commands for fontawesome5 compatibility."""
import re
from pathlib import Path

def kebab_to_camel(name):
    """Convert kebab-case to CamelCase."""
    parts = name.split('-')
    return ''.join(p.capitalize() for p in parts)

# Pattern to match \faIcon{icon-name}
pattern = re.compile(r'\\faIcon\{([a-z-]+)\}')

def replace_icon(match):
    icon_name = match.group(1)
    camel_name = kebab_to_camel(icon_name)
    return f'\\fa{camel_name}'

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
