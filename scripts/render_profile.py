#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
REPOSITORY_CATALOG = ROOT / "assets/data/repository-catalog.json"
ORGANIZATIONAL_CONTRIBUTIONS = ROOT / "assets/data/organizational-contributions.json"
PROJECT_MARKERS = ("<!-- PROJECTS:START -->", "<!-- PROJECTS:END -->")

VISIBLE_TYPE_ORDER = [
    "Projects",
    "Packages",
    "Methods & workflows",
    "Apps & dashboards",
    "Papers",
    "Courses & training",
    "Templates",
    "Websites & infrastructure",
]

# Shared layout for every portfolio table rendered in the GitHub README.
# GitHub may adapt widths on narrow screens, but all tables start from the
# same five-column proportions and full available width.
TABLE_WIDTHS = ("26%", "14%", "42%", "10%", "8%")


def load(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def replace_projects(text: str, body: str) -> str:
    start, end = PROJECT_MARKERS
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if not pattern.search(text):
        raise RuntimeError("Missing PROJECTS markers")
    return pattern.sub(f"{start}\n{body.rstrip()}\n{end}", text)


def remove_level2_section(text: str, heading: str) -> str:
    """Remove one exact level-2 README section without touching adjacent sections."""
    pattern = re.compile(
        rf"\n## {re.escape(heading)}\n.*?(?=\n## |\Z)",
        re.S,
    )
    return pattern.sub("\n", text)


def prune_readme_sections(text: str) -> str:
    """Keep the profile concise while canonical data remain available elsewhere."""
    for heading in ("Research outputs", "How this profile is automated"):
        text = remove_level2_section(text, heading)
    return re.sub(r"\n{3,}", "\n\n", text)


def clean_text(value: Any, default: str = "—") -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    return text or default


def esc(value: Any, default: str = "—") -> str:
    return html.escape(clean_text(value, default), quote=True)


def repo_date(value: Any) -> str:
    text = str(value or "").strip()
    return text[:10] if len(text) >= 10 else "—"


def visibility_label(repo: dict[str, Any]) -> str:
    return "🔒 Private" if repo.get("private") else "🔓 Public"


def repository_row(repo: dict[str, Any]) -> str:
    name = esc(repo.get("name") or "unnamed")
    url = str(repo.get("html_url") or "").strip()
    project = f'<a href="{html.escape(url, quote=True)}"><code>{name}</code></a>' if url else f"<code>{name}</code>"
    private = bool(repo.get("private"))
    description = "Private repository" if private else esc(repo.get("description") or "—")
    language = "—" if private else esc(repo.get("language") or "—")
    updated = "—" if private else esc(repo_date(repo.get("updated_at")))
    cells = [project, esc(visibility_label(repo)), description, language, updated]
    return "<tr>" + "".join(
        f'<td width="{width}">{cell}</td>' for width, cell in zip(TABLE_WIDTHS, cells)
    ) + "</tr>"


def full_width_table(headers: list[str], rows: list[str]) -> list[str]:
    header_cells = "".join(
        f'<th width="{width}">{html.escape(header)}</th>'
        for width, header in zip(TABLE_WIDTHS, headers)
    )
    return [
        '<table width="100%">',
        f"<thead><tr>{header_cells}</tr></thead>",
        "<tbody>",
        *rows,
        "</tbody>",
        "</table>",
    ]


def repository_table(repositories: list[dict[str, Any]]) -> list[str]:
    rows = [repository_row(repo) for repo in repositories]
    return full_width_table(
        ["Repository", "Visibility", "Description", "Main language", "Updated"],
        rows,
    )


def organizational_row(item: dict[str, Any]) -> str:
    name = esc(item.get("name") or "unnamed")
    url = str(item.get("html_url") or "").strip()
    project = f'<a href="{html.escape(url, quote=True)}"><code>{name}</code></a>' if url else f"<code>{name}</code>"
    cells = [
        project,
        esc(item.get("organization")),
        esc(item.get("contribution")),
        esc(item.get("repository_type_label")),
        esc(repo_date(item.get("updated_at"))),
    ]
    return "<tr>" + "".join(
        f'<td width="{width}">{cell}</td>' for width, cell in zip(TABLE_WIDTHS, cells)
    ) + "</tr>"


def render_organizational_contributions() -> list[str]:
    payload = load(ORGANIZATIONAL_CONTRIBUTIONS, {"contributions": []})
    contributions = payload.get("contributions") or []
    if not contributions:
        return []
    rows = [
        organizational_row(item)
        for item in sorted(
            contributions,
            key=lambda x: (
                str(x.get("organization") or "").casefold(),
                str(x.get("name") or "").casefold(),
            ),
        )
    ]
    return [
        "### Institutional & collaborative work",
        "",
        "Selected repositories owned by research organizations are shown separately from my personal repository counts.",
        "",
        *full_width_table(
            ["Repository", "Organization", "Contribution", "Type", "Updated"],
            rows,
        ),
        "",
    ]


def render_projects() -> str:
    payload = load(REPOSITORY_CATALOG, {"repositories": [], "totals": {}})
    repositories = payload.get("repositories") or []
    if not repositories:
        return "_Repository inventory will be populated on the next profile Action run._"

    active = [repo for repo in repositories if not repo.get("archived")]
    archived = [repo for repo in repositories if repo.get("archived")]
    lines: list[str] = []

    for label in VISIBLE_TYPE_ORDER:
        group = sorted(
            [repo for repo in active if repo.get("repository_type_label") == label],
            key=lambda x: (bool(x.get("private")), str(x.get("name") or "").casefold()),
        )
        if not group:
            continue
        lines += [f"### {label} ({len(group)})", ""]
        lines += repository_table(group) + [""]

    lines += render_organizational_contributions()

    if archived:
        lines += [
            f"### Archived repositories ({len(archived)})",
            "",
            "<sub>Archived originals remain available for audit purposes but are excluded from summary cards.</sub>",
            "",
        ]
        lines += repository_table(sorted(archived, key=lambda x: str(x.get("name") or "").casefold())) + [""]

    return "\n".join(lines).rstrip()


def main() -> None:
    text = README.read_text(encoding="utf-8")
    text = prune_readme_sections(text)
    text = replace_projects(text, render_projects())
    README.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
