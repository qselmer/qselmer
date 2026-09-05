# Profile audit

## Objective

The profile is optimized as an academic landing page for PhD applications in quantitative marine ecology, fisheries science, ecological statistics, marine ecosystem modelling and scientific computing.

## Architecture implemented

### GitHub portfolio

The profile automatically displays two repository cards:

- **Primary Languages** — language composition across original public repositories.
- **Repository Types** — counts based on the controlled `type-*` repository taxonomy.

Forks, archived repositories and private repositories are excluded from these two public portfolio statistics. In addition, the README now renders a **complete public repository inventory**: every public repository owned by `qselmer` is shown, with active originals grouped by type and archived repositories/forks separated for cleanup. Private repository metadata is never exposed.

### Research outputs

ORCID is the canonical scholarly-output source. **All public ORCID works are retained**, not only peer-reviewed journal articles. DOI-bearing records are enriched through Crossref where metadata are available.

Outputs are classified into:

1. Journal articles
2. Preprints & working papers
3. Conference outputs
4. Books & chapters
5. Theses
6. Reports & technical outputs
7. Data & software
8. Other research outputs

The README renders every public ORCID work by default and labels each record by output class.

### Research metrics

The profile generates a separate **Research Metrics** card. The metrics shown are deliberately source-specific:

- public ORCID works — ORCID;
- journal-article count — ORCID classification;
- citations — OpenAlex;
- h-index — OpenAlex;
- publishing since — earliest dated public ORCID work.

OpenAlex author identity is matched through the ORCID identifier. The automation does not use name-only matching for citation metrics.

Google Scholar remains an important visible profile link, but it is **not scraped** by the workflow. This avoids an unstable unofficial dependency while still making Scholar available to supervisors and selection committees.

### Repository taxonomy

Canonical types are:

- `type-package` → Packages
- `type-protocol` → Protocols & manuals
- `type-workflow` → Methods & workflows
- `type-report` → Reports
- `type-app` / `type-dashboard` → Apps & dashboards
- `type-paper` → Papers
- `type-training` → Courses & training
- `type-infrastructure` → Websites & infrastructure

`type-learning` remains only as a compatibility alias for `type-training`.

## PhD-profile design decisions

1. Research identity and PhD availability remain visible before the technical portfolio.
2. Repository languages and repository functions are emphasized rather than stars/followers.
3. Scholarly productivity is separated from GitHub productivity.
4. Output counts and bibliometric metrics explicitly state their data sources.
5. Conference outputs, theses and non-journal products remain visible because they document research activity and are legitimate scholarly outputs.
6. Unpublished manuscripts remain in the manually curated research pipeline and are not mixed into ORCID publication metrics.

## Automation

The workflow runs weekly and can also be executed manually. A free `OPENALEX_API_KEY` repository secret is recommended for reliable scheduled citation-metric refreshes. If a refresh fails, previously valid OpenAlex metrics are retained. It refreshes:

- `assets/data/publications.json`
- `assets/data/research-metrics.json`
- `assets/data/repository-catalog.json`
- `assets/generated/top-languages.svg`
- `assets/generated/repository-types.svg`
- `assets/generated/research-outputs.svg`
- `assets/generated/research-metrics.svg`
- `assets/generated/github-stats.svg` (compatibility asset; not displayed)
- `README.md`

The workflow commits updates directly to `main`, preserving the existing behavior of the personal profile repository.

## Remaining manual recommendations

### Pinned repositories

For PhD recruitment, pin repositories that demonstrate research independence and methodological depth rather than course forks. A strong current set should prioritize scientific software, a reproducible paper repository, marine/ocean modelling, and one advanced training resource.

### Repository hygiene

The complete public repository inventory is intentionally exhaustive during cleanup. Use **Other / legacy**, **Archived repositories** and **Forks** as review queues. Archive or remove obsolete experiments, abandoned tests, duplicated forks and old coursework when they no longer represent the active portfolio. Archived repositories and forks remain visible in the cleanup inventory but are automatically excluded from language/type summary metrics.

### Topics

Migrate important active repositories to one canonical `type-*` topic. The override file is a compatibility bridge, not the long-term source of truth.
