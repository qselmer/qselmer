#!/usr/bin/env python3
"""Canonical profile-refresh entrypoint.

The existing ``update_profile.py`` remains the scholarly-metrics engine. This
entrypoint installs the repository-contract layer before running that engine so
repository identity, lifecycle and profile inclusion come from ``repo.yml``
when available.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from typing import Any

try:
    import update_profile as core
except ModuleNotFoundError:  # imported from repository-root unit tests
    from scripts import update_profile as core

try:
    from repository_contracts import fetch_repository_contract
except ModuleNotFoundError:  # imported from repository-root unit tests
    from scripts.repository_contracts import fetch_repository_contract

_LAST_CATALOG: dict[str, Any] | None = None


def repository_classification(
    repo: dict[str, Any],
    config: dict[str, Any],
    contract: dict[str, Any] | None = None,
) -> tuple[str | None, str]:
    """Classify a repository with ``repo.yml`` as the principal contract."""
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
        return hits[0], "topic" if canonical_hits else "legacy-topic"
    if len(hits) > 1:
        return None, "multiple-type-topics"

    name = str(repo.get("name") or "")
    if name in overrides:
        override = str(overrides[name])
        if override in canonical_types:
            return override, "override"

    for pattern, repo_type in core.NAME_FALLBACKS:
        if pattern.search(name):
            return repo_type, "name-inference"
    return None, "unclassified"


def _contract_for(repo: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    token = core.PROFILE_REPO_TOKEN or core.GITHUB_TOKEN or None
    return fetch_repository_contract(repo, config, core.github_json, token)


def build_repository_catalog(repositories: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a repo.yml-aware, privacy-filtered public repository catalog."""
    config = core.load_type_config()
    canonical_types = config.get("canonical_types") or {}
    items: list[dict[str, Any]] = []

    for repo in repositories:
        if repo.get("fork"):
            continue

        contract = _contract_for(repo, config)
        repo_type, source = repository_classification(repo, config, contract)
        label = canonical_types.get(repo_type, "Other / legacy")
        private = bool(repo.get("private"))
        contract_valid = bool(contract.get("valid"))
        profile_include = bool(contract.get("profile_include", True)) if contract_valid else True
        status = str(contract.get("status") or "") if contract_valid else ""
        stage = str(contract.get("stage") or "") if contract_valid else ""
        active = not bool(repo.get("archived")) and status.casefold() != "archived"
        issues = [str(x) for x in (contract.get("issues") or [])]

        if private:
            description = ""
            language = "-"
            topics: list[str] = []
            updated_at = ""
            public_status = ""
            public_stage = ""
            public_issues: list[str] = []
            target_outputs: list[Any] = []
            branding: dict[str, Any] = {}
            relations: dict[str, Any] = {}
            schema_version = None
        else:
            description = (
                str(contract.get("description") or "").strip()
                if contract_valid and contract.get("description")
                else core.safe_text(repo.get("description"))
            )
            language = core.safe_text(repo.get("language")) or "-"
            topics = [str(x) for x in (repo.get("topics") or [])]
            updated_at = core.safe_text(repo.get("updated_at"))
            public_status = status
            public_stage = stage
            public_issues = issues
            target_outputs = list(contract.get("target_outputs") or []) if contract_valid else []
            branding = dict(contract.get("branding") or {}) if contract_valid else {}
            relations = dict(contract.get("relations") or {}) if contract_valid else {}
            schema_version = contract.get("schema_version")

        items.append(
            {
                "name": core.safe_text(repo.get("name")),
                "full_name": core.safe_text(repo.get("full_name")),
                "html_url": core.safe_text(repo.get("html_url")),
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
                "contract_schema_version": schema_version,
                "contract_issue_count": len(issues),
                "contract_issues": public_issues,
                "target_outputs": target_outputs,
                "branding": branding,
                "relations": relations,
            }
        )

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
        "owner": core.GITHUB_USER,
        "scope": (
            "all original repositories visible to PROFILE_REPO_TOKEN; forks excluded; private metadata redacted"
            if core.INCLUDE_PRIVATE_REPOS and core.PROFILE_REPO_TOKEN
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


def write_repository_catalog(repositories: list[dict[str, Any]]) -> dict[str, Any]:
    global _LAST_CATALOG
    payload = build_repository_catalog(repositories)
    core.REPOSITORY_CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    core.REPOSITORY_CATALOG_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    _LAST_CATALOG = payload
    return payload


def repository_type_counts(source: Any) -> Counter[str]:
    """Count active, profile-included repositories from the canonical catalog."""
    if isinstance(source, dict) and isinstance(source.get("repositories"), list):
        catalog = source
    elif _LAST_CATALOG is not None:
        catalog = _LAST_CATALOG
    elif isinstance(source, list):
        catalog = build_repository_catalog(source)
    else:
        catalog = {"repositories": []}

    counts: Counter[str] = Counter()
    for item in catalog.get("repositories") or []:
        if not item.get("profile_include", True):
            continue
        if not item.get("active", not item.get("archived")):
            continue
        counts[str(item.get("repository_type_label") or "Other / legacy")] += 1
    return counts


def install_repository_contracts() -> None:
    core.repository_classification = repository_classification
    core.infer_repo_type = lambda repo, config: repository_classification(repo, config)[0]
    core.build_repository_catalog = build_repository_catalog
    core.write_repository_catalog = write_repository_catalog
    core.repository_type_counts = repository_type_counts


def main() -> int:
    install_repository_contracts()
    return core.main()


if __name__ == "__main__":
    raise SystemExit(main())
