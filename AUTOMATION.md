# Profile automation

The profile is refreshed by `.github/workflows/update-profile.yml` every Monday at 06:27 Peru time and can also be run manually from GitHub Actions.

## Data sources

- **ORCID** — canonical public scholarly-output list.
- **Crossref** — DOI metadata enrichment when a DOI is registered there.
- **OpenAlex** — citation count and h-index, matched strictly through the ORCID identifier.
- **GitHub API** — public original-repository inventory, repository languages and controlled repository-type counts.
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

Public original repositories owned by `qselmer` are written to `assets/data/repository-catalog.json` and rendered into the README. Active originals are grouped by canonical repository type and archived originals remain available as a cleanup section. Forks and private repositories are excluded from the public catalog.

The **Primary Languages** and **Repository Types** cards use only active original public repositories; archived repositories are excluded from those two cards.

New repositories should have one canonical primary `type-*` topic. See `TOPICS.md`. Repositories without a defensible type remain visible under **Other / legacy** until they are reclassified, archived or removed.

## Research outputs

Every public ORCID work is retained in `publications.json` and classified into one of eight output groups. By default, the README renders all public ORCID works. To limit the visible list later, set `MAX_RESEARCH_OUTPUTS` in the workflow to a positive integer.

## Complete repository inventory and visibility

The portfolio intentionally excludes forks. With `INCLUDE_PRIVATE_REPOS=true`, private originals are included only when the repository secret `PROFILE_REPO_TOKEN` is configured. Use a fine-grained personal access token owned by `qselmer`, with access to all repositories and read-only repository metadata/content sufficient for listing repositories and topics.

- `🔓 Public` = public original repository.
- `🔒 Private` = private original repository visible to the read token.
- Private descriptions, language and update dates are suppressed in the public README.
- Summary cards count only active public originals.

If `PROFILE_REPO_TOKEN` is missing, the workflow falls back to public originals and prints a warning rather than failing.

## Research outputs versus active manuscripts

`Research outputs` is a bibliographic record generated from public ORCID Works. `Active manuscripts & research projects` is a manually controlled project-status table for work that is unpublished, submitted, in preparation or planned. A conference presentation can therefore be an ORCID output while a manuscript based on the same study remains active in the pipeline.
