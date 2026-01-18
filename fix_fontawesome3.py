#!/usr/bin/env python3
"""Fix fontawesome5 icon commands to use correct FA5 naming."""
import re
from pathlib import Path

# Mapping from my bad CamelCase to correct fontawesome5 commands
# Format: wrong_name -> correct_command
icon_mapping = {
    # -alt icons use * suffix
    r'\\faFileAlt': r'\\faFile*',
    r'\\faShareAlt': r'\\faShare*',
    r'\\faExchangeAlt': r'\\faExchange*',
    r'\\faLongArrowAltRight': r'\\faLongArrowRight*',
    # Compound names
    r'\\faChartPie': r'\\faChartPie',
    r'\\faChartBar': r'\\faChartBar',
    r'\\faChartLine': r'\\faChartLine',
    r'\\faEyeSlash': r'\\faEyeSlash',
    r'\\faQuestionCircle': r'\\faQuestionCircle',
    r'\\faCheckCircle': r'\\faCheckCircle',
    r'\\faExclamationTriangle': r'\\faExclamationTriangle',
    r'\\faArrowRight': r'\\faArrowRight',
    r'\\faMapMarkedAlt': r'\\faMapMarked*',
    r'\\faGlobeAmericas': r'\\faGlobeAmericas',
    r'\\faBalanceScale': r'\\faBalanceScale',
    r'\\faProjectDiagram': r'\\faProjectDiagram',
    r'\\faTheaterMasks': r'\\faTheaterMasks',
    r'\\faLaptopMedical': r'\\faLaptopMedical',
    r'\\faCarSide': r'\\faCarSide',
    r'\\faLayerGroup': r'\\faLayerGroup',
    r'\\faMapSigns': r'\\faMapSigns',
    r'\\faPuzzlePiece': r'\\faPuzzlePiece',
    r'\\faHandshake': r'\\faHandshake',
    r'\\faGraduationCap': r'\\faGraduationCap',
    r'\\faUsersCog': r'\\faUsersCog',
    r'\\faBookOpen': r'\\faBookOpen',
    r'\\faDotCircle': r'\\faDotCircle',
}

def fix_icons(content):
    """Apply all icon mappings."""
    for wrong, correct in icon_mapping.items():
        content = re.sub(wrong + r'(?![a-zA-Z*])', correct, content)
    return content

# Process all .tex files in chapters directory
chapters_dir = Path('dissertation/chapters')
for tex_file in chapters_dir.glob('*.tex'):
    if '.backup' not in str(tex_file):
        content = tex_file.read_text(encoding='utf-8')
        new_content = fix_icons(content)
        if content != new_content:
            tex_file.write_text(new_content, encoding='utf-8')
            print(f'Updated: {tex_file}')

# Also process intermezzos
intermezzos_dir = Path('dissertation/intermezzos')
for tex_file in intermezzos_dir.glob('*.tex'):
    content = tex_file.read_text(encoding='utf-8')
    new_content = fix_icons(content)
    if content != new_content:
        tex_file.write_text(new_content, encoding='utf-8')
        print(f'Updated: {tex_file}')

print("Done!")
