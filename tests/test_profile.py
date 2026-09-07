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

    def test_name_fallback_detects_template(self):
        repo = {"name": "template-analysis", "topics": []}
        self.assertEqual(update.infer_repo_type(repo, self.config), "type-template")

    def test_protocol_is_not_a_personal_repository_type(self):
        self.assertNotIn("type-protocol", self.config.get("canonical_types", {}))
        self.assertNotIn("Protocols & manuals", update.VISIBLE_TYPE_ORDER)
        self.assertNotIn("Protocols & manuals", render.VISIBLE_TYPE_ORDER)

    def test_report_is_not_a_personal_repository_type(self):
        repo = {"name": "annual-report", "topics": ["type-report"]}
        repo_type, source = update.repository_classification(repo, self.config)
        self.assertIsNone(repo_type)
        self.assertEqual(source, "unclassified")

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

    def test_summary_output_card_uses_six_specific_classes(self):
        self.assertEqual(
            update.SUMMARY_OUTPUT_TYPE_ORDER,
            [
                "Journal articles",
                "Books & chapters",
                "Theses",
                "Conference outputs",
                "Reports & technical outputs",
                "Data & software",
            ],
        )
        self.assertNotIn("Preprints & working papers", update.SUMMARY_OUTPUT_TYPE_ORDER)
        self.assertNotIn("Other research outputs", update.SUMMARY_OUTPUT_TYPE_ORDER)

    def test_unknown_output_renders_specific_source_type(self):
        original_load = render.load
        try:
            render.load = lambda path, default: {
                "publications": [
                    {
                        "type": "Research Technique",
                        "output_category": "Other research outputs",
                        "title": "Specific work",
                        "year": "2026",
                        "authors": ["Elmer Quispe-Salazar"],
                    }
                ]
            }
            text = render.render_publications()
        finally:
            render.load = original_load
        self.assertIn("### Research Technique", text)
        self.assertNotIn("### Other research outputs", text)

    def test_research_outputs_group_by_type_without_icons(self):
        original_load = render.load
        try:
            render.load = lambda path, default: {
                "publications": [
                    {"type": "Conference Paper", "output_category": "Conference outputs", "title": "Conference work", "year": "2026", "authors": ["Elmer Quispe-Salazar"]},
                    {"type": "Journal Article", "output_category": "Journal articles", "title": "Article", "year": "2025", "authors": ["Elmer Quispe-Salazar"]},
                ]
            }
            text = render.render_publications()
        finally:
            render.load = original_load
        self.assertLess(text.index("### Journal articles"), text.index("### Conference contributions"))
        self.assertNotIn("🏛️", text)
        self.assertNotIn("📄", text)
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


    def test_openalex_doi_fallback_uses_exact_orcid_work_authorship(self):
        original_request = update.request_json
        try:
            def fake_request(url, headers=None):
                if "/authors/A123" in url:
                    return {
                        "id": "https://openalex.org/A123",
                        "display_name": "Elmer Quispe-Salazar",
                        "works_count": 2,
                        "cited_by_count": 7,
                        "summary_stats": {"h_index": 2, "i10_index": 0},
                    }
                if "/authors/orcid:" in url or "/authors?" in url:
                    return {"results": []}
                if "/works?" in url:
                    return {
                        "results": [
                            {
                                "authorships": [
                                    {"author": {"id": "https://openalex.org/A123", "display_name": "Elmer Quispe-Salazar"}},
                                    {"author": {"id": "https://openalex.org/A999", "display_name": "Someone Else"}},
                                ]
                            }
                        ]
                    }
                raise AssertionError(url)
            update.request_json = fake_request
            metrics = update.openalex_author_metrics([{
                "doi": "10.3989/scimar.05636.117",
                "title": "Exact ORCID work",
            }])
        finally:
            update.request_json = original_request
        self.assertTrue(metrics["available"])
        self.assertEqual(metrics["resolution"], "doi-authorship")
        self.assertEqual(metrics["cited_by_count"], 7)
        self.assertEqual(metrics["h_index"], 2)

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



class ReadmePresentationTests(unittest.TestCase):
    def test_academic_website_badge_removed_but_site_kept_in_contact_line(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("Academic_Website", text)
        self.assertIn("qselmer.github.io</strong>", text)

    def test_research_cards_have_equal_six_row_layout(self):
        outputs = (ROOT / "assets/generated/research-outputs.svg").read_text(encoding="utf-8")
        metrics = (ROOT / "assets/generated/research-metrics.svg").read_text(encoding="utf-8")
        self.assertEqual(outputs.count('class="label"'), 6)
        self.assertEqual(metrics.count('class="label"'), 6)
        self.assertIn('height="246"', outputs)
        self.assertIn('height="246"', metrics)


class CompleteRepositoryInventoryTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / "assets/data/repository-types.json").read_text())

    def test_catalog_excludes_forks_and_retains_public_private_originals(self):
        repos = [
            {"name": "active", "full_name": "qselmer/active", "private": False, "fork": False, "archived": False, "topics": []},
            {"name": "archived", "full_name": "qselmer/archived", "private": False, "fork": False, "archived": True, "topics": []},
            {"name": "forked", "full_name": "qselmer/forked", "private": False, "fork": True, "archived": False, "topics": []},
            {"name": "secret", "full_name": "qselmer/secret", "private": True, "fork": False, "archived": False, "topics": ["type-workflow"]},
        ]
        catalog = update.build_repository_catalog(repos)
        self.assertEqual(catalog["totals"]["repositories"], 3)
        self.assertEqual(catalog["totals"]["public_repositories"], 2)
        self.assertEqual(catalog["totals"]["private_repositories"], 1)
        self.assertEqual(catalog["totals"]["active_original_repositories"], 2)
        self.assertEqual(catalog["totals"]["archived_original_repositories"], 1)
        names = [x["name"] for x in catalog["repositories"]]
        self.assertNotIn("forked", names)
        self.assertIn("secret", names)

    def test_multiple_type_topics_are_exposed_as_legacy(self):
        repo = {"name": "ambiguous", "topics": ["type-paper", "type-workflow"]}
        repo_type, source = update.repository_classification(repo, self.config)
        self.assertIsNone(repo_type)
        self.assertEqual(source, "multiple-type-topics")

    def test_render_inventory_groups_visibility_and_archived_without_forks(self):
        original_load = render.load
        try:
            render.load = lambda path, default: {
                "totals": {
                    "repositories": 3,
                    "public_repositories": 2,
                    "private_repositories": 1,
                    "active_original_repositories": 2,
                    "archived_original_repositories": 1,
                    "other_or_legacy_active": 1,
                    "manual_type_topics_active": 1,
                },
                "repositories": [
                    {"name": "legacy", "html_url": "https://github.com/qselmer/legacy", "description": "x", "language": "R", "updated_at": "2026-01-01", "private": False, "archived": False, "repository_type_label": "Other / legacy", "classification_source": "unclassified"},
                    {"name": "secret", "html_url": "https://github.com/qselmer/secret", "description": "do not show", "language": "Python", "updated_at": "2026-01-02", "private": True, "archived": False, "repository_type_label": "Methods & workflows", "classification_source": "topic"},
                    {"name": "old", "html_url": "https://github.com/qselmer/old", "description": "x", "language": "R", "updated_at": "2025-01-01", "private": False, "archived": True, "repository_type_label": "Methods & workflows", "classification_source": "topic"},
                ],
            }
            text = render.render_projects()
        finally:
            render.load = original_load
        self.assertIn("Other / legacy (1)", text)
        self.assertIn("Archived repositories (1)", text)
        self.assertIn("🔒 Private", text)
        self.assertNotIn("do not show", text)
        self.assertNotIn("Forks", text)
        self.assertNotIn("Inventory:", text)
        self.assertNotIn("Manual taxonomy:", text)
        self.assertNotIn("Type basis", text)


if __name__ == "__main__":
    unittest.main()
