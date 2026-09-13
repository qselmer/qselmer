#!/usr/bin/env python3
"""Canonical README renderer for the repo.yml-aware repository catalog.

The public GitHub profile is an allow-listed surface. Static scientific identity
text mirrors the canonical career master, while private repository names and
metadata never reach the public README.
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

    return text.replace(
        "Public and private repositories are both listed below; visibility is shown in each table with 🔓 or 🔒. "
        "Forks and archived repositories are excluded from the active portfolio.",
        "Only active public original repositories selected for the profile are listed below. "
        "Private repositories remain internal and are never named on this public surface; forks and archived repositories are excluded from the active portfolio.",
    )


def render_projects() -> str:
    payload = core.load(core.REPOSITORY_CATALOG, {"repositories": [], "totals": {}})
    repositories = payload.get("repositories") or []
    if not repositories:
        return "_Repository inventory will be populated on the next profile Action run._"

    # Public profile = explicit public allow-list. Private repository names must
    # never reach README.md even if a future token can see them.
    included = [
        repo
        for repo in repositories
        if repo.get("profile_include", True) and not bool(repo.get("private"))
    ]
    active = [repo for repo in included if repo.get("active", not repo.get("archived"))]
    inactive = [repo for repo in included if not repo.get("active", not repo.get("archived"))]
    lines: list[str] = []

    for label in core.VISIBLE_TYPE_ORDER:
        group = sorted(
            [repo for repo in active if repo.get("repository_type_label") == label],
            key=lambda x: str(x.get("name") or "").casefold(),
        )
        if not group:
            continue
        lines += [f"### {label}", ""]
        lines += core.repository_table(group) + [""]

    # Organizational contributions are a separate, explicitly maintained
    # public data source and therefore remain eligible for rendering.
    lines += core.render_organizational_contributions()

    if inactive:
        lines += [
            "### Archived repositories",
            "",
            "<sub>Archived or lifecycle-inactive public originals remain available for audit purposes but are excluded from summary cards and active groups.</sub>",
            "",
        ]
        lines += core.repository_table(
            sorted(inactive, key=lambda x: str(x.get("name") or "").casefold())
        ) + [""]

    return "\n".join(lines).rstrip()


def main() -> None:
    core.render_projects = render_projects
    core.refine_static_readme = refine_static_readme
    core.main()


if __name__ == "__main__":
    main()
