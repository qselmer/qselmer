# Changes in this revision

- Added **Research Outputs** and **Research Metrics** SVG cards.
- ORCID now retains and renders **all public scholarly works**, not only journal articles.
- Added automatic scholarly-output classification into eight stable groups.
- Added OpenAlex citation count and h-index, matched strictly by ORCID.
- Kept Google Scholar as a visible profile link, not an automated scraping dependency.
- Added `assets/data/research-metrics.json`.
- Renamed `type-learning` to canonical `type-training` → **Courses & training**.
- Kept `type-learning` as a legacy compatibility alias.
- Shortened `type-infrastructure` display label to **Websites & infrastructure**.
- Updated GitHub Actions to refresh metrics and all new generated assets weekly.
- Added optional `OPENALEX_API_KEY` secret support with graceful stale-metric retention.
- Expanded automated tests from 7 to 15.

- Added `assets/data/repository-catalog.json` as the generated source of truth for the complete public GitHub inventory.
- Repository tables now update automatically from GitHub, with rows added/removed without manual README edits.
- Active original repositories are grouped by repository type; **Other / legacy** is retained as an explicit cleanup queue.
- Archived repositories and public forks are now shown in dedicated cleanup tables, while remaining excluded from language/type summary cards.
- Retired `featured-projects.json` from README rendering; it is retained only as a legacy file for reference.
