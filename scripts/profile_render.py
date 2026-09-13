#!/usr/bin/env python3
"""Canonical README renderer for the repo.yml-aware repository catalog.

The public GitHub profile is an allow-listed surface: private repository names
and private repository metadata remain available to the internal catalog and
summary metrics, but are never rendered in public repository tables.
"""

from __future__ import annotations

try:
    import render_profile as core
except ModuleNotFoundError:  # imported from repository-root unit tests
    from scripts import render_profile as core


_ORIGINAL_REFINE_STATIC_README = core.refine_static_readme


def refine_static_readme(text: str) -> str:
    """Apply the canonical renderer and enforce public-only portfolio wording."""
    text = _ORIGINAL_REFINE_STATIC_README(text)
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
    # never reach README.md even when PROFILE_REPO_TOKEN can see them.
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
