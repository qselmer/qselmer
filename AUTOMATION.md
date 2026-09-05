# Profile automation

The profile is refreshed by `.github/workflows/update-profile.yml` every Monday at 06:27 Peru time and can also be run manually from GitHub Actions.

## Data sources

- **ORCID** — canonical public scholarly-output list.
- **Crossref** — DOI metadata enrichment when a DOI is registered there.
- **OpenAlex** — citation count and h-index, matched strictly through the ORCID identifier.
- **GitHub API** — complete public repository inventory, repository languages and controlled repository-type counts.
- **Google Scholar** — navigation link only; it is not scraped.

## Optional OpenAlex API key

The workflow can attempt a small OpenAlex query without a key, but a free API key is recommended for reliable scheduled use.

Create the repository secret:

```text
OPENALEX_API_KEY
```

Then the workflow automatically passes it to `scripts/update_profile.py`.

If an OpenAlex refresh fails, previously valid OpenAlex metrics are retained rather than replaced with missing values.

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

`github-stats.svg` is retained only for compatibility and is not displayed in the profile.

## Repository inventory and types

Every public repository owned by `qselmer` is written to `assets/data/repository-catalog.json` and rendered into the README. Active original repositories are grouped by canonical repository type. Archived original repositories and public forks are shown in separate cleanup sections. Private repositories are never written to the public catalog.

The **Primary Languages** and **Repository Types** cards remain PhD-facing summary metrics and therefore use only active original public repositories; forks and archived repositories are excluded from those two cards.

New repositories should have one canonical primary `type-*` topic. See `TOPICS.md`. Repositories without a defensible type remain visible under **Other / legacy** until they are reclassified, archived or removed.

## Research outputs

Every public ORCID work is retained in `publications.json` and classified into one of eight output groups. By default, the README renders all public ORCID works. To limit the visible list later, set `MAX_RESEARCH_OUTPUTS` in the workflow to a positive integer.
