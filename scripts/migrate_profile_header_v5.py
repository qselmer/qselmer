from pathlib import Path
import re

# Update durable renderer.
p = Path('scripts/render_profile.py')
s = p.read_text(encoding='utf-8')

# Do not render a duplicate personal name in the README; GitHub already shows it in the profile sidebar.
s = s.replace(
    "    if '<h1 align=\"center\">Elmer Quispe-Salazar</h1>' not in text:\n"
    "        text = text.replace(\n"
    "            professional_heading,\n"
    "            '<h1 align=\"center\">Elmer Quispe-Salazar</h1>\\n\\n' + professional_heading,\n"
    "            1,\n"
    "        )\n",
    "    text = text.replace('<h1 align=\"center\">Elmer Quispe-Salazar</h1>\\n\\n', '')\n",
)

old_focus = '''    focus_match = re.search(r'(\\n## Research focus\\n.*?)(?=\\n## |\\Z)', text, flags=re.S)\n    if focus_match:\n        focus_block = focus_match.group(1).rstrip()\n        replacement = focus_block + "\\n\\n" + PORTFOLIO_CARDS + "\\n\\n" + PORTFOLIO_NOTE + "\\n"\n        text = text[:focus_match.start()] + replacement + text[focus_match.end():]\n'''
new_focus = '''    contact_match = re.search(\n        r'\\n(<p align="justify">\\s*For research collaboration or professional contact:.*?</p>)\\n',\n        text,\n        flags=re.S,\n    )\n    contact_block = contact_match.group(1) if contact_match else ""\n    if contact_match:\n        text = text[:contact_match.start()] + "\\n" + text[contact_match.end():]\n\n    focus_match = re.search(r'(\\n## Research focus\\n.*?)(?=\\n## |\\Z)', text, flags=re.S)\n    if focus_match:\n        focus_block = focus_match.group(1).rstrip()\n        replacement = focus_block\n        if contact_block:\n            replacement += "\\n\\n" + contact_block\n        replacement += "\\n\\n" + PORTFOLIO_CARDS + "\\n\\n" + PORTFOLIO_NOTE + "\\n"\n        text = text[:focus_match.start()] + replacement + text[focus_match.end():]\n'''
assert old_focus in s, 'Expected Research focus rendering block not found'
s = s.replace(old_focus, new_focus, 1)
p.write_text(s, encoding='utf-8')

# Update regression tests.
p = Path('tests/test_profile_v2.py')
t = p.read_text(encoding='utf-8')
t = t.replace(
    "    assert '<h1 align=\"center\">Elmer Quispe-Salazar</h1>' in refined\n",
    "    assert '<h1 align=\"center\">Elmer Quispe-Salazar</h1>' not in refined\n",
)
anchor = '    assert refined.index("## Research focus") < refined.index("assets/generated/top-languages.svg")\n'
assert anchor in t, 'Expected ordering assertion not found'
t = t.replace(
    anchor,
    anchor + '    assert refined.index("## Research focus") < refined.index("For research collaboration or professional contact") < refined.index("assets/generated/top-languages.svg")\n',
    1,
)
p.write_text(t, encoding='utf-8')

# Update current README immediately.
p = Path('README.md')
r = p.read_text(encoding='utf-8')
r = r.replace('<h1 align="center">Elmer Quispe-Salazar</h1>\n\n', '', 1)
contact_pattern = re.compile(r'\n(<p align="justify">\s*For research collaboration or professional contact:.*?</p>)\n', re.S)
m = contact_pattern.search(r)
contact = m.group(1) if m else ''
if m:
    r = r[:m.start()] + '\n' + r[m.end():]
if contact:
    focus = re.search(r'(\n## Research focus\n.*?)(?=\n<p align="center">\s*<img src="assets/generated/top-languages\.svg")', r, re.S)
    assert focus, 'Could not locate Research focus before portfolio cards'
    block = focus.group(1).rstrip() + '\n\n' + contact + '\n'
    r = r[:focus.start()] + block + r[focus.end():]
p.write_text(r, encoding='utf-8')
