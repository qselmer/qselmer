#!/usr/bin/env python3
from pathlib import Path

renderer = Path("scripts/render_profile.py")
readme = Path("README.md")

text = renderer.read_text(encoding="utf-8")
start = text.index('SCIENTIFIC_COMPUTING_BLOCK = """')
end = text.index('"""\n\nMETRICS_NOTE', start)
block = text[start:end]
if block.count('<p align="center">') != 2:
    raise SystemExit("Expected exactly two centered paragraphs in SCIENTIFIC_COMPUTING_BLOCK")
block = block.replace('<p align="center">', '<p align="left">')
text = text[:start] + block + text[end:]
renderer.write_text(text, encoding="utf-8")

text = readme.read_text(encoding="utf-8")
start = text.index("## Scientific computing\n")
end = text.index("\n## Scientific computing & reproducible research", start)
block = text[start:end]
if block.count('<p align="center">') != 2:
    raise SystemExit("Expected exactly two centered paragraphs in README Scientific computing section")
block = block.replace('<p align="center">', '<p align="left">')
text = text[:start] + block + text[end:]
readme.write_text(text, encoding="utf-8")

print("Scientific computing badges aligned to the left in renderer and README.")
