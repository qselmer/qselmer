# Repository type topics

This profile inventories **public original repositories owned by `qselmer`**. Forks and private repositories are excluded. Active original repositories are classified using one controlled primary `type-*` topic; archived originals remain visible only as a cleanup queue.

## Canonical types

| Topic | Visible group | Intended use |
|---|---|---|
| `type-package` | Packages | Reusable scientific software, libraries and installable packages. |
| `type-workflow` | Methods & workflows | Reproducible scientific methods, analyses and computational workflows. |
| `type-app` | Apps & dashboards | Interactive applications and web tools. |
| `type-dashboard` | Apps & dashboards | Dashboard-oriented interactive products. |
| `type-project` | Research projects | Research initiatives in development that are exploratory, incubating, collaborative, or not yet committed to one manuscript. |
| `type-paper` | Papers | Reproducibility repositories associated with one scientific manuscript or paper. |
| `type-training` | Courses & training | MOOCs, courses, workshops, worked examples and training material. |
| `type-template` | Templates | Reusable repository/project/report/manuscript scaffolds intended to be copied or instantiated. |
| `type-infrastructure` | Websites & infrastructure | Profile/site repositories and supporting technical infrastructure. |

`type-learning` is retained only as a legacy alias for `type-training`. New repositories should use `type-training`.

`type-report` is **not part of the personal-profile taxonomy**. A repository that produces a report should be classified by its actual function, for example `type-workflow` when it contains a reproducible analytical process or `type-template` when it is a reusable report scaffold.

## Project versus paper

Use `type-project` when the repository represents a research initiative rather than a committed manuscript. Typical cases include an exploratory question, an incubating research line, a collaboration-seeking project, a multi-output programme, or work for which the final scholarly product has not yet been decided.

Use `type-paper` once the repository is organized around **one defined manuscript** with a specific scientific question, analysis plan, figures/tables, manuscript files, or a reproducibility package intended to support that paper.

The normal transition is:

```text
type-project
    ↓ scientific question and manuscript become defined
type-paper
    ↓ formal scholarly output
publication record
```

A broad `type-project` may remain active after one or more paper repositories are created from it. Do not reclassify a paper repository back to `type-project` merely because the manuscript is still private, in preparation, or seeking collaborators.

## How to decide the repository type

Use the repository's **primary function**, not its subject, language or file extension:

1. **Can another user install/reuse it as software?** → `type-package`.
2. **Does it implement a reproducible analytical method or end-to-end analysis?** → `type-workflow`.
3. **Is it an exploratory/incubating research initiative without one committed manuscript?** → `type-project`.
4. **Does it reproduce/develop one scientific manuscript?** → `type-paper`.
5. **Is the main deliverable an interactive interface?** → `type-app` or `type-dashboard`.
6. **Is the main purpose teaching or skill development?** → `type-training`.
7. **Is it designed to be copied as a starting structure?** → `type-template`.
8. **Is it a website/profile/support system rather than a scientific analysis?** → `type-infrastructure`.

A repository should normally have **exactly one primary `type-*` topic**. Domain topics such as `fisheries`, `marine-ecology`, `stock-assessment`, `r`, or `python` are secondary descriptors and do not replace the repository type.

## Classification precedence used by the automation

1. Exactly one canonical `type-*` topic on the repository — authoritative.
2. A recognized legacy topic alias.
3. A temporary explicit override in `assets/data/repository-types.json`.
4. Conservative name-based inference for old repositories.
5. `Other / legacy` when no defensible classification is available or when multiple primary type topics conflict.

For repository cleanup, the goal is to migrate important repositories to rule 1 and progressively remove overrides/name inference.

`type-project` is intentionally **not inferred from repository names**. Because "project" is too generic, it must be assigned explicitly as a GitHub topic or by a temporary audited override. This prevents analytical workflows and manuscript repositories from being misclassified.

## Scope of profile statistics and inventory

The **Primary Languages**, **Repository Types** card and detailed repository portfolio use only repositories that are:

- owned by `qselmer`;
- public;
- original (not forks).

Archived originals may remain visible in the detailed cleanup inventory but are excluded from summary cards. Forks and private repository names/metadata are not rendered in the public profile.

## Manual type assignment

For portfolio cleanup, assign exactly one canonical `type-*` topic manually to every active original repository. The explicit topic takes precedence over all legacy overrides and name inference. Additional domain topics such as `fisheries`, `anchovy`, `stock-assessment`, `r`, or `spatiotemporal` are secondary and do not replace the primary repository type.

Classification provenance is retained in `assets/data/repository-catalog.json` for audit and cleanup, while the public README shows only the academic repository grouping.
