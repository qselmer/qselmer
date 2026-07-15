#!/usr/bin/env python3
from __future__ import annotations

import json, os, re, urllib.error, urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / 'README.md'
PUBS = ROOT / 'assets/data/publications.json'
PROJECTS = ROOT / 'assets/data/featured-projects.json'
PIPELINE = ROOT / 'assets/data/research-pipeline.json'
TOKEN = os.getenv('GITHUB_TOKEN', '')
MAX_PUBLICATIONS = int(os.getenv('MAX_PUBLICATIONS', '5'))

MARKERS = {
    'publications': ('<!-- PUBLICATIONS:START -->', '<!-- PUBLICATIONS:END -->'),
    'projects': ('<!-- PROJECTS:START -->', '<!-- PROJECTS:END -->'),
    'pipeline': ('<!-- PIPELINE:START -->', '<!-- PIPELINE:END -->'),
}
STATUS = {
    'published': ('📄', 'Published'),
    'in_preparation': ('🔓', 'Manuscript in preparation'),
    'under_review': ('🔒', 'Manuscript submitted for publication'),
    'planned': ('💻', 'Planned study'),
}


def load(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def replace(text: str, key: str, body: str) -> str:
    start, end = MARKERS[key]
    pattern = re.compile(re.escape(start) + r'.*?' + re.escape(end), re.S)
    if not pattern.search(text):
        raise RuntimeError(f'Missing markers for {key}')
    return pattern.sub(f'{start}\n{body.rstrip()}\n{end}', text)


def github_repo(full_name: str) -> dict[str, Any]:
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'qselmer-profile'}
    if TOKEN:
        headers['Authorization'] = f'Bearer {TOKEN}'
    request = urllib.request.Request(f'https://api.github.com/repos/{full_name}', headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError):
        return {}


def initials(given: str) -> str:
    parts = re.findall(r'[^\W\d_]+', given, flags=re.UNICODE)
    return ' '.join(f'{part[0].upper()}.' for part in parts if part)


def is_elmer(name: str) -> bool:
    n = name.casefold()
    return 'quispe' in n and 'salazar' in n and ('elmer' in n or re.search(r'\be\.?\b', n))


def apa_name(name: str) -> str:
    name = re.sub(r'\s+', ' ', name.strip())
    if not name:
        return ''
    if ',' in name:
        family, given = [x.strip() for x in name.split(',', 1)]
    else:
        parts = name.split()
        family, given = (parts[-1], ' '.join(parts[:-1])) if len(parts) > 1 else (parts[0], '')
    value = f'{family}, {initials(given)}'.strip().rstrip(',')
    return f'**{value}**' if is_elmer(name) else value


def authors_apa(pub: dict[str, Any]) -> str:
    names = pub.get('authors') or ['Elmer Quispe-Salazar']
    values = [apa_name(str(name)) for name in names if str(name).strip()]
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f'{values[0]}, & {values[1]}'
    return f"{', '.join(values[:-1])}, & {values[-1]}"


def source_apa(pub: dict[str, Any]) -> str:
    journal = str(pub.get('journal') or pub.get('outlet') or pub.get('type') or '').strip()
    volume = str(pub.get('volume') or '').strip()
    issue = str(pub.get('issue') or '').strip()
    pages = str(pub.get('pages') or '').strip()
    if not journal:
        return ''
    source = f'*{journal}*'
    if volume:
        source = f'*{journal}, {volume}*'
    if issue:
        source += f'({issue})'
    if pages:
        source += f', {pages}'
    return source + '.'


def reference(pub: dict[str, Any]) -> str:
    status = str(pub.get('status') or 'published')
    icon, date_text = STATUS.get(status, STATUS['published'])
    year = str(pub.get('year') or 'n.d.')
    date = f'({year}).' if status == 'published' else f'({date_text}).'
    title = str(pub.get('title') or 'Untitled work').strip()
    parts = [f'- {icon} {authors_apa(pub)} {date} {title}.']
    source = source_apa(pub)
    if source:
        parts.append(source)
    url = str(pub.get('url') or '').strip()
    if url:
        label = str(pub.get('link_label') or ('View publication' if status == 'published' else 'View project'))
        parts.append(f'[{label}]({url})')
    return ' '.join(parts)


def render_publications() -> str:
    pubs = load(PUBS, {}).get('publications', [])
    return '\n'.join(reference({**pub, 'status': 'published'}) for pub in pubs[:MAX_PUBLICATIONS]) or '_Publication metadata is temporarily unavailable._'


def render_pipeline() -> str:
    items = load(PIPELINE, {}).get('items', [])
    order = {'under_review': 0, 'in_preparation': 1, 'planned': 2}
    items = sorted(items, key=lambda x: (order.get(x.get('status'), 9), x.get('title', '').lower()))
    return '\n'.join(reference(item) for item in items) or '_No pipeline items are currently listed._'


def render_projects() -> str:
    payload = load(PROJECTS, {'sections': []})
    lines: list[str] = []
    for section in payload.get('sections', []):
        lines += [f"### {section.get('title', 'Projects')}", '', '| Access | Project | Purpose | Main language | Stage |', '|---|---|---|---|---|']
        for item in section.get('items', []):
            repo = str(item.get('repository') or '')
            meta = github_repo(repo) if repo else {}
            private = bool(meta.get('private')) if meta else str(item.get('visibility', 'public')).lower() == 'private'
            access = '🔒 Private' if private else '🔓 Public'
            language = str(meta.get('language') or item.get('language') or '—')
            url = str(meta.get('html_url') or (f'https://github.com/{repo}' if repo and not private else ''))
            name = str(item.get('name') or repo.split('/')[-1])
            project = f'[`{name}`]({url})' if url and not private else f'`{name}`'
            purpose = str(item.get('purpose') or 'Scientific computing project.')
            stage = str(item.get('stage') or 'Active development')
            lines.append(f'| {access} | {project} | {purpose} | {language} | {stage} |')
        lines.append('')
    return '\n'.join(lines).rstrip() or '_No featured projects are configured._'


def main() -> None:
    text = README.read_text(encoding='utf-8')
    text = replace(text, 'projects', render_projects())
    text = replace(text, 'publications', render_publications())
    text = replace(text, 'pipeline', render_pipeline())
    README.write_text(text, encoding='utf-8')


if __name__ == '__main__':
    main()
