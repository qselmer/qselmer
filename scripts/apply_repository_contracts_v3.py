#!/usr/bin/env python3
"""One-off migration for canonical repo.yml ingestion. Removed after use."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def write(path, text):
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError(f"missing patch anchor: {label}")
    return text.replace(old, new, 1)


# --- scripts/update_profile.py -------------------------------------------------
path = "scripts/update_profile.py"
text = read(path)
text = replace_once(
    text,
    "The script intentionally uses only the Python standard library. It:\n",
    "The profile refresh uses the Python standard library plus PyYAML for validated repository contracts. It:\n",
    "update_profile docstring",
)
text = replace_once(
    text,
    "from typing import Any\n",
    "from typing import Any\n\ntry:\n    from repository_contracts import fetch_repository_contract\nexcept ModuleNotFoundError:  # imported by tests from the repository root\n    from scripts.repository_contracts import fetch_repository_contract\n",
    "repository contract import",
)

classification = '''def repository_classification(
    repo: dict[str, Any],
    config: dict[str, Any],
    contract: dict[str, Any] | None = None,
) -> tuple[str | None, str]:
    """Return canonical repository type plus the rule used to classify it.

    A valid ``repo.yml`` is authoritative. If no contract is present, legacy
    topic/override/name rules remain as a temporary migration fallback. An
    invalid existing contract is never silently bypassed.
    """
    canonical_types = config.get("canonical_types") or {}

    if contract is not None and contract.get("present"):
        repo_type = str(contract.get("repository_type") or "")
        if contract.get("valid") and repo_type in canonical_types:
            return repo_type, "repo.yml"
        return None, "repo.yml-invalid"

    aliases = config.get("legacy_type_aliases") or {}
    overrides = config.get("overrides") or {}
    topics = [str(x) for x in (repo.get("topics") or [])]

    canonical_hits = list(dict.fromkeys(topic for topic in topics if topic in canonical_types))
    alias_hits = list(dict.fromkeys(aliases[topic] for topic in topics if topic in aliases))
    hits = list(dict.fromkeys(canonical_hits + alias_hits))
    if len(hits) == 1:
        source = "topic" if canonical_hits else "legacy-topic"
        return hits[0], source
    if len(hits) > 1:
        return None, "multiple-type-topics"

    name = str(repo.get("name") or "")
    if name in overrides:
        override = str(overrides[name])
        if override in canonical_types:
            return override, "override"

    for pattern, repo_type in NAME_FALLBACKS:
        if pattern.search(name):
            return repo_type, "name-inference"
    return None, "unclassified"


'''
text, n = re.subn(
    r"def repository_classification\(.*?\n\ndef build_repository_catalog",
    classification + "def build_repository_catalog",
    text,
    count=1,
    flags=re.S,
)
if n != 1:
    raise RuntimeError("could not replace repository_classification")

catalog = '''def build_repository_catalog(repositories: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the public-safe inventory of original repositories.

    ``repo.yml`` is the principal machine-readable contract when present.
    Missing contracts temporarily fall back to legacy classification rules.
    Private repositories retain only the minimum metadata needed for counts and
    the visible lock-marked portfolio; sensitive descriptive metadata is
    redacted before this public JSON artifact is written.
    """
    config = load_type_config()
    canonical_types = config.get("canonical_types") or {}
    items: list[dict[str, Any]] = []
    contract_token = PROFILE_REPO_TOKEN or GITHUB_TOKEN or None

    for repo in repositories:
        if repo.get("fork"):
            continue

        contract = fetch_repository_contract(repo, config, github_json, contract_token)
        repo_type, source = repository_classification(repo, config, contract)
        label = canonical_types.get(repo_type, "Other / legacy")
        private = bool(repo.get("private"))
        contract_valid = bool(contract.get("valid"))
        profile_include = bool(contract.get("profile_include", True)) if contract_valid else True
        status = str(contract.get("status") or "") if contract_valid else ""
        stage = str(contract.get("stage") or "") if contract_valid else ""
        active = not bool(repo.get("archived")) and status.casefold() != "archived"
        issues = [str(x) for x in (contract.get("issues") or [])]

        description = ""
        language = "-"
        topics: list[str] = []
        updated_at = ""
        public_status = ""
        public_stage = ""
        contract_issues: list[str] = []
        target_outputs: list[Any] = []
        branding: dict[str, Any] = {}
        relations: dict[str, Any] = {}

        if not private:
            description = (
                str(contract.get("description") or "").strip()
                if contract_valid and contract.get("description")
                else safe_text(repo.get("description"))
            )
            language = safe_text(repo.get("language")) or "-"
            topics = [str(x) for x in (repo.get("topics") or [])]
            updated_at = safe_text(repo.get("updated_at"))
            public_status = status
            public_stage = stage
            contract_issues = issues
            if contract_valid:
                target_outputs = list(contract.get("target_outputs") or [])
                branding = dict(contract.get("branding") or {})
                relations = dict(contract.get("relations") or {})

        item = {
            "name": safe_text(repo.get("name")),
            "full_name": safe_text(repo.get("full_name")),
            "html_url": safe_text(repo.get("html_url")),
            "description": description,
            "language": language,
            "updated_at": updated_at,
            "archived": bool(repo.get("archived")),
            "active": active,
            "private": private,
            "visibility": "private" if private else "public",
            "fork": False,
            "profile_include": profile_include,
            "repository_type": repo_type or "",
            "repository_type_label": label,
            "classification_source": source,
            "status": public_status,
            "stage": public_stage,
            "topics": topics,
            "contract_present": bool(contract.get("present")),
            "contract_valid": contract_valid,
            "contract_schema_version": contract.get("schema_version") if not private else None,
            "contract_issue_count": len(issues),
            "contract_issues": contract_issues,
            "target_outputs": target_outputs,
            "branding": branding,
            "relations": relations,
        }
        items.append(item)

    items.sort(
        key=lambda x: (
            not x.get("profile_include", True),
            not x.get("active", False),
            x.get("repository_type_label", ""),
            x.get("private", False),
            x.get("name", "").casefold(),
        )
    )
    included = [x for x in items if x.get("profile_include", True)]
    active = [x for x in included if x.get("active", False)]
    archived = [x for x in included if not x.get("active", False)]
    public_items = [x for x in items if not x["private"]]
    private_items = [x for x in items if x["private"]]
    active_public = [x for x in active if not x["private"]]
    active_private = [x for x in active if x["private"]]
    other_legacy = [x for x in active if x["repository_type_label"] == "Other / legacy"]
    manual_topic = [x for x in active if x["classification_source"] == "topic"]

    return {
        "schema_version": 3,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "owner": GITHUB_USER,
        "scope": (
            "all original repositories visible to PROFILE_REPO_TOKEN; forks excluded; private metadata redacted"
            if INCLUDE_PRIVATE_REPOS and PROFILE_REPO_TOKEN
            else "public original repositories only; forks excluded"
        ),
        "classification_precedence": [
            "repo.yml",
            "canonical GitHub type topic",
            "legacy type alias",
            "temporary audited override",
            "conservative name inference",
            "unclassified",
        ],
        "totals": {
            "repositories": len(items),
            "public_repositories": len(public_items),
            "private_repositories": len(private_items),
            "active_original_repositories": len(active),
            "active_public_original_repositories": len(active_public),
            "active_private_original_repositories": len(active_private),
            "archived_original_repositories": len(archived),
            "profile_excluded_repositories": len([x for x in items if not x.get("profile_include", True)]),
            "contracts_present": len([x for x in items if x.get("contract_present")]),
            "contracts_valid": len([x for x in items if x.get("contract_valid")]),
            "contract_issues": sum(int(x.get("contract_issue_count", 0)) for x in items),
            "other_or_legacy_active": len(other_legacy),
            "manual_type_topics_active": len(manual_topic),
        },
        "repositories": items,
    }


'''
text, n = re.subn(
    r"def build_repository_catalog\(.*?\n\ndef write_repository_catalog",
    catalog + "def write_repository_catalog",
    text,
    count=1,
    flags=re.S,
)
if n != 1:
    raise RuntimeError("could not replace build_repository_catalog")

counts = '''def repository_type_counts(source: Any) -> Counter[str]:
    """Count profile-included active repository types.

    Catalog payloads use repo.yml-aware classification. A raw repository list is
    still accepted for backward-compatible unit tests and legacy callers.
    """
    counts: Counter[str] = Counter()
    if isinstance(source, dict) and isinstance(source.get("repositories"), list):
        for item in source["repositories"]:
            if not item.get("profile_include", True) or not item.get("active", not item.get("archived")):
                continue
            counts[str(item.get("repository_type_label") or "Other / legacy")] += 1
        return counts

    repositories = source if isinstance(source, list) else []
    config = load_type_config()
    canonical_types = config.get("canonical_types") or {}
    for repo in original_active_repositories(repositories):
        repo_type = infer_repo_type(repo, config)
        label = canonical_types.get(repo_type, "Other / legacy")
        counts[label] += 1
    return counts


'''
text, n = re.subn(
    r"def repository_type_counts\(.*?\n\ndef svg_escape",
    counts + "def svg_escape",
    text,
    count=1,
    flags=re.S,
)
if n != 1:
    raise RuntimeError("could not replace repository_type_counts")

text = replace_once(
    text,
    "    write_repository_catalog(repositories)\n",
    "    catalog = write_repository_catalog(repositories)\n",
    "catalog assignment",
)
text = replace_once(
    text,
    "    type_counts = repository_type_counts(repositories)\n",
    "    type_counts = repository_type_counts(catalog)\n",
    "catalog type counts",
)
write(path, text)


# --- scripts/render_profile.py -------------------------------------------------
path = "scripts/render_profile.py"
text = read(path)
text = replace_once(
    text,
    '    "archived repositories are excluded.</sub>"\n',
    '    "archived repositories and repositories with profile.include=false are excluded.</sub>"\n',
    "portfolio note",
)
text = replace_once(
    text,
    '    active = [repo for repo in repositories if not repo.get("archived")]\n    archived = [repo for repo in repositories if repo.get("archived")]\n',
    '    included = [repo for repo in repositories if repo.get("profile_include", True)]\n    active = [repo for repo in included if repo.get("active", not repo.get("archived"))]\n    archived = [repo for repo in included if not repo.get("active", not repo.get("archived"))]\n',
    "renderer profile include",
)
write(path, text)


# --- .github/workflows/update-profile.yml -------------------------------------
path = ".github/workflows/update-profile.yml"
text = read(path)
text = replace_once(
    text,
    '      - "scripts/update_profile.py"\n',
    '      - "scripts/update_profile.py"\n      - "scripts/repository_contracts.py"\n      - "requirements-profile.txt"\n      - "repo.yml"\n',
    "workflow paths",
)
text = replace_once(
    text,
    '      - name: Refresh scholarly outputs, research metrics and repository portfolio\n',
    '      - name: Install profile dependencies\n        run: python -m pip install --disable-pip-version-check -r requirements-profile.txt\n\n      - name: Refresh scholarly outputs, research metrics and repository portfolio\n',
    "workflow dependency install",
)
text = replace_once(
    text,
    '          python -m py_compile scripts/update_profile.py scripts/render_profile.py\n',
    '          python -m py_compile scripts/update_profile.py scripts/render_profile.py scripts/repository_contracts.py\n',
    "workflow compile",
)
write(path, text)


# --- AUTOMATION.md -------------------------------------------------------------
path = "AUTOMATION.md"
text = read(path)
old = '''## Repository inventory and types

Original repositories owned by `qselmer` are written to `assets/data/repository-catalog.json`. When the read token can see private repositories, the canonical catalog retains both public and private originals; forks are excluded.

The public README is deliberately narrower than the canonical catalog:

- **Primary Languages** uses active public original repositories only.
- **Repository Types** counts active public and private original repositories visible to the profile automation.
- Detailed repository tables list active public and private originals.
- Private repositories are marked with 🔒; their descriptions and language metadata are suppressed in the public README.
- Archived repositories are excluded from the two summary cards and from the active portfolio groups.

New repositories should have one canonical primary `type-*` topic. See `TOPICS.md`. Repositories without a defensible type remain an internal cleanup category in `repository-catalog.json`; they are not rendered as an `Other / legacy` section in the public README.
'''
new = '''## Repository inventory and types

Original repositories owned by `qselmer` are written to `assets/data/repository-catalog.json`; forks are excluded. A root `repo.yml` (schema version 2) is the principal machine-readable contract for repository identity, lifecycle state and profile inclusion.

Classification precedence is deliberately explicit:

1. valid `repo.yml`;
2. one canonical GitHub `type-*` topic when `repo.yml` is absent;
3. legacy topic alias;
4. temporary audited override;
5. conservative name inference;
6. unclassified cleanup state.

If `repo.yml` exists but is invalid, the automation does not silently bypass it. If its canonical type disagrees with the GitHub `type-*` topic, the contract remains authoritative and the catalog records a `classification_conflict` hygiene issue. Repositories with `integration.profile.include: false` remain in the inventory but are excluded from public portfolio groups and repository-type summary counts.

The public catalog is privacy-filtered before it is committed:

- **Primary Languages** uses active public original repositories only.
- **Repository Types** counts active, profile-included public and private originals visible to the automation.
- Public repositories can expose contract status/stage, topics and other non-sensitive contract metadata.
- Private repositories retain only the minimum fields needed for identity, visibility and aggregate counts; description, language, topics, lifecycle detail, relations and other contract metadata are redacted from the public JSON as well as the README.
- Archived repositories and `profile.include: false` repositories are excluded from active portfolio groups.

Every audited repository should converge on exactly one canonical GitHub `type-*` topic agreeing with `repository.type` in `repo.yml`. See `TOPICS.md`.
'''
text = replace_once(text, old, new, "automation inventory section")
text = replace_once(
    text,
    "The private inventory supports complete repository-type counts and the visible portfolio. Private repository names are rendered with 🔒, while descriptions, language and other sensitive metadata remain suppressed in the public README.\n",
    "The private inventory supports complete repository-type counts and the visible portfolio. Private repository names are rendered with 🔒; sensitive metadata are redacted before `repository-catalog.json` is committed, so the public data artifact and README follow the same privacy boundary.\n",
    "automation privacy statement",
)
write(path, text)

print("repository contract migration applied")
