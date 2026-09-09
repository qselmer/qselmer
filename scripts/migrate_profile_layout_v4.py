from pathlib import Path
import re


def dedent10(text: str) -> str:
    return re.sub(r'^ {10}', '', text, flags=re.M)


p = Path('scripts/render_profile.py')
s = p.read_text(encoding='utf-8')

new_refine = dedent10(r'''def refine_static_readme(text: str) -> str:
          """Apply stable presentation rules without shortening the biography or research focus."""
          old_professional_heading = '<h2 align="center">Marine Quantitative Ecologist & Fisheries Scientist</h2>'
          professional_heading = '<h1 align="center">Marine Quantitative Ecologist & Fisheries Scientist</h1>'
          text = text.replace(old_professional_heading, professional_heading)
          if '<h1 align="center">Elmer Quispe-Salazar</h1>' not in text:
              text = text.replace(
                  professional_heading,
                  '<h1 align="center">Elmer Quispe-Salazar</h1>\n\n' + professional_heading,
                  1,
              )

          text = text.replace(
              '\n<p align="center"><strong>Instituto del Mar del Perú (IMARPE)</strong> · Peru</p>\n',
              "\n",
          )

          text = re.sub(
              r'\n<p align="center">\s*<img[^>]+komarev\.com/ghpvc/[^>]+>\s*</p>\n',
              "\n",
              text,
              flags=re.S,
          )
          text = re.sub(r'\n\s*<a href="https://www\.researchgate\.net/[^\n]+</a>', "", text)
          text = re.sub(r'\n\s*<a href="https://x\.com/[^\n]+</a>', "", text)

          profile_links = None
          for match in re.finditer(
              r'\n(<p align="center">\s*(?:(?:<a href="[^"]+">.*?</a>)\s*)+</p>)\n',
              text,
              flags=re.S,
          ):
              if "Google_Scholar" in match.group(1) and "ORCID" in match.group(1):
                  profile_links = match
                  break
          if profile_links:
              block = profile_links.group(1)
              start, end = profile_links.span(1)
              text = text[:start] + text[end:]
              text = text.replace(professional_heading, professional_heading + "\n\n" + block, 1)

          text = text.replace("\n## Research outputs & metrics\n", "\n")
          text = re.sub(
              r'<sub>This card summarizes the public scholarly record\..*?</sub>',
              METRICS_NOTE,
              text,
              count=1,
              flags=re.S,
          )

          text = text.replace(PORTFOLIO_NOTE, "")
          text = re.sub(
              r'\n<p align="center">\s*<img src="assets/generated/top-languages\.svg".*?'
              r'<img src="assets/generated/repository-types\.svg".*?</p>\n',
              "\n",
              text,
              count=1,
              flags=re.S,
          )

          focus_match = re.search(r'(\n## Research focus\n.*?)(?=\n## |\Z)', text, flags=re.S)
          if focus_match:
              focus_block = focus_match.group(1).rstrip()
              replacement = focus_block + "\n\n" + PORTFOLIO_CARDS + "\n\n" + PORTFOLIO_NOTE + "\n"
              text = text[:focus_match.start()] + replacement + text[focus_match.end():]

          text = re.sub(
              r'(## Scientific computing & reproducible research\n\n).*?(?=\n\n<!-- PROJECTS:START -->)',
              r'\1Active original research repositories are organized by their primary scientific or computational function. '
              r'Public and private repositories are both listed below; private repositories are marked with 🔒. '
              r'Forks and archived repositories are excluded from the active portfolio.',
              text,
              count=1,
              flags=re.S,
          )

          text = re.sub(
              r'\n\s*<img src="https://img\.shields\.io/badge/(?:Git-|GitHub_Actions-|Quarto-)[^\n]+>',
              "",
              text,
          )
          return re.sub(r"\n{3,}", "\n\n", text)
''')

s, n = re.subn(
    r'def refine_static_readme\(text: str\) -> str:.*?\n\ndef clean_text',
    new_refine + '\n\ndef clean_text',
    s,
    count=1,
    flags=re.S,
)
assert n == 1, 'Could not replace refine_static_readme'

new_row = dedent10(r'''def repository_row(repo: dict[str, Any]) -> str:
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
''')

s, n = re.subn(
    r'def repository_row\(repo: dict\[str, Any\]\) -> str:.*?\n\ndef full_width_table',
    new_row + '\n\ndef full_width_table',
    s,
    count=1,
    flags=re.S,
)
assert n == 1, 'Could not replace repository_row'

new_projects = dedent10(r'''def render_projects() -> str:
          payload = load(REPOSITORY_CATALOG, {"repositories": [], "totals": {}})
          repositories = payload.get("repositories") or []
          if not repositories:
              return "_Repository inventory will be populated on the next profile Action run._"

          active = [repo for repo in repositories if not repo.get("archived")]
          archived = [repo for repo in repositories if repo.get("archived")]
          lines: list[str] = [
              "<sub>🔒 Private repository.</sub>",
              "",
          ]

          for label in VISIBLE_TYPE_ORDER:
              group = sorted(
                  [repo for repo in active if repo.get("repository_type_label") == label],
                  key=lambda x: (bool(x.get("private")), str(x.get("name") or "").casefold()),
              )
              if not group:
                  continue
              lines += [f"### {label} ({len(group)})", ""]
              lines += repository_table(group) + [""]

          lines += render_organizational_contributions()

          if archived:
              lines += [
                  f"### Archived repositories ({len(archived)})",
                  "",
                  "<sub>Archived originals remain available for audit purposes but are excluded from summary cards and active groups.</sub>",
                  "",
              ]
              lines += repository_table(
                  sorted(archived, key=lambda x: (bool(x.get("private")), str(x.get("name") or "").casefold()))
              ) + [""]

          return "\n".join(lines).rstrip()
''')

s, n = re.subn(
    r'def render_projects\(\) -> str:.*?\n\ndef main\(\)',
    new_projects + '\n\ndef main()',
    s,
    count=1,
    flags=re.S,
)
assert n == 1, 'Could not replace render_projects'
p.write_text(s, encoding='utf-8')

# Tests
p = Path('tests/test_profile_v2.py')
t = p.read_text(encoding='utf-8')
new_inventory_test = dedent10(r'''def test_readme_inventory_lists_public_and_private_repositories():
          original_load = render.load
          try:
              def fake_load(path, default):
                  if path == render.ORGANIZATIONAL_CONTRIBUTIONS:
                      return {"contributions": []}
                  return {
                      "repositories": [
                          {
                              "name": "public-app",
                              "html_url": "https://github.com/qselmer/public-app",
                              "description": "Public app",
                              "language": "Python",
                              "private": False,
                              "archived": False,
                              "repository_type_label": "Apps & dashboards",
                          },
                          {
                              "name": "private-app",
                              "html_url": "https://github.com/qselmer/private-app",
                              "description": "Sensitive description",
                              "language": "R",
                              "private": True,
                              "archived": False,
                              "repository_type_label": "Apps & dashboards",
                          },
                      ]
                  }
              render.load = fake_load
              text = render.render_projects()
          finally:
              render.load = original_load

          assert "### Apps & dashboards (2)" in text
          assert "public-app" in text
          assert "private-app" in text
          assert "🔒 <code>private-app</code>" in text
          assert "Sensitive description" not in text
          assert "Private repository" in text
''')

t, n = re.subn(
    r'def test_readme_inventory_lists_public_repositories_only\(\):.*?(?=\n\ndef test_personal_repository_table_is_three_columns)',
    new_inventory_test.rstrip(),
    t,
    count=1,
    flags=re.S,
)
assert n == 1, 'Could not replace inventory test'

start = t.index('def test_static_refinement_preserves_biography_and_research_focus():')
new_static_test = '''def test_static_refinement_preserves_biography_and_research_focus():
    sample = \"\"\"<h2 align=\"center\">Marine Quantitative Ecologist & Fisheries Scientist</h2>

<p align=\"justify\">BIOGRAPHY MUST REMAIN EXACTLY AS WRITTEN.</p>

<p align=\"center\"><img src=\"https://komarev.com/ghpvc/?username=qselmer\" alt=\"Profile views\"></p>

<p align=\"center\">
<a href=\"https://www.researchgate.net/profile/Elmer-Quispe-Salazar\">ResearchGate</a>
<a href=\"https://x.com/elmerseascient\">X</a>
</p>

<p align=\"center\">
  <img src=\"assets/generated/top-languages.svg\" width=\"410\" alt=\"x\">
  <img src=\"assets/generated/repository-types.svg\" width=\"410\" alt=\"y\">
</p>

## Research focus

- KEEP THIS FOCUS LINE.

## Research outputs & metrics

<p align=\"center\">
  <img src=\"assets/generated/research-outputs.svg\" width=\"410\" alt=\"x\">
  <img src=\"assets/generated/research-metrics.svg\" width=\"410\" alt=\"y\">
</p>

<sub>This card summarizes the public scholarly record. ORCID is the canonical source for research outputs; DOI records are enriched with Crossref metadata. Citation count, h-index and i10-index are refreshed from OpenAlex, resolving the author first by ORCID and, when needed, through exact DOI-authorship links from the ORCID record. Google Scholar remains linked above for profile discovery and citation browsing, but is not scraped by the automation.</sub>

## Scientific computing & reproducible research

Old intro.

<!-- PROJECTS:START -->
x
<!-- PROJECTS:END -->
\"\"\"
    refined = render.refine_static_readme(sample)
    assert \"BIOGRAPHY MUST REMAIN EXACTLY AS WRITTEN.\" in refined
    assert \"- KEEP THIS FOCUS LINE.\" in refined
    assert \"Profile views\" not in refined
    assert \"researchgate.net\" not in refined
    assert \"https://x.com\" not in refined
    assert \"Instituto del Mar del Perú (IMARPE)\" not in refined
    assert \"## Research outputs & metrics\" not in refined
    assert '<h1 align=\"center\">Elmer Quispe-Salazar</h1>' in refined
    assert '<h1 align=\"center\">Marine Quantitative Ecologist & Fisheries Scientist</h1>' in refined
    assert refined.index(\"assets/generated/research-outputs.svg\") < refined.index(\"## Research focus\")
    assert refined.index(\"## Research focus\") < refined.index(\"assets/generated/top-languages.svg\")
'''
t = t[:start] + new_static_test
p.write_text(t, encoding='utf-8')

# Documentation
p = Path('AUTOMATION.md')
a = p.read_text(encoding='utf-8')
a = a.replace(
    '- Public repository tables list active public originals only.\n- Private repository names and metadata are not rendered in the public tables.',
    '- Detailed repository tables list active public and private originals.\n- Private repositories are marked with 🔒; their descriptions and language metadata are suppressed in the public README.',
)
a = a.replace(
    'The private inventory is used to support complete repository-type counts and internal portfolio management. It does **not** cause private repository names, descriptions, languages or update dates to be rendered in the public README.',
    'The private inventory supports complete repository-type counts and the visible portfolio. Private repository names are rendered with 🔒, while descriptions, language and other sensitive metadata remain suppressed in the public README.',
)
p.write_text(a, encoding='utf-8')

p = Path('TOPICS.md')
x = p.read_text(encoding='utf-8')
x = x.replace(
    'Public repositories form the visible README portfolio, while private originals can contribute to complete repository-type counts when the profile automation can access them.',
    'Public and private originals form the visible README portfolio when the profile automation can access them; private repositories are marked with 🔒.',
)
x = x.replace(
    '- **Detailed repository tables**: active, public, original repositories only.',
    '- **Detailed repository tables**: active original repositories, including public and private repositories visible to the profile automation; private rows are marked with 🔒.',
)
x = x.replace(
    'Private repository names and metadata are retained only in the canonical internal catalog when the configured read token can access them. They are not rendered in the public README tables.',
    'Private repository names are rendered in the README with 🔒 when the configured read token can access them. Private descriptions and language metadata remain suppressed.',
)
x = x.replace(
    'while the public README shows only the academic repository grouping for public repositories.',
    'while the public README shows the academic repository grouping for both public and private active originals, marking private repositories with 🔒.',
)
p.write_text(x, encoding='utf-8')
