#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Expected exactly one match in {path!r}, found {count}: {old!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    "assets/data/repository-types.json",
    '"type-project": "Projects"',
    '"type-project": "Research projects"',
)
replace_once(
    "scripts/update_profile.py",
    'VISIBLE_TYPE_ORDER = [\n    "Projects",',
    'VISIBLE_TYPE_ORDER = [\n    "Research projects",',
)
replace_once(
    "scripts/render_profile.py",
    'VISIBLE_TYPE_ORDER = [\n    "Projects",',
    'VISIBLE_TYPE_ORDER = [\n    "Research projects",',
)
replace_once(
    "scripts/render_profile.py",
    '        lines += [f"### {label} ({len(group)})", ""]',
    '        lines += [f"### {label}", ""]',
)
replace_once(
    "scripts/render_profile.py",
    '            f"### Archived repositories ({len(archived)})",',
    '            "### Archived repositories",',
)
replace_once(
    "tests/test_project_taxonomy.py",
    'assert config["canonical_types"]["type-project"] == "Projects"',
    'assert config["canonical_types"]["type-project"] == "Research projects"',
)
replace_once(
    "tests/test_project_taxonomy.py",
    'assert update.VISIBLE_TYPE_ORDER[0] == "Projects"',
    'assert update.VISIBLE_TYPE_ORDER[0] == "Research projects"',
)
replace_once(
    "tests/test_profile_v2.py",
    'assert "### Apps & dashboards (2)" in text',
    'assert "### Apps & dashboards" in text',
)
replace_once(
    "tests/test_profile.py",
    'self.assertIn("Archived repositories (1)", text)',
    'self.assertIn("Archived repositories", text)',
)

print("Profile contract v2 migration applied.")
