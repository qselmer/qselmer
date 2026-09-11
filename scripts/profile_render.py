#!/usr/bin/env python3
"""Canonical README renderer for the repo.yml-aware repository catalog."""

from __future__ import annotations

try:
    import render_profile as core
except ModuleNotFoundError:  # imported from repository-root unit tests
    from scripts import render_profile as core


def render_projects() -> str:
    payload = core.load(core.REPOSITORY_CATALOG, {"repositories": [], "totals": {}})
    repositories = payload.get("repositories") or []
    if not repositories:
        return "_Repository inventory will be populated on the next profile Action run._"

    included = [repo for repo in repositories if repo.get("profile_include", True)]
    active = [repo for repo in included if repo.get("active", not repo.get("archived"))]
    inactive = [repo for repo in included if not repo.get("active", not repo.get("archived"))]
    lines: list[str] = []

    for label in core.VISIBLE_TYPE_ORDER:
        group = sorted(
            [repo for repo in active if repo.get("repository_type_label") == label],
            key=lambda x: (bool(x.get("private")), str(x.get("name") or "").casefold()),
        )
        if not group:
            continue
        lines += [f"### {label}", ""]
        lines += core.repository_table(group) + [""]

    lines += core.render_organizational_contributions()

    if inactive:
        lines += [
            "### Archived repositories",
            "",
            "<sub>Archived or lifecycle-inactive originals remain available for audit purposes but are excluded from summary cards and active groups.</sub>",
            "",
        ]
        lines += core.repository_table(
            sorted(inactive, key=lambda x: (bool(x.get("private")), str(x.get("name") or "").casefold()))
        ) + [""]

    return "\n".join(lines).rstrip()


def main() -> None:
    core.render_projects = render_projects
    core.main()


if __name__ == "__main__":
    main()
