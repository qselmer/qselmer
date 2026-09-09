from pathlib import Path

src = Path('scripts/migrate_profile_layout_v4.py').read_text(encoding='utf-8')
src = src.replace("    new_refine + '\\n\\ndef clean_text',", "    lambda m: new_refine + '\\n\\ndef clean_text',")
src = src.replace("    new_row + '\\n\\ndef full_width_table',", "    lambda m: new_row + '\\n\\ndef full_width_table',")
src = src.replace("    new_projects + '\\n\\ndef main()',", "    lambda m: new_projects + '\\n\\ndef main()',")
src = src.replace("    new_inventory_test.rstrip(),", "    lambda m: new_inventory_test.rstrip(),")
exec(compile(src, 'scripts/migrate_profile_layout_v4.py', 'exec'))
