import importlib.util
import json
import pathlib

from scripts import repository_contracts as contracts

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "assets/data/repository-types.json").read_text())


def load_update_module():
    spec = importlib.util.spec_from_file_location("update_profile_contract_tests", ROOT / "scripts/update_profile.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def public_repo(**overrides):
    repo = {
        "name": "example-paper",
        "full_name": "qselmer/example-paper",
        "owner": {"login": "qselmer"},
        "private": False,
        "fork": False,
        "archived": False,
        "topics": ["type-paper", "fisheries"],
        "description": "GitHub description",
        "language": "R",
        "html_url": "https://github.com/qselmer/example-paper",
        "updated_at": "2026-09-11T00:00:00Z",
    }
    repo.update(overrides)
    return repo


def valid_contract_text(include="true"):
    return f"""schema_version: 2
repository:
  owner: qselmer
  name: example-paper
  title: Example paper
  type: type-paper
  status: active
  stage: analysis
  visibility: public
  description: Contract description
  topics:
    - type-paper
    - fisheries
integration:
  profile:
    include: {include}
"""


def test_valid_repo_yml_is_normalized():
    contract = contracts.parse_repository_contract(valid_contract_text(), public_repo(), CONFIG)
    assert contract["valid"] is True
    assert contract["repository_type"] == "type-paper"
    assert contract["status"] == "active"
    assert contract["stage"] == "analysis"
    assert contract["profile_include"] is True
    assert contract["issues"] == []


def test_github_topic_mismatch_is_explicit_conflict_not_silent_reclassification():
    repo = public_repo(topics=["type-workflow"])
    contract = contracts.parse_repository_contract(valid_contract_text(), repo, CONFIG)
    issues = contracts.github_topic_issues(repo, CONFIG, contract)
    assert contract["valid"] is True
    assert "classification_conflict" in issues


def test_missing_github_type_topic_is_reported():
    repo = public_repo(topics=["fisheries"])
    contract = contracts.parse_repository_contract(valid_contract_text(), repo, CONFIG)
    assert contracts.github_topic_issues(repo, CONFIG, contract) == ["github_missing_type_topic"]


def test_invalid_schema_is_not_a_valid_contract():
    text = valid_contract_text().replace("schema_version: 2", "schema_version: 1")
    contract = contracts.parse_repository_contract(text, public_repo(), CONFIG)
    assert contract["valid"] is False
    assert "repo_yml_schema_version" in contract["issues"]


def test_repo_yml_classification_precedes_legacy_rules():
    update = load_update_module()
    repo = public_repo(name="misleading-workflow", topics=["type-workflow"])
    contract = contracts.parse_repository_contract(valid_contract_text(), public_repo(), CONFIG)
    repo_type, source = update.repository_classification(repo, CONFIG, contract)
    assert repo_type == "type-paper"
    assert source == "repo.yml"


def test_private_catalog_redacts_sensitive_metadata():
    update = load_update_module()
    repo = public_repo(
        private=True,
        topics=["type-paper", "confidential-topic"],
        description="Confidential description",
        language="Python",
    )
    contract = contracts.parse_repository_contract(
        valid_contract_text().replace("visibility: public", "visibility: private"),
        {**repo, "name": "example-paper"},
        CONFIG,
    )
    contract["issues"].append("github_missing_type_topic")
    update.fetch_repository_contract = lambda *args, **kwargs: contract
    catalog = update.build_repository_catalog([repo])
    item = catalog["repositories"][0]
    assert item["repository_type"] == "type-paper"
    assert item["description"] == ""
    assert item["language"] == "-"
    assert item["topics"] == []
    assert item["status"] == ""
    assert item["stage"] == ""
    assert item["contract_issues"] == []
    assert item["contract_issue_count"] >= 1


def test_profile_include_false_excludes_type_count():
    update = load_update_module()
    repo = public_repo()
    contract = contracts.parse_repository_contract(valid_contract_text(include="false"), repo, CONFIG)
    update.fetch_repository_contract = lambda *args, **kwargs: contract
    catalog = update.build_repository_catalog([repo])
    assert catalog["repositories"][0]["profile_include"] is False
    counts = update.repository_type_counts(catalog)
    assert counts.get("Papers", 0) == 0
