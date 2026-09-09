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

# Public repository tables intentionally share one compact three-column layout.
# GitHub may adapt widths on narrow screens, but every table starts from the
# same proportions and full available width.
TABLE_WIDTHS = ("28%", "58%", "14%")
ORGANIZATIONAL_TABLE_WIDTHS = ("22%", "16%", "16%", "34%", "12%")

PORTFOLIO_CARDS = """<p align="center">
  <img src="assets/generated/top-languages.svg" width="410" alt="Primary programming languages across active public original repositories">
  <img src="assets/generated/repository-types.svg" width="410" alt="Active original repositories by repository type, including public and private repositories">
</p>"""

METRICS_NOTE = (
    "<sub>Research outputs are synchronized from ORCID/Crossref; "
    "bibliometric indicators are obtained from OpenAlex.</sub>"
)
PORTFOLIO_NOTE = (
    "<sub>Primary Languages uses active public original repositories. Repository Types includes "
    "active public and private original repositories visible to the profile automation; forks and "
    "archived repositories are excluded.</sub>"
)


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


def refine_static_readme(text: str) -> str:
    """Apply stable presentation rules without shortening the biography or research focus."""
    # Make the profile self-contained while preserving the existing introductory paragraph.
    first_heading = '<h2 align="center">Marine Quantitative Ecologist & Fisheries Scientist</h2>'
    if '<h1 align="center">Elmer Quispe-Salazar</h1>' not in text:
        text = text.replace(
            first_heading,
            '<h1 align="center">Elmer Quispe-Salazar</h1>\n\n'
            + first_heading
            + '\n\n<p align="center"><strong>Instituto del Mar del Perú (IMARPE)</strong> · Peru</p>',
            1,
        )

    # Remove vanity traffic counters and keep only the core academic/professional profile links.
    text = re.sub(
        r'\n<p align="center">\s*<img[^>]+komarev\.com/ghpvc/[^>]+>\s*</p>\n',
        "\n",
        text,
        flags=re.S,
    )
    text = re.sub(r'\n\s*<a href="https://www\.researchgate\.net/[^\n]+</a>', "", text)
    text = re.sub(r'\n\s*<a href="https://x\.com/[^\n]+</a>', "", text)

    # Keep institutional affiliation out of the public GitHub profile header.
    text = text.replace(
        '\n<p align="center"><strong>Instituto del Mar del Perú (IMARPE)</strong> · Peru</p>\n',
        "\n",
    )

    # Keep the academic/profile link badges immediately below the professional title.
    profile_links = None
    for match in re.finditer(
        r'\n(<p align="center">\s*(?:(?:<a href="[^"]+">.*?</a>)\s*)+</p>)\n',
        text,
        flags=re.S,
    ):
        if "Google_Scholar" in match.group(1) and "ORCID" in match.group(1):
            profile_links = match
            break
    if profile_links:
        block = profile_links.group(1)
        start, end = profile_links.span(1)
        text = text[:start] + text[end:]
        text = text.replace(first_heading, first_heading + "\n\n" + block, 1)

    # Academic outputs and metrics precede the thematic Research focus section.
    focus_match = re.search(r'\n## Research focus\n.*?(?=\n## |\Z)', text, flags=re.S)
    outputs_match = re.search(r'\n## Research outputs & metrics\n.*?(?=\n## |\Z)', text, flags=re.S)
    if focus_match and outputs_match and focus_match.start() < outputs_match.start():
        between = text[focus_match.end():outputs_match.start()]
        if "\n## " not in between:
            text = (
                text[:focus_match.start()]
                + outputs_match.group(0)
                + focus_match.group(0)
                + text[outputs_match.end():]
            )

    # Remove any previously rendered scope note before rebuilding the card block.
    text = text.replace(PORTFOLIO_NOTE, "")

    # Remove the repository cards from their legacy top-of-profile position.
    text = re.sub(
        r'\n<p align="center">\s*<img src="assets/generated/top-languages\.svg".*?'
        r'<img src="assets/generated/repository-types\.svg".*?</p>\n',
        "\n",
        text,
        count=1,
        flags=re.S,
    )

    # Keep metric provenance visible but concise, then place computing cards after academic metrics.
    text = re.sub(
        r'<sub>This card summarizes the public scholarly record\..*?</sub>',
        METRICS_NOTE,
        text,
        count=1,
        flags=re.S,
    )
    if PORTFOLIO_CARDS not in text:
        text = text.replace(
            METRICS_NOTE,
            METRICS_NOTE + "\n\n" + PORTFOLIO_CARDS + "\n\n" + PORTFOLIO_NOTE,
            1,
        )

    # Public tables are the discovery layer; private repositories remain counted but are not listed.
    text = re.sub(
        r'(## Scientific computing & reproducible research\n\n).*?(?=\n\n<!-- PROJECTS:START -->)',
        r'\1Public original research repositories are organized by their primary scientific or computational function. '
        r'Forks and archived repositories are excluded from the active portfolio. Private repositories remain included '
        r'in Repository Types counts but are not listed below.',
        text,
        count=1,
        flags=re.S,
    )

    # Keep scientific-computing technologies; implementation/infrastructure badges are already evidenced by the repo.
    text = re.sub(
        r'\n\s*<img src="https://img\.shields\.io/badge/(?:Git-|GitHub_Actions-|Quarto-)[^\n]+>',
        "",
        text,
    )
    return re.sub(r"\n{3,}", "\n\n", text)


def clean_text(value: Any, default: str = "—") -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    return text or default


def esc(value: Any, default: str = "—") -> str:
    return html.escape(clean_text(value, default), quote=True)


def repo_date(value: Any) -> str:
    text = str(value or "").strip()
    return text[:10] if len(text) >= 10 else "—"


def repository_row(repo: dict[str, Any]) -> str:
    name = esc(repo.get("name") or "unnamed")
    url = str(repo.get("html_url") or "").strip()
    project = f'<a href="{html.escape(url, quote=True)}"><code>{name}</code></a>' if url else f"<code>{name}</code>"
    cells = [
        project,
        esc(repo.get("description") or "—"),
        esc(repo.get("language") or "—"),
    ]
    return "<tr>" + "".join(
        f'<td width="{width}">{cell}</td>' for width, cell in zip(TABLE_WIDTHS, cells)
    ) + "</tr>"


def full_width_table(headers: list[str], rows: list[str], widths: tuple[str, ...]) -> list[str]:
    if len(headers) != len(widths):
        raise ValueError("Table headers and widths must have the same length")
    header_cells = "".join(
        f'<th width="{width}">{html.escape(header)}</th>'
        for width, header in zip(widths, headers)
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
        ["Repository", "Description", "Main language"],
        rows,
        TABLE_WIDTHS,
    )


def organizational_row(item: dict[str, Any]) -> str:
    name = esc(item.get("name") or "unnamed")
    url = str(item.get("html_url") or "").strip()
    project = f'<a href="{html.escape(url, quote=True)}"><code>{name}</code></a>' if url else f"<code>{name}</code>"
    cells = [
        project,
        esc(item.get("organization")),
        esc(item.get("role")),
        esc(item.get("contribution")),
        esc(item.get("repository_type_label")),
    ]
    return "<tr>" + "".join(
        f'<td width="{width}">{cell}</td>'
        for width, cell in zip(ORGANIZATIONAL_TABLE_WIDTHS, cells)
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
            ["Repository", "Organization", "Role", "Contribution", "Type"],
            rows,
            ORGANIZATIONAL_TABLE_WIDTHS,
        ),
        "",
    ]


def render_projects() -> str:
    payload = load(REPOSITORY_CATALOG, {"repositories": [], "totals": {}})
    repositories = payload.get("repositories") or []
    if not repositories:
        return "_Repository inventory will be populated on the next profile Action run._"

    active_public = [
        repo for repo in repositories
        if not repo.get("archived") and not repo.get("private")
    ]
    archived_public = [
        repo for repo in repositories
        if repo.get("archived") and not repo.get("private")
    ]
    lines: list[str] = [
        "<sub>🔒 Private repositories are included in Repository Types counts but omitted from the public inventory below.</sub>",
        "",
    ]

    for label in VISIBLE_TYPE_ORDER:
        group = sorted(
            [repo for repo in active_public if repo.get("repository_type_label") == label],
            key=lambda x: str(x.get("name") or "").casefold(),
        )
        if not group:
            continue
        lines += [f"### {label} ({len(group)})", ""]
        lines += repository_table(group) + [""]

    lines += render_organizational_contributions()

    if archived_public:
        lines += [
            f"### Archived repositories ({len(archived_public)})",
            "",
            "<sub>Archived originals remain available for audit purposes but are excluded from summary cards.</sub>",
            "",
        ]
        lines += repository_table(
            sorted(archived_public, key=lambda x: str(x.get("name") or "").casefold())
        ) + [""]

    return "\n".join(lines).rstrip()


def main() -> None:
    text = README.read_text(encoding="utf-8")
    text = prune_readme_sections(text)
    text = refine_static_readme(text)
    text = replace_projects(text, render_projects())
    README.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
