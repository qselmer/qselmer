#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPDATE = ROOT / "scripts" / "update_profile.py"
MIGRATION = ROOT / "scripts" / "_migrate_profile_hierarchy_v2.py"
WORKFLOW = ROOT / ".github" / "workflows" / "profile-hierarchy-v2-migration.yml"

text = UPDATE.read_text(encoding="utf-8")

old = '''def original_public_repositories(repositories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        repo
        for repo in repositories
        if not repo.get("fork") and not repo.get("private") and not repo.get("archived")
    ]


def language_totals(repositories: list[dict[str, Any]]) -> Counter[str]:
'''
new = '''def original_public_repositories(repositories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        repo
        for repo in repositories
        if not repo.get("fork") and not repo.get("private") and not repo.get("archived")
    ]


def original_active_repositories(repositories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return active original repositories regardless of public/private visibility."""
    return [
        repo
        for repo in repositories
        if not repo.get("fork") and not repo.get("archived")
    ]


def language_totals(repositories: list[dict[str, Any]]) -> Counter[str]:
'''
if old not in text:
    raise RuntimeError("Could not locate original repository selector block")
text = text.replace(old, new, 1)

old = '''    Forks are excluded. Public and private originals are retained when the read
    token can see them. Summary cards remain based on active public originals.
'''
new = '''    Forks are excluded. Public and private originals are retained when the read
    token can see them. Language composition remains based on active public
    originals, while repository-type counts include active public and private
    originals visible to the profile automation.
'''
if old not in text:
    raise RuntimeError("Could not locate repository catalog summary-card comment")
text = text.replace(old, new, 1)

old = '''def repository_type_counts(repositories: list[dict[str, Any]]) -> Counter[str]:
    config = load_type_config()
    canonical_types = config.get("canonical_types") or {}
    counts: Counter[str] = Counter()
    for repo in original_public_repositories(repositories):
        repo_type = infer_repo_type(repo, config)
        label = canonical_types.get(repo_type, "Other / legacy")
        counts[label] += 1
    return counts
'''
new = '''def repository_type_counts(repositories: list[dict[str, Any]]) -> Counter[str]:
    """Count repository types across all active originals visible to automation."""
    config = load_type_config()
    canonical_types = config.get("canonical_types") or {}
    counts: Counter[str] = Counter()
    for repo in original_active_repositories(repositories):
        repo_type = infer_repo_type(repo, config)
        label = canonical_types.get(repo_type, "Other / legacy")
        counts[label] += 1
    return counts
'''
if old not in text:
    raise RuntimeError("Could not locate repository_type_counts")
text = text.replace(old, new, 1)

text = text.replace(
    "6. queries all public GitHub repositories owned by the user;\n7. computes language composition and repository-type counts;\n8. writes a public original-repository inventory for README tables (forks excluded);",
    "6. queries owned GitHub repositories visible to the configured credentials;\n7. computes public language composition and public/private repository-type counts;\n8. writes the original-repository inventory used by the profile renderer (forks excluded);",
    1,
)

UPDATE.write_text(text, encoding="utf-8")

# The migration artifacts remove themselves from the branch after applying the source patch.
if WORKFLOW.exists():
    WORKFLOW.unlink()
if MIGRATION.exists():
    MIGRATION.unlink()
