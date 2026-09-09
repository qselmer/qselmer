from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
render_path = ROOT / "scripts" / "render_profile.py"
update_path = ROOT / "scripts" / "update_profile.py"
test_path = ROOT / "tests" / "test_profile_v2.py"
legacy_test_path = ROOT / "tests" / "test_profile.py"

render = render_path.read_text(encoding="utf-8")
old_constants = '''TABLE_WIDTHS = ("26%", "46%", "12%", "16%")\nORGANIZATIONAL_TABLE_WIDTHS = ("20%", "14%", "14%", "30%", "12%", "10%")'''
new_constants = '''TABLE_TOTAL_WIDTH = "950"\nTABLE_WIDTHS = ("247", "437", "114", "152")\nORGANIZATIONAL_TABLE_WIDTHS = ("190", "133", "133", "285", "114", "95")'''
if old_constants not in render:
    raise SystemExit("table width constants anchor not found")
render = render.replace(old_constants, new_constants, 1)
old_table = '''    return [\n        '<table width="100%">','''
new_table = '''    return [\n        f'<table width="{TABLE_TOTAL_WIDTH}">','''
if old_table not in render:
    raise SystemExit("full table width anchor not found")
render = render.replace(old_table, new_table, 1)
render_path.write_text(render, encoding="utf-8")

update = update_path.read_text(encoding="utf-8")
old_metric = '''def format_metric(value: Any) -> str:\n    if value is None or value == "":\n        return "—"\n    try:\n        return f"{int(value):,}"\n    except (TypeError, ValueError):\n        return str(value)'''
new_metric = '''def format_metric(value: Any) -> str:\n    if value is None or value == "":\n        return "—"\n    try:\n        number = int(value)\n    except (TypeError, ValueError):\n        return str(value)\n    return "—" if number == 0 else f"{number:,}"'''
if old_metric not in update:
    raise SystemExit("format_metric anchor not found")
update = update.replace(old_metric, new_metric, 1)
old_outputs = '''    output_rows = [\n        (SUMMARY_OUTPUT_LABELS[label], str(counts.get(label, 0)))\n        for label in SUMMARY_OUTPUT_TYPE_ORDER\n    ]'''
new_outputs = '''    output_rows = [\n        (SUMMARY_OUTPUT_LABELS[label], format_metric(counts.get(label, 0)))\n        for label in SUMMARY_OUTPUT_TYPE_ORDER\n    ]'''
if old_outputs not in update:
    raise SystemExit("research outputs rows anchor not found")
update = update.replace(old_outputs, new_outputs, 1)
old_types = '''    type_rows = [\n        (label, str(type_counts.get(label, 0)))\n        for label in VISIBLE_TYPE_ORDER\n        if type_counts.get(label, 0) > 0 or label != "Other / legacy"\n    ]'''
new_types = '''    type_rows = [\n        (label, format_metric(type_counts.get(label, 0)))\n        for label in VISIBLE_TYPE_ORDER\n        if type_counts.get(label, 0) > 0 or label != "Other / legacy"\n    ]'''
if old_types not in update:
    raise SystemExit("repository type rows anchor not found")
update = update.replace(old_types, new_types, 1)
update_path.write_text(update, encoding="utf-8")

tests = test_path.read_text(encoding="utf-8")
anchor = '    assert "https://cdn.simpleicons.org/r/276DC3" in table\n    assert ">R<" not in table\n'
addition = '''    assert '<table width="950">' in table\n    assert 'width="247"' in table\n    assert 'width="437"' in table\n    assert 'width="114"' in table\n    assert 'width="152"' in table\n'''
if anchor not in tests:
    raise SystemExit("table test anchor not found")
if addition not in tests:
    tests = tests.replace(anchor, anchor + addition, 1)
metric_test = '''\n\ndef test_zero_summary_values_render_as_dash():\n    assert update.format_metric(0) == "—"\n    assert update.format_metric("0") == "—"\n    assert update.format_metric(None) == "—"\n    assert update.format_metric(5) == "5"\n'''
if "def test_zero_summary_values_render_as_dash" not in tests:
    tests += metric_test
test_path.write_text(tests, encoding="utf-8")

legacy_tests = legacy_test_path.read_text(encoding="utf-8")
legacy_tests = legacy_tests.replace(
    'self.assertIn(\'<table width="100%">\', table)',
    'self.assertIn(\'<table width="950">\', table)',
)
legacy_tests = legacy_tests.replace(
    'self.assertIn(\'<table width="100%">\', text)',
    'self.assertIn(\'<table width="950">\', text)',
)
legacy_test_path.write_text(legacy_tests, encoding="utf-8")

# Regenerate README with fixed-width tables.
spec = importlib.util.spec_from_file_location("render_profile_refresh", render_path)
render_mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(render_mod)
render_mod.main()

# Regenerate the two research cards from existing canonical JSON.
spec2 = importlib.util.spec_from_file_location("update_profile_refresh", update_path)
update_mod = importlib.util.module_from_spec(spec2)
assert spec2.loader is not None
spec2.loader.exec_module(update_mod)
publications_payload = json.loads((ROOT / "assets" / "data" / "publications.json").read_text(encoding="utf-8"))
metrics_payload = json.loads((ROOT / "assets" / "data" / "research-metrics.json").read_text(encoding="utf-8"))
update_mod.generate_research_cards(publications_payload.get("publications") or [], metrics_payload)

# Regenerate Repository Types from the existing canonical repository catalog, without external API calls.
catalog = json.loads((ROOT / "assets" / "data" / "repository-catalog.json").read_text(encoding="utf-8"))
counts = Counter(
    item.get("repository_type_label")
    for item in (catalog.get("repositories") or [])
    if not item.get("archived") and item.get("repository_type_label") in update_mod.VISIBLE_TYPE_ORDER
)
type_rows = [(label, update_mod.format_metric(counts.get(label, 0))) for label in update_mod.VISIBLE_TYPE_ORDER]
(ROOT / "assets" / "generated" / "repository-types.svg").write_text(
    update_mod.card_svg("Repository Types", type_rows), encoding="utf-8"
)
