from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
update_path = ROOT / "scripts" / "update_profile.py"
tests_path = ROOT / "tests" / "test_profile_v2.py"

text = update_path.read_text(encoding="utf-8")
old = '''def format_metric(value: Any) -> str:\n    if value is None or value == "":\n        return "—"\n    try:\n        number = int(value)\n    except (TypeError, ValueError):\n        return str(value)\n    return "—" if number == 0 else f"{number:,}"'''
new = '''def format_metric(value: Any) -> str:\n    if value is None or value == "":\n        return "-"\n    try:\n        number = int(value)\n    except (TypeError, ValueError):\n        return str(value)\n    return "-" if number == 0 else f"{number:,}"'''
if old not in text:
    raise SystemExit("format_metric anchor not found")
text = text.replace(old, new, 1)
text = text.replace('(\"Publishing since\", str(metrics.get(\"publishing_since\") or \"—\")),', '(\"Publishing since\", str(metrics.get(\"publishing_since\") or \"-\")),')
update_path.write_text(text, encoding="utf-8")

tests = tests_path.read_text(encoding="utf-8")
for old_assert, new_assert in [
    ('assert update.format_metric(0) == "—"', 'assert update.format_metric(0) == "-"'),
    ('assert update.format_metric("0") == "—"', 'assert update.format_metric("0") == "-"'),
    ('assert update.format_metric(None) == "—"', 'assert update.format_metric(None) == "-"'),
]:
    tests = tests.replace(old_assert, new_assert)
tests_path.write_text(tests, encoding="utf-8")

for name in ("repository-types.svg", "research-outputs.svg", "research-metrics.svg"):
    path = ROOT / "assets" / "generated" / name
    svg = path.read_text(encoding="utf-8")
    svg = svg.replace('class="value">—</text>', 'class="value">-</text>')
    path.write_text(svg, encoding="utf-8")
