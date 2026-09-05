#!/usr/bin/env python3
"""Refresh academic-profile data and generated SVG cards.

The script intentionally uses only the Python standard library. It:
1. retrieves all public scholarly works from ORCID;
2. enriches DOI records with Crossref metadata when available;
3. classifies scholarly outputs into stable research-output groups;
4. retrieves citation metrics from OpenAlex using the ORCID identifier;
5. writes canonical publication and research-metric JSON files;
6. queries all public GitHub repositories owned by the user;
7. computes language composition and repository-type counts;
8. writes a complete public repository inventory for README tables;
9. generates repository-owned SVG cards.

README rendering is handled separately by scripts/render_profile.py so that
publication/project Markdown has one source of truth.
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
DATA_PATH = ROOT / "assets" / "data" / "publications.json"
METRICS_PATH = ROOT / "assets" / "data" / "research-metrics.json"
TYPE_CONFIG_PATH = ROOT / "assets" / "data" / "repository-types.json"
REPOSITORY_CATALOG_PATH = ROOT / "assets" / "data" / "repository-catalog.json"
SVG_DIR = ROOT / "assets" / "generated"

GITHUB_USER = os.getenv("GITHUB_USER", "qselmer")
ORCID_ID = os.getenv("ORCID_ID", "0000-0001-9229-6379")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
OPENALEX_API_KEY = os.getenv("OPENALEX_API_KEY", "")
CONTACT_EMAIL = os.getenv("CROSSREF_MAILTO", "qselmers@gmail.com")
USER_AGENT = f"qselmer-academic-profile/3.0 (mailto:{CONTACT_EMAIL})"

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

OUTPUT_TYPE_ORDER = [
    "Journal articles",
    "Preprints & working papers",
    "Conference outputs",
    "Books & chapters",
    "Theses",
    "Reports & technical outputs",
    "Data & software",
    "Other research outputs",
]

NAME_FALLBACKS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?:^|[-_.])paper$", re.I), "type-paper"),
    (re.compile(r"(?:^|[-_.])(app|dashboard)$", re.I), "type-app"),
    (re.compile(r"(?:^|[-_.])(report|assessment-report)$", re.I), "type-report"),
    (re.compile(r"(?:^|[-_.])(workflow|analysis|model|modelling|modeling)$", re.I), "type-workflow"),
    (
        re.compile(
            r"(labcore|training|course|mooc|lecture|tutorial|intro(?:duction)?|skills|class|aula|exam)",
            re.I,
        ),
        "type-training",
    ),
    (re.compile(r"(template|\.github\.io$|^qselmer$|^\.hub$|^\.template)", re.I), "type-infrastructure"),
]


def request_json(url: str, headers: dict[str, str] | None = None) -> Any:
    request_headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        request_headers.update(headers)
    request = urllib.request.Request(url, headers=request_headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def github_json(path: str) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
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


def normalise_work_type(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "-", safe_text(value).casefold()).strip("-")


def classify_output(record_or_type: dict[str, Any] | str) -> str:
    """Map ORCID/Crossref work types to stable profile-facing groups."""
    if isinstance(record_or_type, dict):
        work_type = normalise_work_type(record_or_type.get("type"))
    else:
        work_type = normalise_work_type(record_or_type)

    if work_type in {
        "journal-article",
        "journalarticle",
        "academic-journal-article",
    }:
        return "Journal articles"

    if work_type in {
        "preprint",
        "working-paper",
        "workingpaper",
        "submitted-manuscript",
    }:
        return "Preprints & working papers"

    if (
        work_type.startswith("conference")
        or work_type in {
            "conference-output",
            "conferenceoutput",
            "lecture-speech",
            "presentation",
            "poster",
        }
    ):
        return "Conference outputs"

    if work_type in {
        "book",
        "book-chapter",
        "bookchapter",
        "edited-book",
        "encyclopedia-entry",
        "dictionary-entry",
    }:
        return "Books & chapters"

    if work_type in {
        "dissertation-thesis",
        "dissertation",
        "thesis",
        "doctoral-thesis",
        "masters-thesis",
        "master-thesis",
    }:
        return "Theses"

    if work_type in {
        "report",
        "report-part",
        "policy-brief",
        "technical-standard",
        "standards-and-policy",
        "research-report",
    }:
        return "Reports & technical outputs"

    if work_type in {
        "data-set",
        "dataset",
        "software",
        "research-tool",
        "online-resource",
        "database",
        "code",
    }:
        return "Data & software"

    return "Other research outputs"


def output_type_counts(publications: list[dict[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for publication in publications:
        counts[classify_output(publication)] += 1
    return counts


def publishing_since(publications: list[dict[str, Any]]) -> str:
    years: list[int] = []
    for publication in publications:
        try:
            year = int(publication.get("year") or 0)
        except (TypeError, ValueError):
            continue
        if 1000 <= year <= 9999:
            years.append(year)
    return str(min(years)) if years else "—"


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
        raw_type = safe_text(work.get("type"))
        work_type = raw_type.replace("_", " ").replace("-", " ").title()
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
        name = " ".join(
            part
            for part in [safe_text(author.get("given")), safe_text(author.get("family"))]
            if part
        )
        if name:
            authors.append(name)

    date_parts = (
        (
            message.get("published-print")
            or message.get("published-online")
            or message.get("issued")
            or {}
        ).get("date-parts")
        or [[]]
    )
    year = str(date_parts[0][0]) if date_parts and date_parts[0] else ""

    return {
        "title": safe_text((message.get("title") or [""])[0]),
        "journal": safe_text((message.get("container-title") or [""])[0]),
        "year": year,
        "authors": authors,
        "url": safe_text(message.get("URL")),
        "type": safe_text(message.get("type")).replace("-", " ").title(),
        "volume": safe_text(message.get("volume")),
        "issue": safe_text(message.get("issue")),
        "pages": safe_text(message.get("page")),
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
        work["output_category"] = classify_output(work)
        merged[publication_key(work)] = work

    def sort_key(record: dict[str, Any]) -> tuple[int, str]:
        try:
            year = int(record.get("year") or 0)
        except ValueError:
            year = 0
        return year, record.get("title", "").lower()

    return sorted(merged.values(), key=sort_key, reverse=True)


def write_publications(publications: list[dict[str, Any]]) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    counts = output_type_counts(publications)
    payload = {
        "orcid": ORCID_ID,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(publications),
        "publishing_since": publishing_since(publications),
        "output_counts": {label: counts.get(label, 0) for label in OUTPUT_TYPE_ORDER},
        "publications": publications,
    }
    DATA_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _matching_openalex_author(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    candidates = payload.get("results") if isinstance(payload.get("results"), list) else [payload]
    wanted = ORCID_ID.casefold()
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        candidate_orcid = safe_text(candidate.get("orcid")).casefold()
        if wanted and wanted in candidate_orcid:
            return candidate
    if len(candidates) == 1 and isinstance(candidates[0], dict):
        return candidates[0]
    return {}


def openalex_author_metrics() -> dict[str, Any]:
    """Retrieve bibliometric metrics from OpenAlex, keyed strictly by ORCID.

    Several lookup forms are tried because OpenAlex supports both external-ID
    lookup and filtered author queries. A name-only match is deliberately not
    used for metrics to avoid author-identity errors.
    """
    orcid_url = f"https://orcid.org/{ORCID_ID}"
    encoded_orcid_url = urllib.parse.quote(orcid_url, safe="")
    base_params = {"mailto": CONTACT_EMAIL}
    if OPENALEX_API_KEY:
        base_params["api_key"] = OPENALEX_API_KEY
    direct_query = urllib.parse.urlencode(base_params)
    filter_plain = urllib.parse.urlencode({**base_params, "filter": f"orcid:{ORCID_ID}", "per_page": 5})
    filter_url = urllib.parse.urlencode({**base_params, "filter": f"orcid:{orcid_url}", "per_page": 5})
    urls = [
        f"https://api.openalex.org/authors/{encoded_orcid_url}?{direct_query}",
        f"https://api.openalex.org/authors?{filter_plain}",
        f"https://api.openalex.org/authors?{filter_url}",
    ]

    author: dict[str, Any] = {}
    last_error = ""
    for url in urls:
        try:
            candidate = _matching_openalex_author(request_json(url))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as exc:
            last_error = str(exc)
            continue
        if candidate:
            author = candidate
            break

    if not author:
        return {
            "available": False,
            "source": "OpenAlex",
            "error": last_error or "No ORCID-matched OpenAlex author record was found.",
        }

    summary = author.get("summary_stats") or {}
    return {
        "available": True,
        "source": "OpenAlex",
        "author_id": safe_text(author.get("id")),
        "display_name": safe_text(author.get("display_name")),
        "works_count": author.get("works_count"),
        "cited_by_count": author.get("cited_by_count"),
        "h_index": summary.get("h_index"),
        "i10_index": summary.get("i10_index"),
    }


def research_metrics_payload(publications: list[dict[str, Any]], openalex: dict[str, Any]) -> dict[str, Any]:
    counts = output_type_counts(publications)
    return {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "orcid": ORCID_ID,
        "public_orcid_works": len(publications),
        "journal_articles": counts.get("Journal articles", 0),
        "publishing_since": publishing_since(publications),
        "output_counts": {label: counts.get(label, 0) for label in OUTPUT_TYPE_ORDER},
        "openalex": openalex,
        "google_scholar_role": "profile-link-only",
    }


def write_research_metrics(publications: list[dict[str, Any]], openalex: dict[str, Any]) -> dict[str, Any]:
    payload = research_metrics_payload(publications, openalex)
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return payload


def github_repositories() -> list[dict[str, Any]]:
    """Return repositories visible on the public user endpoint.

    The public profile intentionally never publishes private-repository metadata.
    """
    repositories: list[dict[str, Any]] = []
    page = 1
    while True:
        batch = github_json(
            f"/users/{GITHUB_USER}/repos?type=owner&sort=updated&per_page=100&page={page}"
        )
        if not batch:
            break
        repositories.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repositories


def original_public_repositories(repositories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        repo
        for repo in repositories
        if not repo.get("fork") and not repo.get("private") and not repo.get("archived")
    ]


def language_totals(repositories: list[dict[str, Any]]) -> Counter[str]:
    totals: Counter[str] = Counter()
    for repo in original_public_repositories(repositories):
        try:
            languages = github_json(f"/repos/{repo['full_name']}/languages")
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
            continue
        for language, count in languages.items():
            totals[language] += int(count)
    return totals


def load_type_config() -> dict[str, Any]:
    try:
        return json.loads(TYPE_CONFIG_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {"canonical_types": {}, "legacy_type_aliases": {}, "overrides": {}}


def canonical_topic(repo: dict[str, Any], config: dict[str, Any]) -> str | None:
    canonical_types = config.get("canonical_types") or {}
    aliases = config.get("legacy_type_aliases") or {}
    topics = [str(x) for x in (repo.get("topics") or [])]
    canonical_hits = [topic for topic in topics if topic in canonical_types]
    alias_hits = [aliases[topic] for topic in topics if topic in aliases]
    hits = list(dict.fromkeys(canonical_hits + alias_hits))
    if len(hits) == 1:
        return hits[0]
    return None


def infer_repo_type(repo: dict[str, Any], config: dict[str, Any]) -> str | None:
    repo_type, _ = repository_classification(repo, config)
    return repo_type




def repository_classification(repo: dict[str, Any], config: dict[str, Any]) -> tuple[str | None, str]:
    """Return canonical repository type plus the rule used to classify it.

    Ambiguous multiple type topics are deliberately not guessed: they are sent to
    Other / legacy so that repository hygiene problems remain visible.
    """
    canonical_types = config.get("canonical_types") or {}
    aliases = config.get("legacy_type_aliases") or {}
    overrides = config.get("overrides") or {}
    topics = [str(x) for x in (repo.get("topics") or [])]

    canonical_hits = list(dict.fromkeys(topic for topic in topics if topic in canonical_types))
    alias_hits = list(dict.fromkeys(aliases[topic] for topic in topics if topic in aliases))
    hits = list(dict.fromkeys(canonical_hits + alias_hits))
    if len(hits) == 1:
        source = "topic" if canonical_hits else "legacy-topic"
        return hits[0], source
    if len(hits) > 1:
        return None, "multiple-type-topics"

    name = str(repo.get("name") or "")
    if name in overrides:
        override = str(overrides[name])
        if override in canonical_types:
            return override, "override"

    for pattern, repo_type in NAME_FALLBACKS:
        if pattern.search(name):
            return repo_type, "name-inference"
    return None, "unclassified"


def build_repository_catalog(repositories: list[dict[str, Any]]) -> dict[str, Any]:
    """Build an exhaustive inventory of public repositories owned by the user.

    Unlike the summary cards, the inventory intentionally retains public forks and
    archived repositories so they are visible during portfolio cleanup. Private
    repository metadata is never written to the public profile.
    """
    config = load_type_config()
    canonical_types = config.get("canonical_types") or {}
    items: list[dict[str, Any]] = []

    for repo in repositories:
        if repo.get("private"):
            continue
        repo_type, source = repository_classification(repo, config)
        label = canonical_types.get(repo_type, "Other / legacy")
        item = {
            "name": safe_text(repo.get("name")),
            "full_name": safe_text(repo.get("full_name")),
            "html_url": safe_text(repo.get("html_url")),
            "description": safe_text(repo.get("description")),
            "language": safe_text(repo.get("language")) or "—",
            "updated_at": safe_text(repo.get("updated_at")),
            "archived": bool(repo.get("archived")),
            "fork": bool(repo.get("fork")),
            "repository_type": repo_type or "",
            "repository_type_label": label,
            "classification_source": source,
            "topics": [str(x) for x in (repo.get("topics") or [])],
        }
        items.append(item)

    items.sort(key=lambda x: (x.get("fork", False), x.get("archived", False), x.get("repository_type_label", ""), x.get("name", "").casefold()))
    active_original = [x for x in items if not x["fork"] and not x["archived"]]
    archived_original = [x for x in items if not x["fork"] and x["archived"]]
    forks = [x for x in items if x["fork"]]
    other_legacy = [x for x in active_original if x["repository_type_label"] == "Other / legacy"]

    return {
        "schema_version": 1,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "owner": GITHUB_USER,
        "scope": "all public repositories owned by the user; private repositories excluded",
        "totals": {
            "public_repositories": len(items),
            "active_original_repositories": len(active_original),
            "archived_original_repositories": len(archived_original),
            "forks": len(forks),
            "other_or_legacy_active": len(other_legacy),
        },
        "repositories": items,
    }


def write_repository_catalog(repositories: list[dict[str, Any]]) -> dict[str, Any]:
    payload = build_repository_catalog(repositories)
    REPOSITORY_CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPOSITORY_CATALOG_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return payload


def repository_type_counts(repositories: list[dict[str, Any]]) -> Counter[str]:
    config = load_type_config()
    canonical_types = config.get("canonical_types") or {}
    counts: Counter[str] = Counter()
    for repo in original_public_repositories(repositories):
        repo_type = infer_repo_type(repo, config)
        label = canonical_types.get(repo_type, "Other / legacy")
        counts[label] += 1
    return counts


def svg_escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def card_svg(
    title: str,
    rows: list[tuple[str, str]],
    width: int = 410,
    min_height: int = 210,
) -> str:
    height = max(min_height, 54 + 29 * len(rows) + 18)
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


def format_metric(value: Any) -> str:
    if value is None or value == "":
        return "—"
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return str(value)


def generate_research_cards(publications: list[dict[str, Any]], metrics: dict[str, Any]) -> None:
    counts = output_type_counts(publications)
    output_rows = [(label, str(counts.get(label, 0))) for label in OUTPUT_TYPE_ORDER]

    openalex = metrics.get("openalex") or {}
    metric_rows = [
        ("Public ORCID works", format_metric(metrics.get("public_orcid_works"))),
        ("Journal articles", format_metric(metrics.get("journal_articles"))),
        ("Citations (OpenAlex)", format_metric(openalex.get("cited_by_count"))),
        ("h-index (OpenAlex)", format_metric(openalex.get("h_index"))),
        ("Publishing since", str(metrics.get("publishing_since") or "—")),
    ]

    SVG_DIR.mkdir(parents=True, exist_ok=True)
    (SVG_DIR / "research-outputs.svg").write_text(
        card_svg("Research Outputs", output_rows, min_height=333), encoding="utf-8"
    )
    (SVG_DIR / "research-metrics.svg").write_text(
        card_svg("Research Metrics", metric_rows, min_height=333), encoding="utf-8"
    )


def generate_github_cards() -> None:
    user = github_json(f"/users/{GITHUB_USER}")
    repositories = github_repositories()
    write_repository_catalog(repositories)
    originals = original_public_repositories(repositories)

    languages = language_totals(repositories)
    total_bytes = sum(languages.values()) or 1
    language_rows = [
        (language, f"{count / total_bytes:.1%}")
        for language, count in languages.most_common(8)
    ]
    if not language_rows:
        language_rows = [("No language data", "—")]

    type_counts = repository_type_counts(repositories)
    type_rows = [
        (label, str(type_counts.get(label, 0)))
        for label in VISIBLE_TYPE_ORDER
        if type_counts.get(label, 0) > 0 or label != "Other / legacy"
    ]
    type_rows = type_rows[:9]

    stars = sum(int(repo.get("stargazers_count", 0)) for repo in originals)
    forks = sum(int(repo.get("forks_count", 0)) for repo in originals)
    stats_rows = [
        ("Public repositories", str(user.get("public_repos", 0))),
        ("Original public repositories", str(len(originals))),
        ("Repository stars", str(stars)),
        ("Repository forks", str(forks)),
        ("Followers", str(user.get("followers", 0))),
    ]

    SVG_DIR.mkdir(parents=True, exist_ok=True)
    (SVG_DIR / "top-languages.svg").write_text(
        card_svg("Primary Languages", language_rows, min_height=333), encoding="utf-8"
    )
    (SVG_DIR / "repository-types.svg").write_text(
        card_svg("Repository Types", type_rows, min_height=333), encoding="utf-8"
    )
    # Retained as a generated compatibility asset, but not shown in the README.
    (SVG_DIR / "github-stats.svg").write_text(
        card_svg("GitHub Profile", stats_rows), encoding="utf-8"
    )


def existing_metrics() -> dict[str, Any]:
    try:
        payload = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def existing_publications() -> list[dict[str, Any]]:
    try:
        payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        publications = payload.get("publications") or []
        if isinstance(publications, list):
            for publication in publications:
                if isinstance(publication, dict):
                    publication["output_category"] = classify_output(publication)
            return publications
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return []


def main() -> int:
    try:
        publications = collect_publications()
    except Exception as exc:
        print(f"Warning: ORCID/Crossref metadata could not be refreshed: {exc}", file=sys.stderr)
        publications = existing_publications()

    write_publications(publications)

    previous_metrics = existing_metrics()
    try:
        openalex = openalex_author_metrics()
    except Exception as exc:
        print(f"Warning: OpenAlex metrics could not be refreshed: {exc}", file=sys.stderr)
        openalex = {"available": False, "source": "OpenAlex", "error": str(exc)}

    if not openalex.get("available"):
        previous_openalex = previous_metrics.get("openalex") or {}
        if previous_openalex.get("available"):
            openalex = {**previous_openalex, "stale": True, "refresh_warning": openalex.get("error", "OpenAlex refresh failed.")}

    metrics = write_research_metrics(publications, openalex)
    generate_research_cards(publications, metrics)
    generate_github_cards()

    try:
        catalog = json.loads(REPOSITORY_CATALOG_PATH.read_text(encoding="utf-8"))
        totals = catalog.get("totals") or {}
        print(
            "Public repository inventory: "
            f"{totals.get('public_repositories', 0)} total | "
            f"{totals.get('active_original_repositories', 0)} active originals | "
            f"{totals.get('archived_original_repositories', 0)} archived | "
            f"{totals.get('forks', 0)} forks | "
            f"{totals.get('other_or_legacy_active', 0)} other/legacy"
        )
    except Exception:
        pass

    print(f"Public ORCID works: {len(publications)}")
    if openalex.get("available"):
        print(f"OpenAlex citations: {openalex.get('cited_by_count', '—')} | h-index: {openalex.get('h_index', '—')}")
    else:
        print("OpenAlex metrics: unavailable on this refresh (profile retains ORCID-derived metrics).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
