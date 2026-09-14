"""Keep experiment reports in docs/ while artifacts retain their run paths."""
from pathlib import Path
import os
import re
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[2]


def report_path(artifact_path):
    """Map a report's former artifact path to its stable documentation path."""
    path = Path(artifact_path).resolve()
    if path.is_relative_to(ROOT / 'docs'):
        return path
    if path.is_relative_to(ROOT):
        relative = path.relative_to(ROOT)
    else:
        relative = Path('external') / path.relative_to(path.anchor)
    return ROOT / 'docs/reports' / relative


def relocate_links(text, original, destination):
    """Rebase local Markdown links, routing report links alongside reports."""
    original, destination = Path(original).resolve(), Path(destination).resolve()

    def replace(match):
        value = match.group(1)
        raw = value[1:-1] if value.startswith('<') else value
        url = urlsplit(raw)
        if url.scheme or url.netloc or not url.path or raw.startswith('/'):
            return match.group(0)
        target = (original.parent / unquote(url.path)).resolve()
        if (target.suffix == '.md'
                and target not in (ROOT / 'README.md', ROOT / 'AGENT.md')
                and not any(target.is_relative_to(ROOT / folder) for folder in ('docs', 'data', 'user', 'open'))
                and not {'source', 'analysis_source', 'original'}.intersection(target.parts)):
            target = report_path(target)
        relative = Path(os.path.relpath(target, destination.parent)).as_posix()
        if url.query:
            relative += '?' + url.query
        if url.fragment:
            relative += '#' + url.fragment
        return '](' + '<' + relative + '>' + ')'

    return re.sub(r'\]\((<[^>\n]+>|[^\s()]+)\)', replace, text)


def write_report(artifact_path, text):
    """Write a report and keep its links and artifact context usable."""
    original = Path(artifact_path).resolve()
    destination = report_path(original)
    text = relocate_links(text, original, destination)
    artifacts = Path(os.path.relpath(original.parent, destination.parent)).as_posix()
    note = (f'Artifacts: [run directory](<{artifacts}>). '
            'Unlinked artifact names below are relative to that directory.\n\n')
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(note + text, encoding='utf-8')
    return destination
