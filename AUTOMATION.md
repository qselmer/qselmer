# Profile automation

The profile is refreshed by `.github/workflows/update-profile.yml` every Monday at 06:27 Peru time and can also be run manually from GitHub Actions.

## Data sources

- **ORCID** — canonical public scholarly-output list.
- **Crossref** — DOI metadata enrichment when available.
- **OpenAlex** — citation count and h-index, matched strictly through the ORCID identifier.
- **GitHub API** — original-repository inventory, repository languages and controlled repository-type counts.
- **Google Scholar** — profile link only; it is not scraped.

## Repository access

Public original repositories are available through the standard GitHub API. Private original repositories are included only when both conditions are met:

```text
INCLUDE_PRIVATE_REPOS=true
PROFILE_REPO_TOKEN=<repository secret>
```

`PROFILE_REPO_TOKEN` should be a fine-grained personal access token with read-only access to the repositories required for the inventory. Forks are excluded from the portfolio.

For private repositories, the public README exposes only the repository name, visibility and controlled repository type. Description, language and update date are suppressed.

The **Primary Languages** and **Repository Types** cards use only active original public repositories, so private and archived repositories do not distort the public-facing summary.

## Repository taxonomy

Each active repository should have exactly one canonical `type-*` topic. See `TOPICS.md`.

Repositories without a defensible canonical type remain under **Other / legacy** until they are classified, archived or removed. Explicit `type-*` topics are the preferred long-term source of truth; overrides and name inference are compatibility fallbacks.

## Research outputs

Every public ORCID work is retained in `assets/data/publications.json` and classified by scholarly-output type. DOI-bearing records are enriched through Crossref when possible. The README renders outputs grouped by type.

## Research metrics

A free `OPENALEX_API_KEY` repository secret is recommended for reliable scheduled refreshes. If an OpenAlex refresh fails, previously valid metrics are retained instead of being replaced with missing values.

## Generated files

The workflow updates:

```text
README.md
assets/data/publications.json
assets/data/research-metrics.json
assets/data/repository-catalog.json
assets/generated/top-languages.svg
assets/generated/repository-types.svg
assets/generated/research-outputs.svg
assets/generated/research-metrics.svg
assets/generated/github-stats.svg
```

`github-stats.svg` is retained as a compatibility asset and is not displayed in the profile.

## Maintenance

The workflow validates JSON, compiles the Python scripts, runs the unit tests and commits generated changes directly to `main` when the rendered profile has changed.
