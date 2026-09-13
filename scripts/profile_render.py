#!/usr/bin/env python3
"""Canonical README renderer for the repo.yml-aware repository catalog.

The public GitHub profile is an allow-listed surface. Static scientific identity
text mirrors the canonical career master, while private repository names and
metadata never reach the public README. Repository highlights are deliberately
curated from records approved for the ``github_profile`` target in the career
master; this file is the public-code mirror of that selection.
"""

from __future__ import annotations

import re

try:
    import render_profile as core
except ModuleNotFoundError:  # imported from repository-root unit tests
    from scripts import render_profile as core


_ORIGINAL_REFINE_STATIC_README = core.refine_static_readme

# Canonical public identity text mirrored from the career master (06_PROFILE).
CANONICAL_HEADLINE = "Quantitative Marine Ecology & Fisheries Science"
CANONICAL_SHORT_BIO = (
    "Marine biologist affiliated with the Peruvian Marine Research Institute (IMARPE), "
    "working at the intersection of quantitative marine ecology, fisheries science and "
    "scientific computing. His research focuses on pelagic resources, stock assessment, "
    "spatiotemporal analysis and reproducible ocean- and fisheries-data workflows in the "
    "Humboldt Current system."
)

# Public repository highlights mirrored from approved master placements.
# Private repositories are intentionally impossible to add to this public list.
CURATED_REPOSITORY_GROUPS = [
    (
        "Scientific software & workflows",
        (
            "oceancube",
            "humboldt-ocean-watch",
            "oceHCS-environmental-data-workflow",
        ),
    ),
    (
        "Reproducible templates",
        (
            ".template-mse",
        ),
    ),
    (
        "Books & research resources",
        (
            "fisheries-research-workflows-book",
        ),
    ),
]
CURATED_REPOSITORIES = {
    name for _, names in CURATED_REPOSITORY_GROUPS for name in names
}


def refine_static_readme(text: str) -> str:
    """Apply canonical master text and enforce public-only portfolio wording."""
    text = _ORIGINAL_REFINE_STATIC_README(text)

    text = re.sub(
        r'<h1 align="center">.*?</h1>',
        f'<h1 align="center">{CANONICAL_HEADLINE}</h1>',
        text,
        count=1,
        flags=re.S,
    )

    text = re.sub(
        r'<p align="justify">\s*.*?</p>',
        '<p align="justify">\n  ' + CANONICAL_SHORT_BIO + '\n</p>',
        text,
        count=1,
        flags=re.S,
    )

    text = text.replace(
        "Public and private repositories are both listed below; visibility is shown in each table with 🔓 or 🔒. "
        "Forks and archived repositories are excluded from the active portfolio.",
        "Only repositories deliberately selected for the public scientific profile are listed below. "
        "Private repositories remain internal and are never named on this public surface; forks and archived repositories are excluded from the active portfolio.",
    )

    text = re.sub(
        r'<sub>Primary Languages uses active public original repositories\. Repository Types includes .*?</sub>',
        '<sub>Primary Languages and Repository Types summarize the active public original repository inventory. '
        'The portfolio below is a smaller curated scientific selection mirrored from the career master; private repositories are excluded.</sub>',
        text,
        count=1,
        flags=re.S,
    )
    return text


def render_projects() -> str:
    payload = core.load(core.REPOSITORY_CATALOG, {"repositories": [], "totals": {}})
    repositories = payload.get("repositories") or []
    if not repositories:
        return "_Repository inventory will be populated on the next profile Action run._"

    by_name = {
        str(repo.get("name") or ""): repo
        for repo in repositories
        if not bool(repo.get("private"))
    }

    # Defense in depth: a private record can never be rendered, and only names
    # explicitly selected in the public career-master mirror can enter the table.
    lines: list[str] = []
    for heading, names in CURATED_REPOSITORY_GROUPS:
        group = []
        for name in names:
            repo = by_name.get(name)
            if not repo:
                continue
            if not repo.get("active", not repo.get("archived")):
                continue
            group.append(repo)
        if not group:
            continue
        lines += [f"### {heading}", ""]
        lines += core.repository_table(group) + [""]

    # Organizational contributions are maintained through a separate explicit
    # public data source and may remain visible independently of personal repos.
    lines += core.render_organizational_contributions()

    if not lines:
        return "_Curated public repository highlights are being synchronized._"
    return "\n".join(lines).rstrip()


def main() -> None:
    core.render_projects = render_projects
    core.refine_static_readme = refine_static_readme
    core.main()


if __name__ == "__main__":
    main()
