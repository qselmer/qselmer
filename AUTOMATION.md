# Profile automation

The profile is refreshed by `.github/workflows/update-profile.yml` every Monday at 06:27 Peru time and can also be run manually from GitHub Actions.

## Data sources

- **ORCID** - canonical public scholarly-output list.
- **Crossref** - DOI metadata enrichment when a DOI is registered there.
- **OpenAlex** - citation count, h-index and i10-index, resolved by ORCID, with a conservative fallback through exact DOI-authorship links from ORCID-listed works.
- **GitHub API** - owned original-repository inventory, public repository languages and controlled repository-type counts.
- **Root `repo.yml`** - principal machine-readable contract for repository identity, lifecycle metadata, profile inclusion and repository relationships when available.
- **Google Scholar** - navigation link only; it is not scraped.

## Optional OpenAlex API key

The workflow can attempt a small OpenAlex query without a key, but a free API key is recommended for reliable scheduled use.

Create the repository secret:

```text
OPENALEX_API_KEY
```

Then the workflow automatically passes it to `scripts/profile_refresh.py`.

If an OpenAlex refresh fails, previously valid OpenAlex metrics are retained rather than replaced with missing values.

## Runtime dependency

Repository contracts are parsed with PyYAML. The pinned dependency used by the profile workflow is declared in:

```text
requirements-profile.txt
```

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

Original repositories owned by `qselmer` are written to `assets/data/repository-catalog.json`; forks are excluded. A root `repo.yml` using schema version 2 is the principal machine-readable contract for repository identity, lifecycle state and profile inclusion.

Classification precedence is explicit:

1. valid `repo.yml`;
2. one canonical GitHub `type-*` topic when `repo.yml` is absent;
3. legacy topic alias;
4. temporary audited override;
5. conservative name inference;
6. unclassified cleanup state.

If `repo.yml` exists but is invalid, the automation does not silently bypass it. If its canonical type disagrees with the GitHub `type-*` topic, `repo.yml` remains authoritative and the catalog records a `classification_conflict` hygiene issue. Repositories with `integration.profile.include: false` remain auditable but are excluded from public portfolio groups and repository-type summary counts.

The public catalog is privacy-filtered before it is committed:

- **Primary Languages** uses active public original repositories only.
- **Repository Types** counts active, profile-included public and private originals visible to the profile automation.
- Detailed repository tables list active, profile-included public and private originals.
- Private repositories are marked with 🔒, but description, language, topics, update timestamp, lifecycle details, relations and other contract metadata are redacted from the public `repository-catalog.json` as well as the README.
- Archived or lifecycle-inactive repositories are excluded from the two summary cards and from active portfolio groups.

Every audited repository should converge on exactly one canonical GitHub `type-*` topic agreeing with `repository.type` in `repo.yml`. See `TOPICS.md`. Repositories without a defensible type remain a cleanup category and are not rendered as an `Other / legacy` section in the public README.

## Research outputs

Every public ORCID work is retained in `publications.json` and classified into a stable scholarly-output group. The GitHub profile shows compact Research Outputs and Research Metrics cards rather than duplicating the full publication list. The detailed publication catalogue is maintained on the academic website from the same canonical data.

## Complete repository inventory and visibility

The portfolio intentionally excludes forks. With `INCLUDE_PRIVATE_REPOS=true`, private originals are included only when the repository secret `PROFILE_REPO_TOKEN` is configured. Use a fine-grained personal access token owned by `qselmer`, with access to all repositories and read-only repository metadata/content sufficient for listing repositories, topics and `repo.yml`.

The private inventory supports complete repository-type counts and the visible portfolio. Private repository names can be rendered with 🔒, while sensitive metadata are redacted before the public catalog artifact is written.

If `PROFILE_REPO_TOKEN` is missing, the workflow falls back to public originals and prints a warning rather than failing; in that case Repository Types necessarily reflects only repositories visible to the workflow.

## Entrypoints

- `scripts/profile_refresh.py` installs the repository-contract layer and then runs the existing scholarly/profile refresh engine in `scripts/update_profile.py`.
- `scripts/profile_render.py` renders the repository portfolio while respecting `profile.include` and lifecycle activity.
- `scripts/repository_contracts.py` parses and validates root `repo.yml` files and checks canonical GitHub topic consistency.
