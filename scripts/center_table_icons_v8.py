from pathlib import Path

render_path = Path("scripts/render_profile.py")
test_path = Path("tests/test_profile_v2.py")

src = render_path.read_text(encoding="utf-8")

old_repo = '''    return "<tr>" + "".join(\n        f'<td width="{width}">{cell}</td>' for width, cell in zip(TABLE_WIDTHS, cells)\n    ) + "</tr>"'''
new_repo = '''    return "<tr>" + "".join(\n        f'<td width="{width}"{\' align="center"\' if index in (2, 3) else \'\'}>{cell}</td>'\n        for index, (width, cell) in enumerate(zip(TABLE_WIDTHS, cells))\n    ) + "</tr>"'''

if old_repo not in src:
    raise SystemExit("Personal repository row block not found")
src = src.replace(old_repo, new_repo, 1)

old_org = '''    return "<tr>" + "".join(\n        f'<td width="{width}">{cell}</td>'\n        for width, cell in zip(ORGANIZATIONAL_TABLE_WIDTHS, cells)\n    ) + "</tr>"'''
new_org = '''    return "<tr>" + "".join(\n        f'<td width="{width}"{\' align="center"\' if index == 4 else \'\'}>{cell}</td>'\n        for index, (width, cell) in enumerate(zip(ORGANIZATIONAL_TABLE_WIDTHS, cells))\n    ) + "</tr>"'''

if old_org not in src:
    raise SystemExit("Organizational repository row block not found")
src = src.replace(old_org, new_org, 1)

render_path.write_text(src, encoding="utf-8")

tests = test_path.read_text(encoding="utf-8")
anchor = '    assert "https://cdn.simpleicons.org/r/276DC3" in table\n'
addition = '    assert table.count(\'align="center"\') >= 2\n'
if addition not in tests:
    if anchor not in tests:
        raise SystemExit("Test anchor not found")
    tests = tests.replace(anchor, anchor + addition, 1)

test_path.write_text(tests, encoding="utf-8")
