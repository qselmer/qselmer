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

    assert "### Apps & dashboards" in text
    assert "public-app" in text
    assert "private-app" in text
    assert "🔒" in text
    assert "🔓" in text
    assert "🔒 Private" not in text
    assert "🔓 Public" not in text
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
    assert "🔓" in table
    assert "🔓 Public" not in table
    assert "Updated" not in table
    assert "Repository" in table
    assert "Description" in table
    assert "Main language" in table
    assert table.index("Description") < table.index("Visibility") < table.index("Main language")
    assert "https://cdn.simpleicons.org/r/276DC3" in table
    assert ">R<" not in table
    assert '<table width="950">' in table
    assert 'width="247"' in table
    assert 'width="437"' in table
    assert 'width="114"' in table
    assert 'width="152"' in table


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

<p align="justify">
For research collaboration or professional contact: <a href="mailto:qselmers@gmail.com">qselmers@gmail.com</a>
</p>

## Research outputs & metrics

<p align="center">
  <img src="assets/generated/research-outputs.svg" width="410" alt="x">
  <img src="assets/generated/research-metrics.svg" width="410" alt="y">
</p>

<sub>This card summarizes the public scholarly record. ORCID is the canonical source for research outputs; DOI records are enriched with Crossref metadata. Citation count, h-index and i10-index are refreshed from OpenAlex, resolving the author first by ORCID and, when needed, through exact DOI-authorship links from the ORCID record. Google Scholar remains linked above for profile discovery and citation browsing, but is not scraped by the automation.</sub>

## Scientific computing

Old skills block.

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
    assert refined.index("## Research focus") < refined.index("For research collaboration or professional contact")
    assert refined.index("For research collaboration or professional contact") < refined.index("## Scientific computing")
    assert refined.index("## Scientific computing") < refined.index("assets/generated/top-languages.svg")
    assert refined.count("## Scientific computing\n") == 1
    assert "JavaScript-F7DF1E" in refined
    assert "Jupyter-F37626" in refined
    assert "Quarto-75AADB" in refined
    assert "LaTeX-008080" in refined
    assert "Git-F05032" in refined
    assert "GitHub_Actions-2088FF" in refined


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


def test_zero_summary_values_render_as_dash():
    assert update.format_metric(0) == "-"
    assert update.format_metric("0") == "-"
    assert update.format_metric(None) == "-"
    assert update.format_metric(5) == "5"
