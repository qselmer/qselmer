#!/usr/bin/env python3
"""Update the academic GitHub profile using GitHub, ORCID and Crossref metadata.

The script has no third-party Python dependencies. It:
1. retrieves public scholarly works associated with the configured ORCID;
2. enriches DOI records with Crossref metadata when available;
3. writes a canonical publications JSON file;
4. replaces the publication block in README.md;
5. generates repository-owned SVG cards for languages and profile statistics.
"""

from __future__ import annotations

import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
README_PATH = ROOT / "README.md"
DATA_PATH = ROOT / "assets" / "data" / "publications.json"
SVG_DIR = ROOT / "assets" / "generated"

GITHUB_USER = os.getenv("GITHUB_USER", "qselmer")
ORCID_ID = os.getenv("ORCID_ID", "0000-0001-9229-6379")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
CONTACT_EMAIL = os.getenv("CROSSREF_MAILTO", "qselmers@gmail.com")
MAX_PUBLICATIONS = int(os.getenv("MAX_PUBLICATIONS", "5"))

START_MARKER = "<!-- PUBLICATIONS:START -->"
END_MARKER = "<!-- PUBLICATIONS:END -->"
USER_AGENT = f"qselmer-academic-profile/1.0 (mailto:{CONTACT_EMAIL})"


def request_json(url: str, headers: dict[str, str] | None = None) -> Any:
    request_headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        request_headers.update(headers)
    request = urllib.request.Request(url, headers=request_headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def github_json(path: str) -> Any:
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return request_json(f"https://api.github.com{path}", headers)


def safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, dict):
        value = value.get("value", default)
    return str(value).strip()


def normalise_doi(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"^https?://(dx\.)?doi\.org/", "", value)
    return value


def orcid_works() -> list[dict[str, Any]]:
    url = f"https://pub.orcid.org/v3.0/{ORCID_ID}/works"
    payload = request_json(url, {"Accept": "application/vnd.orcid+json"})
    records: list[dict[str, Any]] = []

    for group in payload.get("group", []):
        summaries = group.get("work-summary", [])
        if not summaries:
            continue
        work = summaries[0]
        title_data = (work.get("title") or {}).get("title") or {}
        title = safe_text(title_data)
        if not title:
            continue

        year = safe_text(((work.get("publication-date") or {}).get("year") or {}))
        journal = safe_text(work.get("journal-title"))
        work_type = safe_text(work.get("type")).replace("_", " ").title()
        url_value = safe_text(work.get("url"))
        doi = ""

        for external_id in (work.get("external-ids") or {}).get("external-id", []):
            if safe_text(external_id.get("external-id-type")).lower() == "doi":
                doi = normalise_doi(safe_text(external_id.get("external-id-value")))
                break

        records.append(
            {
                "title": title,
                "year": year,
                "journal": journal,
                "type": work_type,
                "doi": doi,
                "url": url_value or (f"https://doi.org/{doi}" if doi else ""),
                "authors": [],
                "source": "ORCID",
            }
        )
    return records


def crossref_metadata(doi: str) -> dict[str, Any]:
    if not doi:
        return {}
    encoded = urllib.parse.quote(doi, safe="")
    url = f"https://api.crossref.org/works/{encoded}?mailto={urllib.parse.quote(CONTACT_EMAIL)}"
    try:
        message = request_json(url).get("message", {})
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError):
        return {}

    authors = []
    for author in message.get("author", []):
        name = " ".join(part for part in [safe_text(author.get("given")), safe_text(author.get("family"))] if part)
        if name:
            authors.append(name)

    date_parts = ((message.get("published-print") or message.get("published-online") or message.get("issued") or {}).get("date-parts") or [[]])
    year = str(date_parts[0][0]) if date_parts and date_parts[0] else ""

    return {
        "title": safe_text((message.get("title") or [""])[0]),
        "journal": safe_text((message.get("container-title") or [""])[0]),
        "year": year,
        "authors": authors,
        "url": safe_text(message.get("URL")),
        "type": safe_text(message.get("type")).replace("-", " ").title(),
        "source": "ORCID + Crossref",
    }


def publication_key(record: dict[str, Any]) -> str:
    if record.get("doi"):
        return f"doi:{record['doi']}"
    title = re.sub(r"[^a-z0-9]+", "", record.get("title", "").lower())
    return f"title:{title}"


def collect_publications() -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for work in orcid_works():
        enriched = crossref_metadata(work.get("doi", ""))
        for field, value in enriched.items():
            if value:
                work[field] = value
        merged[publication_key(work)] = work

    def sort_key(record: dict[str, Any]) -> tuple[int, str]:
        try:
            year = int(record.get("year") or 0)
        except ValueError:
            year = 0
        return year, record.get("title", "").lower()

    return sorted(merged.values(), key=sort_key, reverse=True)


def publication_markdown(publications: list[dict[str, Any]]) -> str:
    lines = [START_MARKER]
    if not publications:
        lines.append("_Publication metadata is temporarily unavailable. See the complete record on the academic website._")
    for pub in publications[:MAX_PUBLICATIONS]:
        title = pub.get("title") or "Untitled work"
        url = pub.get("url") or "https://qselmer.github.io/publications/"
        journal = pub.get("journal") or pub.get("type") or "Scholarly work"
        year = pub.get("year") or "n.d."
        authors = pub.get("authors") or []
        lines.append(f"- **[{title}]({url})**. *{journal}* ({year}).")
        if authors:
            lines.append(f"  <br><sub>{', '.join(authors)}</sub>")
    lines.append(END_MARKER)
    return "\n".join(lines)


def update_readme(publications: list[dict[str, Any]]) -> None:
    text = README_PATH.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER), re.DOTALL)
    replacement = publication_markdown(publications)
    if not pattern.search(text):
        raise RuntimeError("README publication markers were not found")
    README_PATH.write_text(pattern.sub(replacement, text), encoding="utf-8")


def github_repositories() -> list[dict[str, Any]]:
    repositories: list[dict[str, Any]] = []
    page = 1
    while True:
        batch = github_json(f"/users/{GITHUB_USER}/repos?type=owner&sort=updated&per_page=100&page={page}")
        if not batch:
            break
        repositories.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repositories


def language_totals(repositories: list[dict[str, Any]]) -> Counter[str]:
    totals: Counter[str] = Counter()
    for repo in repositories:
        if repo.get("fork") or repo.get("archived") or repo.get("private"):
            continue
        try:
            languages = github_json(f"/repos/{repo['full_name']}/languages")
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
            continue
        for language, count in languages.items():
            totals[language] += int(count)
    return totals


def svg_escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def card_svg(title: str, rows: list[tuple[str, str]], width: int = 410, height: int = 210) -> str:
    row_markup = []
    y = 72
    for label, value in rows:
        row_markup.append(
            f'<text x="24" y="{y}" class="label">{svg_escape(label)}</text>'
            f'<text x="{width - 24}" y="{y}" text-anchor="end" class="value">{svg_escape(value)}</text>'
        )
        y += 29
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" role="img" aria-label="{svg_escape(title)}">
<style>
  .card {{ fill: #ffffff; stroke: #d0d7de; }}
  .title {{ font: 600 18px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill: #0969da; }}
  .label {{ font: 14px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill: #24292f; }}
  .value {{ font: 600 14px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill: #0969da; }}
  @media (prefers-color-scheme: dark) {{
    .card {{ fill: #0d1117; stroke: #30363d; }}
    .title, .value {{ fill: #58a6ff; }}
    .label {{ fill: #c9d1d9; }}
  }}
</style>
<rect class="card" x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="8"/>
<text x="24" y="37" class="title">{svg_escape(title)}</text>
{''.join(row_markup)}
</svg>'''


def generate_cards() -> None:
    user = github_json(f"/users/{GITHUB_USER}")
    repositories = github_repositories()
    owned_public = [repo for repo in repositories if not repo.get("fork") and not repo.get("private")]
    stars = sum(int(repo.get("stargazers_count", 0)) for repo in owned_public)
    forks = sum(int(repo.get("forks_count", 0)) for repo in owned_public)

    languages = language_totals(repositories)
    total_bytes = sum(languages.values()) or 1
    language_rows = [
        (language, f"{count / total_bytes:.1%}")
        for language, count in languages.most_common(5)
    ]
    if not language_rows:
        language_rows = [("No language data", "—")]

    stats_rows = [
        ("Public repositories", str(user.get("public_repos", 0))),
        ("Original public repositories", str(len(owned_public))),
        ("Repository stars", str(stars)),
        ("Repository forks", str(forks)),
        ("Followers", str(user.get("followers", 0))),
    ]

    SVG_DIR.mkdir(parents=True, exist_ok=True)
    (SVG_DIR / "top-languages.svg").write_text(card_svg("Top Languages", language_rows), encoding="utf-8")
    (SVG_DIR / "github-stats.svg").write_text(card_svg("GitHub Profile", stats_rows), encoding="utf-8")


def write_publications(publications: list[dict[str, Any]]) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "orcid": ORCID_ID,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(publications),
        "publications": publications,
    }
    DATA_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    try:
        publications = collect_publications()
    except Exception as exc:  # preserve existing publication block on remote API failure
        print(f"Warning: publication metadata could not be refreshed: {exc}", file=sys.stderr)
        publications = []

    if publications:
        write_publications(publications)
        update_readme(publications)
    elif not DATA_PATH.exists():
        write_publications([])

    generate_cards()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
