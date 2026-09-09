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

# Repository tables intentionally share one compact four-column layout.
# Visibility is encoded with an icon only: 🔓 or 🔒, and is the penultimate column.
# Main language is represented by the corresponding language logo when supported.
TABLE_TOTAL_WIDTH = "950"
TABLE_WIDTHS = ("247", "437", "114", "152")
ORGANIZATIONAL_TABLE_WIDTHS = ("190", "133", "133", "285", "114", "95")

PORTFOLIO_CARDS = """<p align="center">
  <img src="assets/generated/top-languages.svg" width="410" alt="Primary programming languages across active public original repositories">
  <img src="assets/generated/repository-types.svg" width="410" alt="Active original repositories by repository type, including public and private repositories">
</p>"""

SCIENTIFIC_COMPUTING_BLOCK = """## Scientific computing

<p align="center">
  <img src="https://img.shields.io/badge/R-276DC3?style=flat&logo=r&logoColor=white" alt="R">
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/C++-00599C?style=flat&logo=cplusplus&logoColor=white" alt="C++">
  <img src="https://img.shields.io/badge/Julia-9558B2?style=flat&logo=julia&logoColor=white" alt="Julia">
  <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=flat&logo=javascript&logoColor=000000" alt="JavaScript">
  <img src="https://img.shields.io/badge/TMB-333333?style=flat" alt="TMB">
  <img src="https://img.shields.io/badge/Stan-B2011D?style=flat" alt="Stan">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Jupyter-F37626?style=flat&logo=jupyter&logoColor=white" alt="Jupyter">
  <img src="https://img.shields.io/badge/Quarto-75AADB?style=flat&logo=quarto&logoColor=white" alt="Quarto">
  <img src="https://img.shields.io/badge/LaTeX-008080?style=flat&logo=latex&logoColor=white" alt="LaTeX">
  <img src="https://img.shields.io/badge/Git-F05032?style=flat&logo=git&logoColor=white" alt="Git">
  <img src="https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat&logo=githubactions&logoColor=white" alt="GitHub Actions">
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
    for heading in ("Research outputs", "How this profile is automated", "Collaboration and opportunities"):
        text = remove_level2_section(text, heading)
    return re.sub(r"\n{3,}", "\n\n", text)


def refine_static_readme(text: str) -> str:
    """Apply stable presentation rules without shortening the biography or research focus."""
    old_professional_heading = '<h2 align="center">Marine Quantitative Ecologist & Fisheries Scientist</h2>'
    professional_heading = '<h1 align="center">Marine Quantitative Ecologist & Fisheries Scientist</h1>'
    text = text.replace(old_professional_heading, professional_heading)
    text = text.replace('<h1 align="center">Elmer Quispe-Salazar</h1>\n\n', '')

    text = text.replace(
        '\n<p align="center"><strong>Instituto del Mar del Perú (IMARPE)</strong> · Peru</p>\n',
        "\n",
    )

    text = re.sub(
        r'\n<p align="center">\s*<img[^>]+komarev\.com/ghpvc/[^>]+>\s*</p>\n',
        "\n",
        text,
        flags=re.S,
    )
    text = re.sub(r'\n\s*<a href="https://www\.researchgate\.net/[^\n]+</a>', "", text)
    text = re.sub(r'\n\s*<a href="https://x\.com/[^\n]+</a>', "", text)

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
        text = text.replace(professional_heading, professional_heading + "\n\n" + block, 1)

    text = text.replace("\n## Research outputs & metrics\n", "\n")
    text = re.sub(
        r'<sub>This card summarizes the public scholarly record\..*?</sub>',
        METRICS_NOTE,
        text,
        count=1,
        flags=re.S,
    )

    # Rebuild this block at one canonical location below the contact line.
    text = remove_level2_section(text, "Scientific computing")

    text = text.replace(PORTFOLIO_NOTE, "")
    text = re.sub(
        r'\n<p align="center">\s*<img src="assets/generated/top-languages\.svg".*?'
        r'<img src="assets/generated/repository-types\.svg".*?</p>\n',
        "\n",
        text,
        count=1,
        flags=re.S,
    )

    contact_match = re.search(
        r'\n(<p align="justify">\s*For research collaboration or professional contact:.*?</p>)\n',
        text,
        flags=re.S,
    )
    contact_block = contact_match.group(1) if contact_match else ""
    if contact_match:
        text = text[:contact_match.start()] + "\n" + text[contact_match.end():]

    focus_match = re.search(r'(\n## Research focus\n.*?)(?=\n## |\Z)', text, flags=re.S)
    if focus_match:
        focus_block = focus_match.group(1).rstrip()
        replacement = focus_block
        if contact_block:
            replacement += "\n\n" + contact_block
        replacement += "\n\n" + SCIENTIFIC_COMPUTING_BLOCK
        replacement += "\n\n" + PORTFOLIO_CARDS + "\n\n" + PORTFOLIO_NOTE + "\n"
        text = text[:focus_match.start()] + replacement + text[focus_match.end():]

    text = re.sub(
        r'(## Scientific computing & reproducible research\n\n).*?(?=\n\n<!-- PROJECTS:START -->)',
        r'\1Active original research repositories are organized by their primary scientific or computational function. '
        r'Public and private repositories are both listed below; visibility is shown in each table with 🔓 or 🔒. '
        r'Forks and archived repositories are excluded from the active portfolio.',
        text,
        count=1,
        flags=re.S,
    )

    return re.sub(r"\n{3,}", "\n\n", text)


def clean_text(value: Any, default: str = "-") -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    return text or default


def esc(value: Any, default: str = "-") -> str:
    return html.escape(clean_text(value, default), quote=True)


def repo_date(value: Any) -> str:
    text = str(value or "").strip()
    return text[:10] if len(text) >= 10 else "-"


def language_logo(value: Any) -> str:
    language = clean_text(value, "-")
    if language == "-":
        return "-"
    logos = {
        "r": ("r", "276DC3"),
        "python": ("python", "3776AB"),
        "c++": ("cplusplus", "00599C"),
        "julia": ("julia", "9558B2"),
        "css": ("css", "663399"),
        "html": ("html5", "E34F26"),
        "javascript": ("javascript", "F7DF1E"),
        "typescript": ("typescript", "3178C6"),
        "jupyter notebook": ("jupyter", "F37626"),
        "tex": ("latex", "008080"),
        "shell": ("gnubash", "4EAA25"),
    }
    spec = logos.get(language.casefold())
    if not spec:
        return esc(language)
    slug, color = spec
    return (
        f'<img src="https://cdn.simpleicons.org/{slug}/{color}" '
        f'alt="{html.escape(language, quote=True)}" title="{html.escape(language, quote=True)}" '
        f'width="20" height="20">'
    )


def repository_row(repo: dict[str, Any]) -> str:
    name = esc(repo.get("name") or "unnamed")
    url = str(repo.get("html_url") or "").strip()
    private = bool(repo.get("private"))
    label = f"<code>{name}</code>"
    project = f'<a href="{html.escape(url, quote=True)}">{label}</a>' if url else label
    visibility = "🔒" if private else "🔓"
    cells = [
        project,
        "Private repository" if private else esc(repo.get("description") or "-"),
        visibility,
        "-" if private else language_logo(repo.get("language") or "-"),
    ]
    return "<tr>" + "".join(
        f'<td width="{width}" align="center">{cell}</td>' if index in (2, 3)
        else f'<td width="{width}">{cell}</td>'
        for index, (width, cell) in enumerate(zip(TABLE_WIDTHS, cells))
    ) + "</tr>"


def full_width_table(headers: list[str], rows: list[str], widths: tuple[str, ...]) -> list[str]:
    if len(headers) != len(widths):
        raise ValueError("Table headers and widths must have the same length")
    header_cells = "".join(
        f'<th width="{width}">{html.escape(header)}</th>'
        for width, header in zip(widths, headers)
    )
    return [
        f'<table width="{TABLE_TOTAL_WIDTH}">',
        f"<thead><tr>{header_cells}</tr></thead>",
        "<tbody>",
        *rows,
        "</tbody>",
        "</table>",
    ]


def repository_table(repositories: list[dict[str, Any]]) -> list[str]:
    rows = [repository_row(repo) for repo in repositories]
    return full_width_table(
        ["Repository", "Description", "Visibility", "Main language"],
        rows,
        TABLE_WIDTHS,
    )


def organizational_row(item: dict[str, Any]) -> str:
    name = esc(item.get("name") or "unnamed")
    url = str(item.get("html_url") or "").strip()
    private = bool(item.get("private"))
    project = f'<a href="{html.escape(url, quote=True)}"><code>{name}</code></a>' if url else f"<code>{name}</code>"
    visibility = "🔒" if private else "🔓"
    cells = [
        project,
        esc(item.get("organization")),
        esc(item.get("role")),
        esc(item.get("contribution")),
        visibility,
        esc(item.get("repository_type_label")),
    ]
    return "<tr>" + "".join(
        f'<td width="{width}" align="center">{cell}</td>' if index == 4
        else f'<td width="{width}">{cell}</td>'
        for index, (width, cell) in enumerate(zip(ORGANIZATIONAL_TABLE_WIDTHS, cells))
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
            ["Repository", "Organization", "Role", "Contribution", "Visibility", "Type"],
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
            "<sub>Archived originals remain available for audit purposes but are excluded from summary cards and active groups.</sub>",
            "",
        ]
        lines += repository_table(
            sorted(archived, key=lambda x: (bool(x.get("private")), str(x.get("name") or "").casefold()))
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
