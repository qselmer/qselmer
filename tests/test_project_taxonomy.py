import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_update_module():
    spec = importlib.util.spec_from_file_location("update_profile_project_taxonomy", ROOT / "scripts/update_profile.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_type_project_is_canonical_and_distinct_from_paper():
    config = json.loads((ROOT / "assets/data/repository-types.json").read_text())
    assert config["canonical_types"]["type-project"] == "Research projects"
    assert config["canonical_types"]["type-paper"] == "Papers"
    assert config["canonical_types"]["type-project"] != config["canonical_types"]["type-paper"]


def test_explicit_project_topic_is_classified_by_automation():
    update = load_update_module()
    config = json.loads((ROOT / "assets/data/repository-types.json").read_text())
    repo = {"name": "collaborative-research", "topics": ["type-project"]}
    repo_type, source = update.repository_classification(repo, config)
    assert repo_type == "type-project"
    assert source == "topic"


def test_project_is_not_inferred_from_generic_name():
    update = load_update_module()
    config = json.loads((ROOT / "assets/data/repository-types.json").read_text())
    repo = {"name": "example-project", "topics": []}
    repo_type, source = update.repository_classification(repo, config)
    assert repo_type is None
    assert source == "unclassified"
