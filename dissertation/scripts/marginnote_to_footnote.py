#!/usr/bin/env python3
"""Convert all \marginnote[offset]{text} -> \footnote{text} in chapter files."""
import os, re

chapdir = r'c:/Users/babaj/Documents/GitHub/kaobook/dissertation/chapters'

# Match \marginnote optionally followed by [offset] then {content}
# The content may span lines and contain nested braces
def replace_marginnote(content):
    result = []
    i = 0
    count = 0
    while i < len(content):
        if content[i:i+11] == r'\marginnote':
            j = i + 11
            # Skip optional [offset] argument
            if j < len(content) and content[j] == '[':
                depth = 1
                j += 1
                while j < len(content) and depth > 0:
                    if content[j] == '[': depth += 1
                    elif content[j] == ']': depth -= 1
                    j += 1
            # Skip whitespace
            while j < len(content) and content[j] in ' \t\n':
                j += 1
            # Now expect {content}
            if j < len(content) and content[j] == '{':
                # Find matching closing brace
                depth = 1
                k = j + 1
                while k < len(content) and depth > 0:
                    if content[k] == '{': depth += 1
                    elif content[k] == '}': depth -= 1
                    k += 1
                inner = content[j+1:k-1]
                # Strip \footnotesize if it's the first token
                inner = re.sub(r'^\\footnotesize\s*', '', inner)
                result.append(r'\footnote{' + inner + '}')
                i = k
                count += 1
                continue
        result.append(content[i])
        i += 1
    return ''.join(result), count

total = 0
for fname in sorted(os.listdir(chapdir)):
    if not fname.endswith('.tex'):
        continue
    path = os.path.join(chapdir, fname)
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    if r'\marginnote' not in content:
        continue
    new_content, count = replace_marginnote(content)
    with open(path, 'w', encoding='utf-8', errors='replace') as f:
        f.write(new_content)
    print(f'{fname}: {count} converted')
    total += count

print(f'\nTotal: {total} marginnotes converted to footnotes')
