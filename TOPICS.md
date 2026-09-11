# Repository type topics

This profile uses a controlled taxonomy for **original repositories owned by `qselmer`**. Forks are excluded from the academic portfolio. Every active original repository should expose exactly one canonical `type-*` topic and should keep that type consistent with its root `repo.yml` contract.

## Core rule

`type-*` answers one question only:

> **What is this repository?**

It does **not** describe maintenance state, scientific stage, or expected outputs. Those belong in `repo.yml` as `status`, `stage`, `target_outputs`, and `relations`.

A repository must not use multiple primary types such as `type-project + type-paper` or `type-paper + type-workflow`.

## Canonical types

| Topic | Profile group | Intended use |
|---|---|---|
| `type-project` | Research projects | Autonomous or umbrella research programmes that can produce multiple outputs. |
| `type-paper` | Papers | Repositories organized around one defined scientific manuscript. |
| `type-workflow` | Methods & workflows | Reusable scientific methods, pipelines and reproducible workflows. |
| `type-package` | Packages | Reusable scientific software, libraries and installable packages. |
| `type-app` | Apps & dashboards | Interactive applications, dashboards, explorers and scientific web tools. |
| `type-dashboard` | Apps & dashboards | Historical compatibility alias for dashboard-oriented products; prefer `type-app`. |
| `type-training` | Courses & training | Original courses, workshops, tutorials and teaching material. |
| `type-template` | Templates | Reusable repository, analysis, report or teaching scaffolds. |
| `type-infrastructure` | Websites & infrastructure | Profile repositories, websites, automation and central technical infrastructure. |

`type-learning` is retained only as a legacy alias for `type-training`. New repositories should use `type-training`.

`type-report` and `type-data-product` are not part of the canonical personal-profile taxonomy. A repository that produces a report or data product must be classified by what the repository itself is: for example a workflow, project, package, app or template.

## Project, paper and workflow

Use `type-project` when the repository represents a substantive research programme, umbrella project or scientific line that can produce multiple outputs such as papers, workflows, software, apps, datasets or reports.

Use `type-paper` when the repository is organized around one sufficiently defined scientific question and its analytical architecture converges on a single manuscript. A paper remains `type-paper` while it is in concept, design, analysis, writing, submitted or published stages.

Use `type-workflow` when the repository implements a reusable procedure that can be applied repeatedly across studies or papers.

### Decision test

1. Can the repository produce several distinct scientific outputs while continuing to exist as the parent programme? → `type-project`.
2. Is the repository's complete purpose to develop and reproduce one manuscript? → `type-paper`.
3. Is the repository's main object a reusable scientific procedure? → `type-workflow`.

## Project does not mean unfinished paper

A manuscript repository is not a project merely because the article is unfinished.

```yaml
repository:
  type: type-paper
  status: active
  stage: analysis
```

The distinction is conceptual, not temporal.

## Project to paper conversion

A `type-project` should be converted to `type-paper` only when **both** conditions hold:

1. the repository's complete purpose becomes one specific article; and
2. it no longer functions as an umbrella or multi-output research project.

In that case the old type is replaced; both types are never retained simultaneously. When the project remains broader than one article, keep the project repository and create a separate `*-paper` repository for the manuscript.

Example:

```text
P-SDM-anchovy                 type-project
├── ancNC-nonstationarity-paper   type-paper
├── ancNC-transferability-paper   type-paper
└── environmental-data-workflow   type-workflow
```

## Lifecycle is separate from type

Recommended `status` values include:

- `development`
- `active`
- `stable`
- `maintenance`
- `archived`

Recommended `stage` values depend on repository type. Examples:

- projects: `concept`, `research`, `synthesis`
- papers: `concept`, `design`, `analysis`, `writing`, `submitted`, `published`
- workflows/packages: `prototype`, `development`, `stable`

These values do not replace the canonical type.

## Root `repo.yml`

Every active original repository should contain a root `repo.yml`. This is the machine-readable repository contract and should agree with GitHub metadata.

Minimum structure:

```yaml
schema_version: 2

repository:
  owner: qselmer
  name: REPOSITORY_NAME
  title: Human Readable Title
  type: type-project
  status: active
  stage: research
  visibility: public
  description: >
    Concise scientific description.
  topics:
    - type-project
    - fisheries

integration:
  profile:
    include: true
  repository_url: >
    https://github.com/qselmer/REPOSITORY_NAME
```

Projects may additionally declare `target_outputs`; connected repositories may use `relations.parent_project`, `relations.uses`, and `relations.outputs`.

## GitHub topics

Every active original repository should have **exactly one** canonical `type-*` topic. Domain topics such as `fisheries`, `marine-ecology`, `stock-assessment`, `anchovy`, `r`, `python`, or `spatiotemporal` are secondary descriptors.

A repository with multiple canonical type topics is considered ambiguous and should be corrected rather than guessed.

## Current automation precedence

The profile automation currently resolves repository type conservatively in this order:

1. exactly one canonical `type-*` GitHub topic;
2. recognized legacy topic alias;
3. temporary audited override in `assets/data/repository-types.json`;
4. conservative name-based inference for legacy repositories;
5. internal `Other / legacy` cleanup state when no defensible classification exists or type topics conflict.

The cleanup objective is to move active repositories toward explicit, agreeing GitHub metadata plus `repo.yml`, and progressively eliminate overrides and name inference.

`type-project` is intentionally not inferred from repository names because the word "project" is too generic.

## Profile mapping

The public profile uses the following stable mapping:

| Canonical type | README group |
|---|---|
| `type-project` | Research projects |
| `type-paper` | Papers |
| `type-workflow` | Methods & workflows |
| `type-package` | Packages |
| `type-app` | Apps & dashboards |
| `type-dashboard` | Apps & dashboards |
| `type-training` | Courses & training |
| `type-template` | Templates |
| `type-infrastructure` | Websites & infrastructure |

`Research projects` is reserved for substantive scientific projects and umbrella programmes. It must not become a catch-all category for miscellaneous repositories.

## Forks and archived repositories

Forks are excluded from the main inventory and normally receive no personal `type-*` topic. They remain reference material unless a separate independent project is created.

Archived original repositories remain auditable but are excluded from active portfolio groups and active summary counts.

## Profile inclusion

`repo.yml` should declare:

```yaml
integration:
  profile:
    include: true
```

Use `false` for auxiliary experiments, technical tests or repositories that should not appear in the academic portfolio.

## Consistency requirement

For every audited repository, verify consistency among:

```text
GitHub repository name
↔ GitHub description
↔ GitHub topics
↔ README
↔ repo.yml
↔ CITATION.cff
↔ _quarto.yml
↔ .Rproj
↔ repository URLs
```

Legacy names should not survive after a repository rename or project-to-paper conversion.
