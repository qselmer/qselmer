# Changes

## v4 — personal taxonomy cleanup

- Removed the explicit “Currently seeking PhD opportunities internationally” banner from the profile header.
- Replaced the conference microphone icon with the more academic `🏛️` marker.
- Removed repository-level `type-report` from the personal taxonomy. Research-output reports remain a valid ORCID output category.
- Added `type-template` → **Templates** and moved reusable template repositories into that category.
- Fork repositories are now excluded from the public repository catalog and README rather than rendered as a cleanup table.
- Documented a primary-function decision tree for assigning exactly one canonical repository `type-*` topic.

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

## v5 — repository visibility and non-duplicative research sections

- separated public ORCID research outputs from active manuscripts/projects using a compact pipeline table;
- retained the academic conference icon `🏛️`;
- changed the repository portfolio to include all original repositories visible to an optional read-only `PROFILE_REPO_TOKEN`;
- excluded forks from the portfolio;
- added `🔓 Public` / `🔒 Private` visibility indicators to every repository row;
- suppressed description, language and update-date metadata for private repositories on the public README;
- added the repository classification basis to support manual `type-*` cleanup;
- summary cards continue to use active public original repositories only;
- updated GitHub Actions to Node 24-compatible `actions/checkout@v5` and `actions/setup-python@v6`.


## v6 — academic presentation refinement

- Removed the visible active-manuscript/project section to avoid repeating conference outputs and related studies.
- Grouped ORCID research outputs by scholarly-output type and ordered records by year within each group.
- Removed decorative output icons from the bibliography-facing list.
- Renamed the repository section to **Scientific computing & reproducible research**.
- Removed public inventory/taxonomy progress counters and the `Type basis` column from the README; classification provenance remains in the JSON catalog for audit use.
- Broadened the research description from small pelagics to pelagic systems, reflecting work on anchoveta, jack mackerel, Pacific bonito, chub mackerel and tunas.

## v8 — personal taxonomy simplification and contact visibility

- Removed `type-protocol` / **Protocols & manuals** from the personal repository taxonomy; this category is reserved for organizational/institutional portfolios rather than the personal academic profile.
- Added the academic website (`qselmer.github.io`) alongside the contact email in the profile introduction.
- Kept templates as a dedicated personal repository type.
