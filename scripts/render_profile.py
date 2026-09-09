#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
PUBS = ROOT / "assets/data/publications.json"
REPOSITORY_CATALOG = ROOT / "assets/data/repository-catalog.json"
TOKEN = os.getenv("GITHUB_TOKEN", "")
# 0 means show all public ORCID works in the profile.
MAX_RESEARCH_OUTPUTS = int(os.getenv("MAX_RESEARCH_OUTPUTS", "0"))

MARKERS = {
    "publications": ("<!-- PUBLICATIONS:START -->", "<!-- PUBLICATIONS:END -->"),
    "projects": ("<!-- PROJECTS:START -->", "<!-- PROJECTS:END -->"),
}
STATUS = {
    "published": ("📄", "Published"),
    "in_preparation": ("", "In preparation"),
    "under_review": ("", "Under review"),
    "planned": ("", "Planned"),
}
OUTPUT_META = {
    "Journal articles": ("", "Journal articles"),
    "Preprints & working papers": ("", "Preprints & working papers"),
    "Books & chapters": ("", "Books & chapters"),
    "Theses": ("", "Theses"),
    "Conference outputs": ("", "Conference contributions"),
    "Reports & technical outputs": ("", "Reports & technical outputs"),
    "Data & software": ("", "Data & software"),
    "Other research outputs": ("", "Other research outputs"),
}

OUTPUT_TYPE_ORDER = list(OUTPUT_META)

VISIBLE_TYPE_ORDER = [
    "Projects",
    "Packages",
    "Methods & workflows",
    "Apps & dashboards",
    "Papers",
    "Courses & training",
    "Templates",
    "Websites & infrastructure",
    "Other / legacy",
]


def load(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def replace(text: str, key: str, body: str) -> str:
    start, end = MARKERS[key]
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if not pattern.search(text):
        raise RuntimeError(f"Missing markers for {key}")
    return pattern.sub(f"{start}\n{body.rstrip()}\n{end}", text)


def initials(given: str) -> str:
    parts = re.findall(r"[^\W\d_]+", given, flags=re.UNICODE)
    return " ".join(f"{part[0].upper()}." for part in parts if part)


def is_elmer(name: str) -> bool:
    n = name.casefold()
    return "quispe" in n and "salazar" in n and ("elmer" in n or re.search(r"\be\.?\b", n))


def apa_name(name: str) -> str:
    name = re.sub(r"\s+", " ", name.strip())
    if not name:
        return ""
    if "," in name:
        family, given = [x.strip() for x in name.split(",", 1)]
    else:
        parts = name.split()
        family, given = (parts[-1], " ".join(parts[:-1])) if len(parts) > 1 else (parts[0], "")
    value = f"{family}, {initials(given)}".strip().rstrip(",")
    return f"**{value}**" if is_elmer(name) else value


def authors_apa(pub: dict[str, Any]) -> str:
    names = pub.get("authors") or ["Elmer Quispe-Salazar"]
    values = [apa_name(str(name)) for name in names if str(name).strip()]
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f"{values[0]}, & {values[1]}"
    return f"{', '.join(values[:-1])}, & {values[-1]}"


def source_apa(pub: dict[str, Any]) -> str:
    journal = str(pub.get("journal") or pub.get("outlet") or pub.get("type") or "").strip()
    volume = str(pub.get("volume") or "").strip()
    issue = str(pub.get("issue") or "").strip()
    pages = str(pub.get("pages") or "").strip()
    if not journal:
        return ""
    source = f"*{journal}*"
    if volume:
        source = f"*{journal}, {volume}*"
    if issue:
        source += f"({issue})"
    if pages:
        source += f", {pages}"
    return source + "."


def output_category(pub: dict[str, Any]) -> str:
    category = str(pub.get("output_category") or "").strip()
    return category if category in OUTPUT_META else "Other research outputs"


def reference(pub: dict[str, Any], show_output_type: bool = False) -> str:
    status = str(pub.get("status") or "published")
    status_icon, date_text = STATUS.get(status, STATUS["published"])
    year = str(pub.get("year") or "n.d.")
    date = f"({year})." if status == "published" else f"({date_text})."
    title = str(pub.get("title") or "Untitled work").strip()

    prefix = "-" if status == "published" else f"- {status_icon}".rstrip()
    if show_output_type and status == "published":
        icon, label = OUTPUT_META[output_category(pub)]
        prefix = f"- {icon} **{label}** ·" if icon else f"- **{label}** ·"

    parts = [f"{prefix} {authors_apa(pub)} {date} {title}."]
    source = source_apa(pub)
    if source:
        parts.append(source)
    url = str(pub.get("url") or "").strip()
    if url:
        label = str(pub.get("link_label") or ("View output" if status == "published" else "View project"))
        parts.append(f"[{label}]({url})")
    return " ".join(parts)


def _year_value(pub: dict[str, Any]) -> int:
    try:
        return int(pub.get("year") or 0)
    except (TypeError, ValueError):
        return 0


def render_publications() -> str:
    pubs = load(PUBS, {}).get("publications", [])
    if MAX_RESEARCH_OUTPUTS > 0:
        pubs = pubs[:MAX_RESEARCH_OUTPUTS]
    if not pubs:
        return "_ORCID research-output metadata is temporarily unavailable._"

    grouped: dict[str, list[dict[str, Any]]] = {label: [] for label in OUTPUT_TYPE_ORDER}
    specific_other: dict[str, list[dict[str, Any]]] = {}
    for pub in pubs:
        category = output_category(pub)
        if category == "Other research outputs":
            specific = str(pub.get("type") or "Scholarly output").strip() or "Scholarly output"
            specific_other.setdefault(specific, []).append(pub)
        else:
            grouped[category].append(pub)

    lines: list[str] = []
    for category in OUTPUT_TYPE_ORDER:
        if category == "Other research outputs":
            continue
        items = grouped.get(category) or []
        if not items:
            continue
        _, heading = OUTPUT_META[category]
        lines += [f"### {heading}", ""]
        for pub in sorted(items, key=lambda x: (-_year_value(x), str(x.get("title") or "").casefold())):
            lines.append(reference({**pub, "status": "published"}, show_output_type=False))
        lines.append("")

    # Never expose a vague "Other research outputs" heading. If ORCID contains
    # an uncommon type, use that exact source type as the section heading.
    for specific in sorted(specific_other, key=str.casefold):
        lines += [f"### {specific}", ""]
        for pub in sorted(specific_other[specific], key=lambda x: (-_year_value(x), str(x.get("title") or "").casefold())):
            lines.append(reference({**pub, "status": "published"}, show_output_type=False))
        lines.append("")
    return "\n".join(lines).rstrip()


def md_cell(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "—").strip())
    return text.replace("|", "\\|")


def repo_date(value: Any) -> str:
    text = str(value or "").strip()
    return text[:10] if len(text) >= 10 else "—"


def visibility_label(repo: dict[str, Any]) -> str:
    return "🔒 Private" if repo.get("private") else "🔓 Public"


def classification_label(repo: dict[str, Any]) -> str:
    source = str(repo.get("classification_source") or "unclassified")
    labels = {
        "topic": "type-* topic",
        "legacy-topic": "legacy topic",
        "override": "override",
        "name-inference": "name inference",
        "multiple-type-topics": "ambiguous",
        "unclassified": "unclassified",
    }
    return labels.get(source, source)


def repo_row(repo: dict[str, Any]) -> str:
    name = md_cell(repo.get("name") or "unnamed")
    url = str(repo.get("html_url") or "").strip()
    project = f"[`{name}`]({url})" if url else f"`{name}`"
    private = bool(repo.get("private"))
    # Do not expose additional private-repository metadata on a public profile.
    description = "Private repository" if private else md_cell(repo.get("description") or "—")
    language = "—" if private else md_cell(repo.get("language") or "—")
    updated = "—" if private else repo_date(repo.get("updated_at"))
    return f"| {project} | {visibility_label(repo)} | {description} | {language} | {updated} |"


def repository_table(repositories: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Repository | Visibility | Description | Main language | Updated |",
        "|---|---|---|---|---|",
    ]
    lines.extend(repo_row(repo) for repo in repositories)
    return lines


def render_projects() -> str:
    payload = load(REPOSITORY_CATALOG, {"repositories": [], "totals": {}})
    repositories = payload.get("repositories") or []
    totals = payload.get("totals") or {}
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
        if label == "Other / legacy":
            lines += [
                "<sub>These repositories do not yet have one defensible canonical `type-*` topic. Add exactly one manual `type-*` topic, archive the repository, or remove it if it no longer belongs in the portfolio.</sub>",
                "",
            ]
        lines += repository_table(group) + [""]

    if archived:
        lines += [
            f"### Archived repositories ({len(archived)})",
            "",
            "<sub>Archived originals remain visible for audit purposes but are excluded from language and repository-type summary cards.</sub>",
            "",
        ]
        lines += repository_table(sorted(archived, key=lambda x: str(x.get("name") or "").casefold())) + [""]

    return "\n".join(lines).rstrip()


def main() -> None:
    text = README.read_text(encoding="utf-8")
    text = replace(text, "projects", render_projects())
    text = replace(text, "publications", render_publications())
    README.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
