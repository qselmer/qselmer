#!/usr/bin/env python3
"""Read and validate per-repository ``repo.yml`` contracts.

This module keeps repository identity/lifecycle metadata separate from the
profile renderer. It deliberately exposes only a compact normalized contract;
callers remain responsible for redacting private-repository metadata before
writing public artifacts.
"""

from __future__ import annotations

import base64
import binascii
import urllib.error
from typing import Any, Callable

import yaml

EXPECTED_SCHEMA_VERSION = 2


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def empty_contract() -> dict[str, Any]:
    return {
        "present": False,
        "valid": False,
        "schema_version": None,
        "repository_type": "",
        "status": "",
        "stage": "",
        "visibility": "",
        "description": "",
        "topics": [],
        "profile_include": True,
        "target_outputs": [],
        "branding": {},
        "relations": {},
        "issues": [],
    }


def parse_repository_contract(
    text: str,
    repo: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Parse and validate one ``repo.yml`` document.

    ``valid`` refers to the contract structure itself. GitHub-topic hygiene is
    reported separately in ``issues`` and does not prevent ``repo.yml`` from
    being the authoritative classification source.
    """
    contract = empty_contract()
    contract["present"] = True
    structural_issues: list[str] = []

    try:
        payload = yaml.safe_load(text)
    except yaml.YAMLError:
        contract["issues"] = ["repo_yml_invalid_yaml"]
        return contract

    if not isinstance(payload, dict):
        contract["issues"] = ["repo_yml_root_not_mapping"]
        return contract

    schema_version = payload.get("schema_version")
    contract["schema_version"] = schema_version
    if schema_version != EXPECTED_SCHEMA_VERSION:
        structural_issues.append("repo_yml_schema_version")

    repository = _mapping(payload.get("repository"))
    if not repository:
        structural_issues.append("repo_yml_missing_repository")

    canonical_types = _mapping(config.get("canonical_types"))
    repository_type = _text(repository.get("type"))
    contract["repository_type"] = repository_type
    if not repository_type:
        structural_issues.append("repo_yml_missing_type")
    elif repository_type not in canonical_types:
        structural_issues.append("repo_yml_noncanonical_type")

    status = _text(repository.get("status"))
    stage = _text(repository.get("stage"))
    contract["status"] = status
    contract["stage"] = stage
    if not status:
        structural_issues.append("repo_yml_missing_status")
    if not stage:
        structural_issues.append("repo_yml_missing_stage")

    visibility = _text(repository.get("visibility"))
    contract["visibility"] = visibility
    if not visibility:
        structural_issues.append("repo_yml_missing_visibility")

    expected_owner = _text((_mapping(repo.get("owner"))).get("login"))
    expected_name = _text(repo.get("name"))
    contract_owner = _text(repository.get("owner"))
    contract_name = _text(repository.get("name"))
    if contract_owner and expected_owner and contract_owner.casefold() != expected_owner.casefold():
        structural_issues.append("repo_yml_owner_mismatch")
    if contract_name and expected_name and contract_name != expected_name:
        structural_issues.append("repo_yml_name_mismatch")

    expected_visibility = "private" if bool(repo.get("private")) else "public"
    if visibility and visibility not in {"public", "private"}:
        structural_issues.append("repo_yml_invalid_visibility")
    elif visibility and visibility != expected_visibility:
        structural_issues.append("repo_yml_visibility_mismatch")

    contract["description"] = _text(repository.get("description"))
    contract_topics = _string_list(repository.get("topics"))
    contract["topics"] = contract_topics
    contract_type_topics = [topic for topic in contract_topics if topic.startswith("type-")]
    if len(contract_type_topics) == 0:
        structural_issues.append("repo_yml_missing_type_topic")
    elif len(contract_type_topics) > 1:
        structural_issues.append("repo_yml_multiple_type_topics")
    elif repository_type and contract_type_topics[0] != repository_type:
        structural_issues.append("repo_yml_type_topic_mismatch")

    integration = _mapping(payload.get("integration"))
    profile = _mapping(integration.get("profile"))
    include = profile.get("include", True)
    if not isinstance(include, bool):
        structural_issues.append("repo_yml_profile_include_not_boolean")
        include = True
    contract["profile_include"] = include

    target_outputs = repository.get("target_outputs", payload.get("target_outputs", []))
    if isinstance(target_outputs, list):
        contract["target_outputs"] = target_outputs
    elif target_outputs not in (None, ""):
        structural_issues.append("repo_yml_target_outputs_not_list")

    branding = repository.get("branding", payload.get("branding", {}))
    if isinstance(branding, dict):
        contract["branding"] = branding
    elif branding not in (None, ""):
        structural_issues.append("repo_yml_branding_not_mapping")

    relations = payload.get("relations", repository.get("relations", {}))
    if isinstance(relations, dict):
        contract["relations"] = relations
    elif relations not in (None, ""):
        structural_issues.append("repo_yml_relations_not_mapping")

    contract["valid"] = not structural_issues
    contract["issues"] = structural_issues
    return contract


def github_topic_issues(
    repo: dict[str, Any],
    config: dict[str, Any],
    contract: dict[str, Any],
) -> list[str]:
    """Return GitHub-topic consistency issues for the normalized contract."""
    canonical_types = _mapping(config.get("canonical_types"))
    topics = _string_list(repo.get("topics"))
    type_topics = [topic for topic in topics if topic.startswith("type-")]

    issues: list[str] = []
    if not type_topics:
        issues.append("github_missing_type_topic")
        return issues
    if len(type_topics) > 1:
        issues.append("github_multiple_type_topics")
        return issues

    topic = type_topics[0]
    if topic not in canonical_types:
        issues.append("github_noncanonical_type_topic")
        return issues

    contract_type = _text(contract.get("repository_type"))
    if contract.get("valid") and contract_type and topic != contract_type:
        issues.append("classification_conflict")
    return issues


def fetch_repository_contract(
    repo: dict[str, Any],
    config: dict[str, Any],
    github_json: Callable[[str, str | None], Any],
    token: str | None,
) -> dict[str, Any]:
    """Fetch ``repo.yml`` through the GitHub contents API and normalize it."""
    full_name = _text(repo.get("full_name"))
    if not full_name:
        contract = empty_contract()
        contract["issues"] = ["repo_missing_full_name"]
        return contract

    try:
        payload = github_json(f"/repos/{full_name}/contents/repo.yml", token)
    except urllib.error.HTTPError as exc:
        contract = empty_contract()
        if exc.code == 404:
            contract["issues"] = ["repo_yml_missing"]
            return contract
        contract["issues"] = [f"repo_yml_http_{exc.code}"]
        return contract
    except (urllib.error.URLError, TimeoutError, ValueError):
        contract = empty_contract()
        contract["issues"] = ["repo_yml_fetch_error"]
        return contract

    if not isinstance(payload, dict):
        contract = empty_contract()
        contract["present"] = True
        contract["issues"] = ["repo_yml_invalid_api_payload"]
        return contract

    encoded = _text(payload.get("content")).replace("\n", "")
    encoding = _text(payload.get("encoding")).casefold()
    try:
        if encoding == "base64":
            text = base64.b64decode(encoded).decode("utf-8")
        else:
            text = encoded
    except (binascii.Error, UnicodeDecodeError):
        contract = empty_contract()
        contract["present"] = True
        contract["issues"] = ["repo_yml_decode_error"]
        return contract

    contract = parse_repository_contract(text, repo, config)
    contract["issues"] = list(contract.get("issues") or []) + github_topic_issues(repo, config, contract)
    return contract
