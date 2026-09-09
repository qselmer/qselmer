from pathlib import Path

render_path = Path("scripts/render_profile.py")
test_path = Path("tests/test_profile_v2.py")
legacy_test_path = Path("tests/test_profile.py")

src = render_path.read_text(encoding="utf-8")

replacements = [
    (
        '# Repository tables intentionally share one compact four-column layout.\n'
        '# Visibility is explicit: 🔓 Public or 🔒 Private. GitHub may adapt widths on\n'
        '# narrow screens, but every personal repository table starts from the same proportions.\n'
        'TABLE_WIDTHS = ("26%", "14%", "46%", "14%")\n'
        'ORGANIZATIONAL_TABLE_WIDTHS = ("20%", "12%", "14%", "14%", "30%", "10%")',
        '# Repository tables intentionally share one compact four-column layout.\n'
        '# Visibility is encoded with an icon only: 🔓 or 🔒, and is the penultimate column.\n'
        '# Main language is represented by the corresponding language logo when supported.\n'
        'TABLE_WIDTHS = ("26%", "46%", "12%", "16%")\n'
        'ORGANIZATIONAL_TABLE_WIDTHS = ("20%", "14%", "14%", "30%", "12%", "10%")',
    ),
    (
        'Public and private repositories are both listed below; visibility is shown in each table as 🔓 Public or 🔒 Private. ',
        'Public and private repositories are both listed below; visibility is shown in each table with 🔓 or 🔒. ',
    ),
    (
        '''def repository_row(repo: dict[str, Any]) -> str:\n    name = esc(repo.get("name") or "unnamed")\n    url = str(repo.get("html_url") or "").strip()\n    private = bool(repo.get("private"))\n    label = f"<code>{name}</code>"\n    project = f'<a href="{html.escape(url, quote=True)}">{label}</a>' if url else label\n    visibility = "🔒 Private" if private else "🔓 Public"\n    cells = [\n        project,\n        visibility,\n        "Private repository" if private else esc(repo.get("description") or "-"),\n        "-" if private else esc(repo.get("language") or "-"),\n    ]\n    return "<tr>" + "".join(\n        f'<td width="{width}">{cell}</td>' for width, cell in zip(TABLE_WIDTHS, cells)\n    ) + "</tr>"''',
        '''def language_logo(value: Any) -> str:\n    language = clean_text(value, "-")\n    if language == "-":\n        return "-"\n    logos = {\n        "r": ("r", "276DC3"),\n        "python": ("python", "3776AB"),\n        "c++": ("cplusplus", "00599C"),\n        "julia": ("julia", "9558B2"),\n        "css": ("css", "663399"),\n        "html": ("html5", "E34F26"),\n        "javascript": ("javascript", "F7DF1E"),\n        "typescript": ("typescript", "3178C6"),\n        "jupyter notebook": ("jupyter", "F37626"),\n        "tex": ("latex", "008080"),\n        "shell": ("gnubash", "4EAA25"),\n    }\n    spec = logos.get(language.casefold())\n    if not spec:\n        return esc(language)\n    slug, color = spec\n    return (\n        f'<img src="https://cdn.simpleicons.org/{slug}/{color}" '\n        f'alt="{html.escape(language, quote=True)}" title="{html.escape(language, quote=True)}" '\n        f'width="20" height="20">'\n    )\n\n\ndef repository_row(repo: dict[str, Any]) -> str:\n    name = esc(repo.get("name") or "unnamed")\n    url = str(repo.get("html_url") or "").strip()\n    private = bool(repo.get("private"))\n    label = f"<code>{name}</code>"\n    project = f'<a href="{html.escape(url, quote=True)}">{label}</a>' if url else label\n    visibility = "🔒" if private else "🔓"\n    cells = [\n        project,\n        "Private repository" if private else esc(repo.get("description") or "-"),\n        visibility,\n        "-" if private else language_logo(repo.get("language") or "-"),\n    ]\n    return "<tr>" + "".join(\n        f'<td width="{width}">{cell}</td>' for width, cell in zip(TABLE_WIDTHS, cells)\n    ) + "</tr>"''',
    ),
    (
        '["Repository", "Visibility", "Description", "Main language"]',
        '["Repository", "Description", "Visibility", "Main language"]',
    ),
    (
        '''def organizational_row(item: dict[str, Any]) -> str:\n    name = esc(item.get("name") or "unnamed")\n    url = str(item.get("html_url") or "").strip()\n    private = bool(item.get("private"))\n    project = f'<a href="{html.escape(url, quote=True)}"><code>{name}</code></a>' if url else f"<code>{name}</code>"\n    visibility = "🔒 Private" if private else "🔓 Public"\n    cells = [\n        project,\n        visibility,\n        esc(item.get("organization")),\n        esc(item.get("role")),\n        esc(item.get("contribution")),\n        esc(item.get("repository_type_label")),\n    ]''',
        '''def organizational_row(item: dict[str, Any]) -> str:\n    name = esc(item.get("name") or "unnamed")\n    url = str(item.get("html_url") or "").strip()\n    private = bool(item.get("private"))\n    project = f'<a href="{html.escape(url, quote=True)}"><code>{name}</code></a>' if url else f"<code>{name}</code>"\n    visibility = "🔒" if private else "🔓"\n    cells = [\n        project,\n        esc(item.get("organization")),\n        esc(item.get("role")),\n        esc(item.get("contribution")),\n        visibility,\n        esc(item.get("repository_type_label")),\n    ]''',
    ),
    (
        '["Repository", "Visibility", "Organization", "Role", "Contribution", "Type"]',
        '["Repository", "Organization", "Role", "Contribution", "Visibility", "Type"]',
    ),
]

for old, new in replacements:
    if old not in src:
        raise SystemExit(f"Expected renderer block not found:\n{old[:160]}")
    src = src.replace(old, new, 1)

render_path.write_text(src, encoding="utf-8")

tests = test_path.read_text(encoding="utf-8")
tests = tests.replace('    assert "🔒 Private" in text\n    assert "🔓 Public" in text\n', '    assert "🔒" in text\n    assert "🔓" in text\n    assert "🔒 Private" not in text\n    assert "🔓 Public" not in text\n')
tests = tests.replace('    assert "🔓 Public" in table\n', '    assert "🔓" in table\n    assert "🔓 Public" not in table\n')
tests = tests.replace(
    '    assert "Main language" in table\n',
    '    assert "Main language" in table\n    assert table.index("Description") < table.index("Visibility") < table.index("Main language")\n    assert "https://cdn.simpleicons.org/r/276DC3" in table\n    assert ">R<" not in table\n',
    1,
)
test_path.write_text(tests, encoding="utf-8")

legacy_tests = legacy_test_path.read_text(encoding="utf-8")
legacy_tests = legacy_tests.replace('        self.assertIn("🔒 Private", text)\n', '        self.assertIn("🔒", text)\n        self.assertNotIn("🔒 Private", text)\n')
legacy_test_path.write_text(legacy_tests, encoding="utf-8")
