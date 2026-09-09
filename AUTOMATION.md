# Profile automation

The profile is refreshed by `.github/workflows/update-profile.yml` every Monday at 06:27 Peru time and can also be run manually from GitHub Actions.

## Data sources

- **ORCID** — canonical public scholarly-output list.
- **Crossref** — DOI metadata enrichment when a DOI is registered there.
- **OpenAlex** — citation count, h-index and i10-index, resolved by ORCID, with a conservative fallback through exact DOI-authorship links from ORCID-listed works.
- **GitHub API** — owned original-repository inventory, public repository languages and controlled repository-type counts.
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

Original repositories owned by `qselmer` are written to `assets/data/repository-catalog.json`. When the read token can see private repositories, the canonical catalog retains both public and private originals; forks are excluded.

The public README is deliberately narrower than the canonical catalog:

- **Primary Languages** uses active public original repositories only.
- **Repository Types** counts active public and private original repositories visible to the profile automation.
- Public repository tables list active public originals only.
- Private repository names and metadata are not rendered in the public tables.
- Archived repositories are excluded from the two summary cards and from the active portfolio groups.

New repositories should have one canonical primary `type-*` topic. See `TOPICS.md`. Repositories without a defensible type remain an internal cleanup category in `repository-catalog.json`; they are not rendered as an `Other / legacy` section in the public README.

## Research outputs

Every public ORCID work is retained in `publications.json` and classified into a stable scholarly-output group. The GitHub profile shows compact Research Outputs and Research Metrics cards rather than duplicating the full publication list. The detailed publication catalogue is maintained on the academic website from the same canonical data.

## Complete repository inventory and visibility

The portfolio intentionally excludes forks. With `INCLUDE_PRIVATE_REPOS=true`, private originals are included only when the repository secret `PROFILE_REPO_TOKEN` is configured. Use a fine-grained personal access token owned by `qselmer`, with access to all repositories and read-only repository metadata/content sufficient for listing repositories and topics.

The private inventory is used to support complete repository-type counts and internal portfolio management. It does **not** cause private repository names, descriptions, languages or update dates to be rendered in the public README.

If `PROFILE_REPO_TOKEN` is missing, the workflow falls back to public originals and prints a warning rather than failing; in that case Repository Types necessarily reflects only repositories visible to the workflow.
