from pathlib import Path

p = Path('scripts/render_profile.py')
s = p.read_text(encoding='utf-8')

s = s.replace(
    '# Public repository tables intentionally share one compact three-column layout.\n'
    '# GitHub may adapt widths on narrow screens, but every table starts from the\n'
    '# same proportions and full available width.\n'
    'TABLE_WIDTHS = ("28%", "58%", "14%")\n'
    'ORGANIZATIONAL_TABLE_WIDTHS = ("22%", "16%", "16%", "34%", "12%")',
    '# Repository tables intentionally share one compact four-column layout.\n'
    '# Visibility is explicit: 🔓 Public or 🔒 Private. GitHub may adapt widths on\n'
    '# narrow screens, but every personal repository table starts from the same proportions.\n'
    'TABLE_WIDTHS = ("26%", "14%", "46%", "14%")\n'
    'ORGANIZATIONAL_TABLE_WIDTHS = ("20%", "12%", "14%", "14%", "30%", "10%")'
)

s = s.replace(
    '    for heading in ("Research outputs", "How this profile is automated"):',
    '    for heading in ("Research outputs", "How this profile is automated", "Collaboration and opportunities"):'
)

old_intro = (
    "        r'\\1Active original research repositories are organized by their primary scientific or computational function. '"
    "\n        r'Public and private repositories are both listed below; private repositories are marked with 🔒. '"
    "\n        r'Forks and archived repositories are excluded from the active portfolio.',"
)
new_intro = (
    "        r'\\1Active original research repositories are organized by their primary scientific or computational function. '"
    "\n        r'Public and private repositories are both listed below; visibility is shown in each table as 🔓 Public or 🔒 Private. '"
    "\n        r'Forks and archived repositories are excluded from the active portfolio.',"
)
assert old_intro in s, 'Scientific computing intro pattern not found'
s = s.replace(old_intro, new_intro)

old_row = '''def repository_row(repo: dict[str, Any]) -> str:
    name = esc(repo.get("name") or "unnamed")
    url = str(repo.get("html_url") or "").strip()
    private = bool(repo.get("private"))
    label = f"🔒 <code>{name}</code>" if private else f"<code>{name}</code>"
    project = f'<a href="{html.escape(url, quote=True)}">{label}</a>' if url else label
    cells = [
        project,
        "Private repository" if private else esc(repo.get("description") or "—"),
        "—" if private else esc(repo.get("language") or "—"),
    ]
    return "<tr>" + "".join(
        f'<td width="{width}">{cell}</td>' for width, cell in zip(TABLE_WIDTHS, cells)
    ) + "</tr>"
'''
new_row = '''def repository_row(repo: dict[str, Any]) -> str:
    name = esc(repo.get("name") or "unnamed")
    url = str(repo.get("html_url") or "").strip()
    private = bool(repo.get("private"))
    label = f"<code>{name}</code>"
    project = f'<a href="{html.escape(url, quote=True)}">{label}</a>' if url else label
    visibility = "🔒 Private" if private else "🔓 Public"
    cells = [
        project,
        visibility,
        "Private repository" if private else esc(repo.get("description") or "—"),
        "—" if private else esc(repo.get("language") or "—"),
    ]
    return "<tr>" + "".join(
        f'<td width="{width}">{cell}</td>' for width, cell in zip(TABLE_WIDTHS, cells)
    ) + "</tr>"
'''
assert old_row in s, 'repository_row pattern not found'
s = s.replace(old_row, new_row)

s = s.replace(
    '["Repository", "Description", "Main language"],\n        rows,\n        TABLE_WIDTHS,',
    '["Repository", "Visibility", "Description", "Main language"],\n        rows,\n        TABLE_WIDTHS,'
)

old_org = '''def organizational_row(item: dict[str, Any]) -> str:
    name = esc(item.get("name") or "unnamed")
    url = str(item.get("html_url") or "").strip()
    project = f'<a href="{html.escape(url, quote=True)}"><code>{name}</code></a>' if url else f"<code>{name}</code>"
    cells = [
        project,
        esc(item.get("organization")),
        esc(item.get("role")),
        esc(item.get("contribution")),
        esc(item.get("repository_type_label")),
    ]
    return "<tr>" + "".join(
        f'<td width="{width}">{cell}</td>'
        for width, cell in zip(ORGANIZATIONAL_TABLE_WIDTHS, cells)
    ) + "</tr>"
'''
new_org = '''def organizational_row(item: dict[str, Any]) -> str:
    name = esc(item.get("name") or "unnamed")
    url = str(item.get("html_url") or "").strip()
    private = bool(item.get("private"))
    project = f'<a href="{html.escape(url, quote=True)}"><code>{name}</code></a>' if url else f"<code>{name}</code>"
    visibility = "🔒 Private" if private else "🔓 Public"
    cells = [
        project,
        visibility,
        esc(item.get("organization")),
        esc(item.get("role")),
        esc(item.get("contribution")),
        esc(item.get("repository_type_label")),
    ]
    return "<tr>" + "".join(
        f'<td width="{width}">{cell}</td>'
        for width, cell in zip(ORGANIZATIONAL_TABLE_WIDTHS, cells)
    ) + "</tr>"
'''
assert old_org in s, 'organizational_row pattern not found'
s = s.replace(old_org, new_org)

s = s.replace(
    '["Repository", "Organization", "Role", "Contribution", "Type"],',
    '["Repository", "Visibility", "Organization", "Role", "Contribution", "Type"],'
)

s = s.replace(
    '    lines: list[str] = [\n        "<sub>🔒 Private repository.</sub>",\n        "",\n    ]',
    '    lines: list[str] = []'
)

p.write_text(s, encoding='utf-8')

p = Path('tests/test_profile_v2.py')
t = p.read_text(encoding='utf-8')
t = t.replace('    assert "🔒 <code>private-app</code>" in text\n', '    assert "🔒 Private" in text\n    assert "🔓 Public" in text\n')
t = t.replace('def test_personal_repository_table_is_three_columns():', 'def test_personal_repository_table_has_visibility_column():')
t = t.replace('    assert "Visibility" not in table\n', '    assert "Visibility" in table\n    assert "🔓 Public" in table\n')
t += '''\n\ndef test_collaboration_and_opportunities_is_pruned():\n    sample = """Intro\n\n## Collaboration and opportunities\n\nOld collaboration block.\n\n## Scientific computing\n\nKeep me.\n"""\n    refined = render.prune_readme_sections(sample)\n    assert "Collaboration and opportunities" not in refined\n    assert "Old collaboration block" not in refined\n    assert "## Scientific computing" in refined\n'''
p.write_text(t, encoding='utf-8')
