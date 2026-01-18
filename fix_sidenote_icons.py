#!/usr/bin/env python3
"""
Remove fontawesome icons from sidenotes and marginnotes to fix TeX capacity exceeded errors.
Icons in sidenotes cause stack overflow due to macro expansion in fragile contexts.
"""

import re
import os
from pathlib import Path

def remove_icons_from_sidenotes(content):
    """Remove \faXxx commands from within \sidenote{} and \marginnote{} contexts."""

    # Pattern to match sidenote or marginnote with content
    # We need to find the content within these commands and remove icons from it

    def process_note(match):
        prefix = match.group(1)  # \sidenote{ or \marginnote{
        content = match.group(2)

        # Remove fontawesome commands: \faIconName, \faIconName*, \faIcon{name}, \faIconName[style]
        # Pattern 1: \faIconName\ (with trailing backslash-space)
        content = re.sub(r'\\fa[A-Za-z]+\*?(?:\[[^\]]*\])?\\?\s*', '', content)

        return prefix + content

    # Match \sidenote{ or \marginnote{ followed by content up to balanced }
    # This is tricky because content can have nested braces
    # Simple approach: find these commands and process line by line

    lines = content.split('\n')
    result_lines = []

    for line in lines:
        # Check if line has sidenote or marginnote with fontawesome icon
        if ('\\sidenote{' in line or '\\marginnote{' in line) and '\\fa' in line:
            # Remove icons from within sidenote/marginnote
            # Pattern: \faIconName\ or \faIconName* or \faIconName[style]\
            line = re.sub(r'(\\(?:sidenote|marginnote)\{[^}]*?)\\fa[A-Za-z]+\*?(?:\[[^\]]*\])?\\?\s*', r'\1', line)
            # May need multiple passes for multiple icons in same sidenote
            while '\\fa' in line and ('\\sidenote{' in line or '\\marginnote{' in line):
                old_line = line
                line = re.sub(r'(\\(?:sidenote|marginnote)\{[^}]*?)\\fa[A-Za-z]+\*?(?:\[[^\]]*\])?\\?\s*', r'\1', line)
                if line == old_line:
                    break

        result_lines.append(line)

    return '\n'.join(result_lines)


def process_file(filepath):
    """Process a single .tex file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    content = remove_icons_from_sidenotes(content)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Modified: {filepath}")
        return True
    return False


def main():
    base_path = Path(r'c:\Users\babaj\Documents\GitHub\kaobook\dissertation')

    # Process chapters
    chapters_path = base_path / 'chapters'
    for tex_file in chapters_path.glob('*.tex'):
        if not tex_file.name.endswith('.backup'):
            process_file(tex_file)

    # Process intermezzos
    intermezzos_path = base_path / 'intermezzos'
    for tex_file in intermezzos_path.glob('*.tex'):
        process_file(tex_file)

    print("Done!")


if __name__ == '__main__':
    main()
