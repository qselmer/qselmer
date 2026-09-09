#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "render_profile.py"
SELF = ROOT / "scripts" / "_fix_profile_note_idempotence.py"
WORKFLOW = ROOT / ".github" / "workflows" / "fix-profile-note-idempotence.yml"

text = TARGET.read_text(encoding="utf-8")
needle = '''    # Remove the repository cards from their legacy top-of-profile position.\n    text = re.sub(\n'''
replacement = '''    # Remove any previously rendered scope note before rebuilding the card block.\n    text = text.replace(PORTFOLIO_NOTE, "")\n\n    # Remove the repository cards from their legacy top-of-profile position.\n    text = re.sub(\n'''
if needle not in text:
    raise RuntimeError("Could not locate portfolio-card refinement block")
text = text.replace(needle, replacement, 1)
TARGET.write_text(text, encoding="utf-8")

if WORKFLOW.exists():
    WORKFLOW.unlink()
if SELF.exists():
    SELF.unlink()
