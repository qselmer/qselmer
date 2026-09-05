import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


update = load_module("scripts/update_profile.py", "update_profile")
render = load_module("scripts/render_profile.py", "render_profile")


class RepositoryClassificationTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / "assets/data/repository-types.json").read_text())

    def test_canonical_topic_wins(self):
        repo = {"name": "x-paper", "topics": ["type-workflow"]}
        self.assertEqual(update.infer_repo_type(repo, self.config), "type-workflow")

    def test_legacy_learning_topic_maps_to_training(self):
        repo = {"name": "old-course", "topics": ["type-learning"]}
        self.assertEqual(update.infer_repo_type(repo, self.config), "type-training")

    def test_override_handles_legacy_package(self):
        repo = {"name": "seasignals", "topics": []}
        self.assertEqual(update.infer_repo_type(repo, self.config), "type-package")

    def test_name_fallback_detects_paper(self):
        repo = {"name": "example-paper", "topics": []}
        self.assertEqual(update.infer_repo_type(repo, self.config), "type-paper")

    def test_name_fallback_detects_training(self):
        repo = {"name": "advanced-mooc", "topics": []}
        self.assertEqual(update.infer_repo_type(repo, self.config), "type-training")

    def test_private_fork_archived_excluded(self):
        repos = [
            {"name": "a", "private": False, "fork": False, "archived": False},
            {"name": "b", "private": True, "fork": False, "archived": False},
            {"name": "c", "private": False, "fork": True, "archived": False},
            {"name": "d", "private": False, "fork": False, "archived": True},
        ]
        selected = update.original_public_repositories(repos)
        self.assertEqual([x["name"] for x in selected], ["a"])


class ResearchOutputTests(unittest.TestCase):
    def test_journal_article_classification(self):
        self.assertEqual(update.classify_output({"type": "Journal Article"}), "Journal articles")

    def test_conference_paper_classification(self):
        self.assertEqual(update.classify_output({"type": "Conference-Paper"}), "Conference outputs")

    def test_thesis_classification(self):
        self.assertEqual(update.classify_output({"type": "Dissertation-Thesis"}), "Theses")

    def test_dataset_classification(self):
        self.assertEqual(update.classify_output({"type": "Data-Set"}), "Data & software")

    def test_output_counts(self):
        pubs = [
            {"type": "Journal Article"},
            {"type": "Conference Paper"},
            {"type": "Conference Poster"},
            {"type": "Dissertation Thesis"},
        ]
        counts = update.output_type_counts(pubs)
        self.assertEqual(counts["Journal articles"], 1)
        self.assertEqual(counts["Conference outputs"], 2)
        self.assertEqual(counts["Theses"], 1)

    def test_publishing_since(self):
        pubs = [{"year": "2026"}, {"year": "2024"}, {"year": "2025"}]
        self.assertEqual(update.publishing_since(pubs), "2024")

    def test_rendered_reference_displays_output_class(self):
        pub = {
            "type": "Conference Paper",
            "output_category": "Conference outputs",
            "title": "Example",
            "year": "2026",
            "authors": ["Elmer Quispe-Salazar"],
        }
        text = render.reference(pub, show_output_type=True)
        self.assertIn("Conference output", text)
        self.assertIn("Quispe-Salazar", text)


class ResearchMetricTests(unittest.TestCase):
    def test_openalex_matching_is_orcid_based(self):
        payload = {
            "results": [
                {"id": "A1", "orcid": "https://orcid.org/0000-0000-0000-0000"},
                {"id": "A2", "orcid": f"https://orcid.org/{update.ORCID_ID}"},
            ]
        }
        match = update._matching_openalex_author(payload)
        self.assertEqual(match["id"], "A2")

    def test_metrics_payload_uses_orcid_counts(self):
        pubs = [
            {"type": "Journal Article", "year": "2025"},
            {"type": "Conference Paper", "year": "2024"},
        ]
        payload = update.research_metrics_payload(
            pubs,
            {"available": True, "source": "OpenAlex", "cited_by_count": 4, "h_index": 1},
        )
        self.assertEqual(payload["public_orcid_works"], 2)
        self.assertEqual(payload["journal_articles"], 1)
        self.assertEqual(payload["publishing_since"], "2024")
        self.assertEqual(payload["openalex"]["cited_by_count"], 4)

class CompleteRepositoryInventoryTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / "assets/data/repository-types.json").read_text())

    def test_catalog_retains_public_forks_and_archived_for_cleanup(self):
        repos = [
            {"name": "active", "full_name": "qselmer/active", "private": False, "fork": False, "archived": False, "topics": []},
            {"name": "archived", "full_name": "qselmer/archived", "private": False, "fork": False, "archived": True, "topics": []},
            {"name": "forked", "full_name": "qselmer/forked", "private": False, "fork": True, "archived": False, "topics": []},
            {"name": "secret", "full_name": "qselmer/secret", "private": True, "fork": False, "archived": False, "topics": []},
        ]
        catalog = update.build_repository_catalog(repos)
        self.assertEqual(catalog["totals"]["public_repositories"], 3)
        self.assertEqual(catalog["totals"]["active_original_repositories"], 1)
        self.assertEqual(catalog["totals"]["archived_original_repositories"], 1)
        self.assertEqual(catalog["totals"]["forks"], 1)
        self.assertNotIn("secret", [x["name"] for x in catalog["repositories"]])

    def test_multiple_type_topics_are_exposed_as_legacy(self):
        repo = {"name": "ambiguous", "topics": ["type-paper", "type-workflow"]}
        repo_type, source = update.repository_classification(repo, self.config)
        self.assertIsNone(repo_type)
        self.assertEqual(source, "multiple-type-topics")

    def test_render_inventory_groups_active_archived_and_forks(self):
        original_load = render.load
        try:
            render.load = lambda path, default: {
                "totals": {
                    "public_repositories": 3,
                    "active_original_repositories": 1,
                    "archived_original_repositories": 1,
                    "forks": 1,
                    "other_or_legacy_active": 1,
                },
                "repositories": [
                    {"name": "legacy", "html_url": "https://github.com/qselmer/legacy", "description": "x", "language": "R", "updated_at": "2026-01-01", "fork": False, "archived": False, "repository_type_label": "Other / legacy"},
                    {"name": "old", "html_url": "https://github.com/qselmer/old", "description": "x", "language": "R", "updated_at": "2025-01-01", "fork": False, "archived": True, "repository_type_label": "Methods & workflows"},
                    {"name": "fork", "html_url": "https://github.com/qselmer/fork", "description": "x", "language": "Python", "updated_at": "2024-01-01", "fork": True, "archived": False, "repository_type_label": "Other / legacy"},
                ],
            }
            text = render.render_projects()
        finally:
            render.load = original_load
        self.assertIn("Other / legacy (1)", text)
        self.assertIn("Archived repositories (1)", text)
        self.assertIn("Forks (1)", text)
        self.assertIn("3 public repositories", text)


if __name__ == "__main__":
    unittest.main()
