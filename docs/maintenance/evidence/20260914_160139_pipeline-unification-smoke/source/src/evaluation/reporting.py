"""Write generated sections into the owning run's single canonical report."""
from pathlib import Path
import hashlib
import os
import re
from urllib.parse import unquote, urlsplit
from nara.experiments.recording import ROOT, Run, replace_section


def report_path(artifact_path):
    path = Path(artifact_path).resolve()
    try:
        return Run.find(path).report
    except ValueError:
        if path.is_relative_to(ROOT / "docs"):
            return path
        raise


def relocate_links(text, original, destination):
    original, destination = Path(original).resolve(), Path(destination).resolve()
    def replace(match):
        raw = match.group(1).strip("<>")
        url = urlsplit(raw)
        if url.scheme or url.netloc or not url.path or raw.startswith("/"):
            return match.group(0)
        target = (original.parent / unquote(url.path)).resolve()
        if target.suffix == ".md" and not target.exists():
            try:
                target = report_path(target)
            except ValueError:
                pass
        relative = Path(os.path.relpath(target, destination.parent)).as_posix()
        if url.query:
            relative += "?" + url.query
        if url.fragment:
            relative += "#" + url.fragment
        return "](<" + relative + ">)"
    return re.sub(r"\]\((<[^>\n]+>|[^\s()]+)\)", replace, text)


def write_report(artifact_path, text):
    original = Path(artifact_path).resolve()
    destination = report_path(original)
    text = relocate_links(text, original, destination)
    if original == destination:
        for metadata in (ROOT / "experiments").glob("*/run.json"):
            if Run(metadata.parent).report == destination:
                raise ValueError("Canonical run reports cannot be overwritten; write a generated artifact section")
        for metadata in (ROOT / "docs/maintenance/evidence").glob("*/run.json"):
            if Run(metadata.parent).report == destination:
                raise ValueError("Canonical verification reports cannot be overwritten")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding="utf-8")
        return destination
    run = Run.find(original)
    if run.metadata.get("read_only"):
        raise ValueError("Historical evidence is read-only; create a verification copy")
    section = original.relative_to(run.directory).as_posix()
    key = "generated-" + hashlib.sha256(section.encode()).hexdigest()[:16]
    artifacts = Path(os.path.relpath(original.parent, destination.parent)).as_posix()
    note = f"## {section}\n\nArtifacts: [condition directory](<{artifacts}>).\n\n"
    replace_section(destination, key, note + text)
    return destination
