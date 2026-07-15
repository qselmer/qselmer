#!/usr/bin/env python3
"""Synchronize publications and generate local GitHub profile cards."""
from __future__ import annotations

import datetime as dt
import html
import json
import os
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
DATA_DIR = ROOT / "assets" / "data"
GENERATED_DIR = ROOT / "assets" / "generated"
ORCID = os.getenv("ORCID_ID", "0000-0001-9229-6379")
GITHUB_USER = os.getenv("GITHUB_USER", "qselmer")
CONTACT_EMAIL = os.getenv("OPENALEX_MAILTO", "qselmers@gmail.com")
TOKEN = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")

LANG_COLORS = {
    "R": "#198CE7", "Python": "#3572A5", "C++": "#f34b7d", "C": "#555555",
    "Julia": "#a270ba", "JavaScript": "#f1e05a", "HTML": "#e34c26",
    "CSS": "#563d7c", "Shell": "#89e051", "TeX": "#3D6117"
}


def request_json(url: str, *, github: bool = False) -> Any:
    headers = {"User-Agent": f"qselmer-profile/1.0 ({CONTACT_EMAIL})", "Accept": "application/json"}
    if github:
        headers["Accept"] = "application/vnd.github+json"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
        if TOKEN:
            headers["Authorization"] = f"Bearer {TOKEN}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def fetch_publications() -> list[dict[str, Any]]:
    author_url = f"https://api.openalex.org/authors/https://orcid.org/{ORCID}?mailto={urllib.parse.quote(CONTACT_EMAIL)}"
    author = request_json(author_url)
    author_id = author["id"].rsplit("/", 1)[-1]
    params = urllib.parse.urlencode({
        "filter": f"author.id:{author_id}",
        "sort": "publication_date:desc",
        "per-page": 100,
        "mailto": CONTACT_EMAIL,
    })
    payload = request_json(f"https://api.openalex.org/works?{params}")
    works: list[dict[str, Any]] = []
    for work in payload.get("results", []):
        title = (work.get("display_name") or "").strip()
        if not title:
            continue
        source = (((work.get("primary_location") or {}).get("source") or {}).get("display_name") or "")
        doi = (work.get("doi") or "").replace("https://doi.org/", "")
        authors = [
            ((entry.get("author") or {}).get("display_name") or "").strip()
            for entry in work.get("authorships", [])
        ]
        authors = [author for author in authors if author]
        works.append({
            "title": title,
            "year": work.get("publication_year"),
            "publication_date": work.get("publication_date"),
            "type": work.get("type"),
            "source": source,
            "doi": doi,
            "url": f"https://doi.org/{doi}" if doi else (work.get("id") or ""),
            "cited_by_count": int(work.get("cited_by_count") or 0),
            "authors": authors,
            "open_access": bool((work.get("open_access") or {}).get("is_oa")),
            "openalex_id": work.get("id"),
        })
    works.sort(key=lambda item: (item.get("publication_date") or "", item.get("title") or ""), reverse=True)
    return works


def author_line(authors: list[str], limit: int = 5) -> str:
    if not authors:
        return ""
    text = ", ".join(authors[:limit])
    return text + (", et al." if len(authors) > limit else "")


def update_publication_block(works: list[dict[str, Any]], n: int = 5) -> None:
    text = README.read_text(encoding="utf-8")
    start = "<!-- PUBLICATIONS:START -->"
    end = "<!-- PUBLICATIONS:END -->"
    if start not in text or end not in text:
        raise RuntimeError("Publication markers are missing from README.md")
    lines: list[str] = []
    for work in works[:n]:
        title = work["title"].replace("[", "\\[").replace("]", "\\]")
        url = work.get("url") or work.get("openalex_id")
        source = work.get("source") or "Scholarly work"
        year = work.get("year") or "n.d."
        citations = work.get("cited_by_count", 0)
        lines.append(f"- **[{title}]({url})** ({year}). *{source}*. OpenAlex citations: {citations}.")
        authors = author_line(work.get("authors") or [])
        if authors:
            lines.append(f"  {authors}")
    if not lines:
        lines = ["_No publications were returned by OpenAlex during the latest synchronization._"]
    replacement = start + "\n" + "\n".join(lines) + "\n" + end
    before, remainder = text.split(start, 1)
    _, after = remainder.split(end, 1)
    README.write_text(before + replacement + after, encoding="utf-8")


def fetch_github_data() -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, int]]:
    user = request_json(f"https://api.github.com/users/{GITHUB_USER}", github=True)
    repos: list[dict[str, Any]] = []
    page = 1
    while True:
        batch = request_json(
            f"https://api.github.com/users/{GITHUB_USER}/repos?per_page=100&page={page}&sort=updated",
            github=True,
        )
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    owned = [repo for repo in repos if not repo.get("fork") and not repo.get("archived")]
    languages: dict[str, int] = defaultdict(int)
    for repo in owned:
        language_url = repo.get("languages_url")
        if not language_url:
            continue
        try:
            for language, count in request_json(language_url, github=True).items():
                languages[language] += int(count)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
            continue
    return user, owned, dict(languages)


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def svg_card(title: str, rows: list[tuple[str, str]], width: int = 410, height: int = 190) -> str:
    parts: list[str] = []
    y = 68
    for label, value in rows:
        parts.append(f'<text x="24" y="{y}" class="label">{esc(label)}</text>')
        parts.append(f'<text x="{width - 24}" y="{y}" text-anchor="end" class="value">{esc(value)}</text>')
        y += 28
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">
<style>.card{{fill:#fff;stroke:#d0d7de}}.title{{font:600 18px -apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif;fill:#0969da}}.label{{font:400 14px -apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif;fill:#57606a}}.value{{font:600 14px -apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif;fill:#24292f}}@media(prefers-color-scheme:dark){{.card{{fill:#0d1117;stroke:#30363d}}.title{{fill:#58a6ff}}.label{{fill:#8b949e}}.value{{fill:#c9d1d9}}}}</style>
<rect class="card" x="0.5" y="0.5" rx="8" width="{width-1}" height="{height-1}"/><text x="24" y="36" class="title">{esc(title)}</text>{''.join(parts)}</svg>'''


def language_card(languages: dict[str, int], width: int = 410, height: int = 190) -> str:
    ranked = sorted(languages.items(), key=lambda item: item[1], reverse=True)[:5]
    if not ranked:
        return svg_card("Top Languages", [("Status", "Awaiting workflow run")], width, height)
    total = sum(value for _, value in ranked) or 1
    segments: list[str] = []
    labels: list[str] = []
    x = 24.0
    bar_width = width - 48
    for index, (name, count) in enumerate(ranked):
        percentage = count / total
        segment_width = bar_width * percentage
        color = LANG_COLORS.get(name, "#8c959f")
        segments.append(f'<rect x="{x:.1f}" y="58" width="{segment_width:.1f}" height="10" fill="{color}"/>')
        column = index % 2
        row = index // 2
        label_x = 24 + column * 190
        label_y = 96 + row * 28
        labels.append(f'<circle cx="{label_x+5}" cy="{label_y-5}" r="5" fill="{color}"/><text x="{label_x+17}" y="{label_y}" class="label">{esc(name)} {percentage*100:.1f}%</text>')
        x += segment_width
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Top programming languages"><style>.card{{fill:#fff;stroke:#d0d7de}}.title{{font:600 18px -apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif;fill:#0969da}}.label{{font:400 13px -apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif;fill:#24292f}}@media(prefers-color-scheme:dark){{.card{{fill:#0d1117;stroke:#30363d}}.title{{fill:#58a6ff}}.label{{fill:#c9d1d9}}}}</style><rect class="card" x="0.5" y="0.5" rx="8" width="{width-1}" height="{height-1}"/><text x="24" y="36" class="title">Top Languages</text><clipPath id="bar"><rect x="24" y="58" width="{bar_width}" height="10" rx="5"/></clipPath><g clip-path="url(#bar)">{''.join(segments)}</g>{''.join(labels)}</svg>'''


def write_cards(user: dict[str, Any] | None, repos: list[dict[str, Any]] | None, languages: dict[str, int] | None) -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    if user is None or repos is None:
        stats = svg_card("GitHub Stats", [("Status", "Awaiting workflow run"), ("Profile", f"@{GITHUB_USER}")])
        language_svg = language_card({})
    else:
        stars = sum(int(repo.get("stargazers_count") or 0) for repo in repos)
        forks = sum(int(repo.get("forks_count") or 0) for repo in repos)
        stats = svg_card("GitHub Stats", [
            ("Public original repositories", str(len(repos))),
            ("Repository stars", str(stars)),
            ("Repository forks", str(forks)),
            ("Followers", str(user.get("followers") or 0)),
            ("Updated", dt.datetime.now(dt.timezone.utc).date().isoformat()),
        ])
        language_svg = language_card(languages or {})
    (GENERATED_DIR / "github-stats.svg").write_text(stats, encoding="utf-8")
    (GENERATED_DIR / "top-languages.svg").write_text(language_svg, encoding="utf-8")


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    try:
        works = fetch_publications()
        payload = {"orcid": ORCID, "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(), "works": works}
        (DATA_DIR / "publications.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        update_publication_block(works)
    except Exception as exc:
        failures.append(f"Publications: {exc}")
    try:
        user, repos, languages = fetch_github_data()
        write_cards(user, repos, languages)
    except Exception as exc:
        failures.append(f"GitHub statistics: {exc}")
        write_cards(None, None, None)
    if failures:
        print("; ".join(failures), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
