# Repository type topics

This profile inventories **all public repositories owned by `qselmer`**. Active original repositories are classified using a controlled `type-*` topic; archived repositories and public forks are shown separately as cleanup queues. The summary type counts use only active original public repositories.

## Canonical types

| Topic | Visible group | Intended use |
|---|---|---|
| `type-package` | Packages | Reusable scientific software, libraries and packages. |
| `type-protocol` | Protocols & manuals | Methodological protocols, manuals and standardized procedures. |
| `type-workflow` | Methods & workflows | Reproducible scientific methods, analyses and computational workflows. |
| `type-report` | Reports | Reproducible technical, assessment or monitoring reports. |
| `type-app` | Apps & dashboards | Interactive applications and web tools. |
| `type-dashboard` | Apps & dashboards | Dashboard-oriented interactive products. |
| `type-paper` | Papers | Reproducibility repositories associated with scientific papers. |
| `type-training` | Courses & training | MOOCs, courses, workshops, worked examples, training repositories and teaching material. |
| `type-infrastructure` | Websites & infrastructure | Profile/site repositories, templates and supporting infrastructure. |

`type-learning` is retained only as a legacy alias for `type-training` so older repositories continue to classify correctly. New repositories should use `type-training`.

## Classification rule

The generator uses this precedence:

1. Exactly one canonical `type-*` topic on the repository.
2. A recognized legacy topic alias.
3. An explicit legacy override in `assets/data/repository-types.json`.
4. Conservative name-based inference for old repositories.
5. `Other / legacy` when no defensible classification is available.

New repositories should use a canonical topic rather than relying on an override or name inference.

## Scope of the profile statistics and inventory

Only repositories that are all of the following are included in the **Primary Languages** and **Repository Types** summary cards:

- owned by `qselmer`;
- public;
- not forks;
- not archived.

The detailed README inventory is broader: it lists every **public** repository owned by `qselmer`, including archived repositories and public forks. Those are placed in separate sections so they can be reviewed and cleaned. Private repository names and metadata are never published by the profile automation.
