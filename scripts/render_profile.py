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
PIPELINE = ROOT / "assets/data/research-pipeline.json"
TOKEN = os.getenv("GITHUB_TOKEN", "")
# 0 means show all public ORCID works in the profile.
MAX_RESEARCH_OUTPUTS = int(os.getenv("MAX_RESEARCH_OUTPUTS", "0"))

MARKERS = {
    "publications": ("<!-- PUBLICATIONS:START -->", "<!-- PUBLICATIONS:END -->"),
    "projects": ("<!-- PROJECTS:START -->", "<!-- PROJECTS:END -->"),
    "pipeline": ("<!-- PIPELINE:START -->", "<!-- PIPELINE:END -->"),
}
STATUS = {
    "published": ("📄", "Published"),
    "in_preparation": ("🔓", "Manuscript in preparation"),
    "under_review": ("🔒", "Manuscript submitted for publication"),
    "planned": ("💻", "Planned study"),
}
OUTPUT_META = {
    "Journal articles": ("📄", "Journal article"),
    "Preprints & working papers": ("📝", "Preprint / working paper"),
    "Conference outputs": ("🎤", "Conference output"),
    "Books & chapters": ("📚", "Book / chapter"),
    "Theses": ("🎓", "Thesis"),
    "Reports & technical outputs": ("📋", "Report / technical output"),
    "Data & software": ("💾", "Data / software"),
    "Other research outputs": ("🔬", "Research output"),
}

VISIBLE_TYPE_ORDER = [
    "Packages",
    "Protocols & manuals",
    "Methods & workflows",
    "Reports",
    "Apps & dashboards",
    "Papers",
    "Courses & training",
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

    prefix = f"- {status_icon}"
    if show_output_type and status == "published":
        icon, label = OUTPUT_META[output_category(pub)]
        prefix = f"- {icon} **{label}** ·"

    parts = [f"{prefix} {authors_apa(pub)} {date} {title}."]
    source = source_apa(pub)
    if source:
        parts.append(source)
    url = str(pub.get("url") or "").strip()
    if url:
        label = str(pub.get("link_label") or ("View output" if status == "published" else "View project"))
        parts.append(f"[{label}]({url})")
    return " ".join(parts)


def render_publications() -> str:
    pubs = load(PUBS, {}).get("publications", [])
    if MAX_RESEARCH_OUTPUTS > 0:
        pubs = pubs[:MAX_RESEARCH_OUTPUTS]
    return "\n".join(
        reference({**pub, "status": "published"}, show_output_type=True)
        for pub in pubs
    ) or "_ORCID research-output metadata is temporarily unavailable._"


def render_pipeline() -> str:
    items = load(PIPELINE, {}).get("items", [])
    order = {"under_review": 0, "in_preparation": 1, "planned": 2}
    items = sorted(items, key=lambda x: (order.get(x.get("status"), 9), x.get("title", "").lower()))
    return "\n".join(reference(item) for item in items) or "_No pipeline items are currently listed._"


def md_cell(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "—").strip())
    return text.replace("|", "\\|")


def repo_date(value: Any) -> str:
    text = str(value or "").strip()
    return text[:10] if len(text) >= 10 else "—"


def repo_row(repo: dict[str, Any]) -> str:
    name = md_cell(repo.get("name") or "unnamed")
    url = str(repo.get("html_url") or "").strip()
    project = f"[`{name}`]({url})" if url else f"`{name}`"
    description = md_cell(repo.get("description") or "—")
    language = md_cell(repo.get("language") or "—")
    updated = repo_date(repo.get("updated_at"))
    return f"| {project} | {description} | {language} | {updated} |"


def repository_table(repositories: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Repository | Description | Main language | Updated |",
        "|---|---|---|---|",
    ]
    lines.extend(repo_row(repo) for repo in repositories)
    return lines


def render_projects() -> str:
    payload = load(REPOSITORY_CATALOG, {"repositories": [], "totals": {}})
    repositories = payload.get("repositories") or []
    totals = payload.get("totals") or {}
    if not repositories:
        return "_Repository inventory will be populated on the next profile Action run._"

    active = [repo for repo in repositories if not repo.get("fork") and not repo.get("archived")]
    archived = [repo for repo in repositories if not repo.get("fork") and repo.get("archived")]
    forks = [repo for repo in repositories if repo.get("fork")]

    lines = [
        (
            f"**Inventory:** {totals.get('public_repositories', len(repositories))} public repositories · "
            f"{totals.get('active_original_repositories', len(active))} active originals · "
            f"{totals.get('archived_original_repositories', len(archived))} archived · "
            f"{totals.get('forks', len(forks))} forks · "
            f"{totals.get('other_or_legacy_active', 0)} other/legacy."
        ),
        "",
    ]

    for label in VISIBLE_TYPE_ORDER:
        group = sorted(
            [repo for repo in active if repo.get("repository_type_label") == label],
            key=lambda x: str(x.get("name") or "").casefold(),
        )
        if not group:
            continue
        lines += [f"### {label} ({len(group)})", ""]
        if label == "Other / legacy":
            lines += [
                "<sub>These active repositories do not yet have a single defensible canonical `type-*` classification. Review, reclassify, archive or remove them as appropriate.</sub>",
                "",
            ]
        lines += repository_table(group) + [""]

    if archived:
        lines += [
            f"### Archived repositories ({len(archived)})",
            "",
            "<sub>Archived repositories are shown for cleanup visibility but are excluded from language and repository-type summary cards.</sub>",
            "",
        ]
        lines += repository_table(sorted(archived, key=lambda x: str(x.get("name") or "").casefold())) + [""]

    if forks:
        lines += [
            f"### Forks ({len(forks)})",
            "",
            "<sub>Public forks are shown for cleanup visibility but are excluded from language and repository-type summary cards.</sub>",
            "",
        ]
        lines += repository_table(sorted(forks, key=lambda x: str(x.get("name") or "").casefold())) + [""]

    return "\n".join(lines).rstrip()

def main() -> None:
    text = README.read_text(encoding="utf-8")
    text = replace(text, "projects", render_projects())
    text = replace(text, "publications", render_publications())
    text = replace(text, "pipeline", render_pipeline())
    README.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
