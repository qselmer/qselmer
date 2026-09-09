import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_module(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


update = load_module("scripts/update_profile.py", "update_profile_v2")
render = load_module("scripts/render_profile.py", "render_profile_v2")


def test_repository_type_counts_include_public_and_private_active_originals():
    repos = [
        {"name": "public-app", "topics": ["type-app"], "private": False, "fork": False, "archived": False},
        {"name": "private-app", "topics": ["type-app"], "private": True, "fork": False, "archived": False},
        {"name": "archived-app", "topics": ["type-app"], "private": False, "fork": False, "archived": True},
        {"name": "fork-app", "topics": ["type-app"], "private": False, "fork": True, "archived": False},
    ]
    counts = update.repository_type_counts(repos)
    assert counts["Apps & dashboards"] == 2


def test_readme_inventory_lists_public_and_private_repositories():
    original_load = render.load
    try:
        def fake_load(path, default):
            if path == render.ORGANIZATIONAL_CONTRIBUTIONS:
                return {"contributions": []}
            return {
                "repositories": [
                    {
                        "name": "public-app",
                        "html_url": "https://github.com/qselmer/public-app",
                        "description": "Public app",
                        "language": "Python",
                        "private": False,
                        "archived": False,
                        "repository_type_label": "Apps & dashboards",
                    },
                    {
                        "name": "private-app",
                        "html_url": "https://github.com/qselmer/private-app",
                        "description": "Sensitive description",
                        "language": "R",
                        "private": True,
                        "archived": False,
                        "repository_type_label": "Apps & dashboards",
                    },
                ]
            }
        render.load = fake_load
        text = render.render_projects()
    finally:
        render.load = original_load

    assert "### Apps & dashboards (2)" in text
    assert "public-app" in text
    assert "private-app" in text
    assert "🔒 Private" in text
    assert "🔓 Public" in text
    assert "Sensitive description" not in text
    assert "Private repository" in text

def test_personal_repository_table_has_visibility_column():
    table = "\n".join(render.repository_table([{
        "name": "example",
        "html_url": "https://github.com/qselmer/example",
        "description": "Example",
        "language": "R",
    }]))
    assert "Visibility" in table
    assert "🔓 Public" in table
    assert "Updated" not in table
    assert "Repository" in table
    assert "Description" in table
    assert "Main language" in table


def test_static_refinement_preserves_biography_and_research_focus():
    sample = """<h2 align="center">Marine Quantitative Ecologist & Fisheries Scientist</h2>

<p align="justify">BIOGRAPHY MUST REMAIN EXACTLY AS WRITTEN.</p>

<p align="center"><img src="https://komarev.com/ghpvc/?username=qselmer" alt="Profile views"></p>

<p align="center">
<a href="https://www.researchgate.net/profile/Elmer-Quispe-Salazar">ResearchGate</a>
<a href="https://x.com/elmerseascient">X</a>
</p>

<p align="center">
  <img src="assets/generated/top-languages.svg" width="410" alt="x">
  <img src="assets/generated/repository-types.svg" width="410" alt="y">
</p>

## Research focus

- KEEP THIS FOCUS LINE.

## Research outputs & metrics

<p align="center">
  <img src="assets/generated/research-outputs.svg" width="410" alt="x">
  <img src="assets/generated/research-metrics.svg" width="410" alt="y">
</p>

<sub>This card summarizes the public scholarly record. ORCID is the canonical source for research outputs; DOI records are enriched with Crossref metadata. Citation count, h-index and i10-index are refreshed from OpenAlex, resolving the author first by ORCID and, when needed, through exact DOI-authorship links from the ORCID record. Google Scholar remains linked above for profile discovery and citation browsing, but is not scraped by the automation.</sub>

## Scientific computing & reproducible research

Old intro.

<!-- PROJECTS:START -->
x
<!-- PROJECTS:END -->
"""
    refined = render.refine_static_readme(sample)
    assert "BIOGRAPHY MUST REMAIN EXACTLY AS WRITTEN." in refined
    assert "- KEEP THIS FOCUS LINE." in refined
    assert "Profile views" not in refined
    assert "researchgate.net" not in refined
    assert "https://x.com" not in refined
    assert "Instituto del Mar del Perú (IMARPE)" not in refined
    assert "## Research outputs & metrics" not in refined
    assert '<h1 align="center">Elmer Quispe-Salazar</h1>' not in refined
    assert '<h1 align="center">Marine Quantitative Ecologist & Fisheries Scientist</h1>' in refined
    assert refined.index("assets/generated/research-outputs.svg") < refined.index("## Research focus")
    assert refined.index("## Research focus") < refined.index("assets/generated/top-languages.svg")
    assert refined.index("## Research focus") < refined.index("For research collaboration or professional contact") < refined.index("assets/generated/top-languages.svg")


def test_collaboration_and_opportunities_is_pruned():
    sample = """Intro

## Collaboration and opportunities

Old collaboration block.

## Scientific computing

Keep me.
"""
    refined = render.prune_readme_sections(sample)
    assert "Collaboration and opportunities" not in refined
    assert "Old collaboration block" not in refined
    assert "## Scientific computing" in refined
