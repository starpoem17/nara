"""Retained sweep identity, provenance, condition attempts, and report navigation."""
from contextlib import contextmanager
from datetime import datetime
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
TIMEZONE = ZoneInfo("Asia/Seoul")


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def relative_link(target, document):
    return Path(os.path.relpath(target, document.parent)).as_posix()


def add_link(index, target, description, intro):
    index.parent.mkdir(parents=True, exist_ok=True)
    content = index.read_text() if index.exists() else intro + "\n\n"
    link = f"[{'Run ' if target.stem != 'README' else ''}{target.parent.name if target.stem == 'README' else target.stem}](<{relative_link(target, index)}>)"
    if f"](<{relative_link(target, index)}>)" not in content:
        index.write_text(content.rstrip() + f"\n\n- {link}: {description}\n")


def replace_section(document, key, text):
    start, end = f"<!-- {key}:start -->", f"<!-- {key}:end -->"
    content = document.read_text()
    block = start + "\n" + text.rstrip() + "\n" + end
    if start in content:
        first = content.index(start)
        last = content.index(end, first) + len(end)
        content = content[:first] + block + content[last:]
    else:
        content = content.rstrip() + "\n\n" + block + "\n"
    document.write_text(content)


class Run:
    """One planned sweep; condition retries cannot change its frozen settings."""

    def __init__(self, directory):
        self.directory = Path(directory).resolve()
        self.path = self.directory / "run.json"
        self.metadata = json.loads(self.path.read_text())
        self.root = (self.directory / self.metadata.get("project_root", "../..")).resolve()
        self.report = self.root / self.metadata["report"]

    @classmethod
    def create(cls, area, summary, question, conditions, *, root=None,
               predecessor=None, reason=None, condition_changes=None,
               temporary_paths=(), command=None, max_attempts=1, verification=False):
        root = Path(root or ROOT).resolve()
        for value in (area, summary, *conditions):
            if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", value):
                raise ValueError(f"Invalid path identifier: {value}")
        if type(max_attempts) is not int or max_attempts < 1:
            raise ValueError("A positive planned attempt limit is required")
        if not question.strip() or not conditions:
            raise ValueError("A question and planned conditions are required")
        if predecessor and not reason:
            raise ValueError("A result-triggered follow-up requires a reason")
        if verification and predecessor:
            raise ValueError("Result-triggered experimental follow-ups must be recorded as experiments")
        prior = cls(root / "experiments" / predecessor) if predecessor else None
        started = datetime.now(TIMEZONE)
        base = started.strftime("%Y%m%d_%H%M%S_") + summary
        parent = root / ("docs/maintenance/evidence" if verification else "experiments")
        parent.mkdir(parents=True, exist_ok=True)
        collision = 1
        while True:
            identifier = base if collision == 1 else f"{base}_{collision}"
            directory = parent / identifier
            try:
                directory.mkdir()
                break
            except FileExistsError:
                collision += 1
        report = (root / "docs/maintenance/checks" / f"{identifier}.md" if verification else
                  root / "docs/experiments" / area / started.strftime("%Y-%m") / f"{identifier}.md")
        report.parent.mkdir(parents=True, exist_ok=True)
        metadata = {"schema_version": 1, "record_kind": "verification" if verification else "experiment",
            "project_root": os.path.relpath(root, directory), "run_id": identifier, "area": area,
            "question": question, "started_at": started.isoformat(), "timezone": str(TIMEZONE),
            "report": report.relative_to(root).as_posix(), "status": "prepared",
            "judgment": "not assessed", "max_attempts": max_attempts, "conditions": {
                name: {"settings": settings, "status": "pending", "attempts": []}
                for name, settings in conditions.items()},
            "predecessors": [], "followups": [], "temporary_paths": [str(Path(p).resolve()) for p in temporary_paths],
            "command": list(command or [sys.executable, *sys.argv]),
            "environment": {"python": sys.version, "platform": platform.platform(),
                "packages": {d.metadata["Name"]: d.version for d in importlib.metadata.distributions() if d.metadata["Name"]}},
            "sources": {}, "reproducibility": "Sources recorded; fresh inference reproducibility not verified."}
        report.write_text(f"# {question}\n\nCurrent judgment: **not assessed**. Execution success does not establish adoption.\n\n"
                          f"Run ID: `{identifier}`. Planned comparison: {', '.join(conditions)}.\n\n"
                          "## Question and conditions\n\n" + question + "\n\n"
                          "## Judgment history\n\nThe run was created with the conditions below; no results have been assessed.\n\n"
                          "## Limits\n\nDo not infer unseen-data performance or repeatability from one execution.\n")
        for name in conditions:
            (directory / "conditions" / name).mkdir(parents=True)
        write_json(directory / "run.json", metadata)
        run = cls(directory)
        if prior:
            before = {k: v["settings"] for k, v in prior.metadata["conditions"].items()}
            comparison = {"scope": "Declared execution settings only; source/input/assets not compared yet", "unchanged": [k for k in conditions if k in before and conditions[k] == before[k]],
                "changed": {k: {"before": before[k], "after": conditions[k]} for k in conditions if k in before and conditions[k] != before[k]},
                "added": {k: v for k, v in conditions.items() if k not in before},
                "removed": {k: v for k, v in before.items() if k not in conditions}}
            relation = {"run_id": predecessor, "reason": reason, "condition_changes": condition_changes or comparison}
            run.metadata["predecessors"].append(relation)
            prior.metadata.setdefault("followups", []).append({**relation, "run_id": identifier})
            prior.save()
        run.save()
        if verification:
            index = report.parent / "README.md"
            add_link(index, report, question, "# Task verification\n\nRoutine checks are not hypothesis experiments.")
            add_link(root / "docs/maintenance/README.md", index, "Routine preparation and smoke checks.", "# Maintenance")
            return run
        period = report.parent / "README.md"
        area_index = report.parent.parent / "README.md"
        global_experiments = root / "docs/experiments/README.md"
        add_link(period, report, question, f"# {area}: {started:%Y-%m}\n\nRun judgments and condition comparisons are recorded in the linked reports.")
        add_link(area_index, period, "Run reports and findings for this month.",
            f"# {area}\n\nScope: {question}\n\nOne preplanned comparison sweep is one run. Planned retries remain attempts. Any result-triggered additional execution receives a new ID, even with unchanged conditions.")
        add_link(global_experiments, area_index, question, "# Experiments")
        add_link(root / "docs/README.md", global_experiments, "Questions, sweeps, judgments, and retained evidence.", "# Project documentation")
        return run

    @classmethod
    def find(cls, path):
        path = Path(path).resolve()
        for directory in (path, *path.parents):
            if (directory / "run.json").is_file():
                return cls(directory)
        raise ValueError(f"No retained run metadata for {path}; create a run before writing its report")

    def save(self):
        write_json(self.path, self.metadata)
        m = self.metadata
        lines = ["## Execution evidence", "", f"Execution status: **{m['status']}**. Judgment: **{m['judgment']}**.", "",
                 f"[Run directory](<{relative_link(self.directory, self.report)}>) · [Metadata](<{relative_link(self.path, self.report)}>)", "",
                 "| Condition | Status | Attempts | Settings |", "|---|---|---:|---|"]
        for name, condition in m["conditions"].items():
            condition_path = self.directory / condition.get("artifact_path", f"conditions/{name}")
            lines.append(f"| [{name}](<{relative_link(condition_path, self.report)}>) | {condition['status']} | {len(condition['attempts'])} | `{json.dumps(condition['settings'], ensure_ascii=False)}` |")
        for kind in ("predecessors", "followups"):
            for relation in m.get(kind, []):
                linked = Run(self.root / "experiments" / relation["run_id"])
                lines += ["", f"{kind.title()}: [{relation['run_id']}](<{relative_link(linked.report, self.report)}>) — {relation['reason']}. Conditions: `{json.dumps({"declared": relation.get("condition_changes", {}), "provenance": relation.get("provenance_changes", "not compared")})}`"]
        for path in m.get("temporary_paths", []):
            lines += ["", f"Retained task temporary path: `{path}`."]
        lines += ["", m.get("reproducibility", "Reproduction has not been verified.")]
        replace_section(self.report, "execution", "\n".join(lines))

    def capture(self, paths):
        if self.metadata.get("read_only"):
            raise ValueError("Historical source evidence is read-only")
        if any(c["attempts"] for c in self.metadata["conditions"].values()):
            raise ValueError("Source evidence is frozen before execution; recapture is forbidden")
        for supplied in paths:
            source = Path(supplied)
            if not source.is_absolute():
                source = self.root / source
            relative = source.relative_to(self.root)
            target = self.directory / "source" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and target.read_bytes() != source.read_bytes():
                raise ValueError(f"Retained source cannot be overwritten: {relative}")
            shutil.copyfile(source, target)
            self.metadata["sources"][relative.as_posix()] = hashlib.sha256(target.read_bytes()).hexdigest()
        try:
            self.metadata["source_revision"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.root, stderr=subprocess.DEVNULL, text=True).strip()
            patch = subprocess.check_output(["git", "diff", "HEAD", "--binary", "--", "src", "pyproject.toml", "uv.lock", ".gitignore"], cwd=self.root)
        except subprocess.CalledProcessError:
            self.metadata["source_revision"] = None
            patch = b"Git revision unavailable; retained source contents are authoritative.\n"
        target = self.directory / "source/uncommitted.patch"
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.read_bytes() != patch:
            raise ValueError("Retained source patch cannot be overwritten")
        target.write_bytes(patch)
        self.metadata["source_patch"] = "source/uncommitted.patch"
        self.save()

    def capture_input(self, supplied):
        """Capture an evaluation input when it becomes available, without changing sources."""
        if self.metadata.get("read_only"):
            raise ValueError("Historical inputs are read-only; evaluate a retained verification copy")
        source = Path(supplied).resolve()
        relative = (source.relative_to(self.root) if source.is_relative_to(self.root) else
                    Path("external") / hashlib.sha256(str(source).encode()).hexdigest()[:16] / source.name)
        target = self.directory / "inputs" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.read_bytes() != source.read_bytes():
            raise ValueError("Retained input cannot be overwritten")
        shutil.copyfile(source, target)
        self.metadata.setdefault("inputs", {})[relative.as_posix()] = {
            "path": target.relative_to(self.directory).as_posix(),
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}
        self.save()

    def reference(self, directories):
        """Identify locally retained large assets without duplicating checkpoints."""
        if self.metadata.get("read_only") or any(c["attempts"] for c in self.metadata["conditions"].values()):
            raise ValueError("Asset evidence is frozen before execution")
        references = {}
        for directory in directories:
            folder = Path(directory).resolve()
            if not folder.exists():
                references[str(folder)] = {"available": False}
                continue
            entries = {}
            for path in ([folder] if folder.is_file() else sorted(folder.rglob("*"))):
                if path.is_file():
                    with path.open("rb") as stream:
                        entries[path.name if folder.is_file() else path.relative_to(folder).as_posix()] = {
                            "sha256": hashlib.file_digest(stream, "sha256").hexdigest(), "bytes": path.stat().st_size}
            references[str(folder)] = {"available": True, "files": entries,
                "access": "Retained locally; not Git-tracked. Restore matching bytes separately in another checkout."}
        self.metadata["asset_references"] = references
        self.save()

    def compare_provenance(self):
        """Record material content changes after sources and large assets are identified."""
        for relation in self.metadata["predecessors"]:
            prior = Run(self.root / "experiments" / relation["run_id"])
            differences = {}
            for field in ("sources", "inputs", "asset_references"):
                before, after = prior.metadata.get(field), self.metadata.get(field)
                if before is None or after is None:
                    differences[field] = {"status": "not comparable", "reason": "Evidence absent or not yet captured"}
                else:
                    differences[field] = {"status": "compared", "changed": [key for key in before.keys() | after.keys() if before.get(key) != after.get(key)],
                        "unchanged_count": sum(key in before and before[key] == value for key, value in after.items())}
            relation["provenance_changes"] = differences
            for reciprocal in prior.metadata.get("followups", []):
                if reciprocal["run_id"] == self.directory.name:
                    reciprocal["provenance_changes"] = differences
            prior.save()
        self.save()

    def require_active_attempt(self, directory, settings):
        path = Path(directory).resolve()
        for condition in self.metadata["conditions"].values():
            for attempt in condition["attempts"]:
                if (self.directory / attempt["path"]).resolve() == path:
                    if self.metadata.get("read_only") or attempt["status"] != "running" or condition["status"] != "running":
                        raise ValueError("Execution requires an active, writable attempt")
                    if any(condition["settings"].get(key) != value for key, value in settings.items()):
                        raise ValueError("Execution differs from the declared condition")
                    return
        raise ValueError("Execution requires a registered active attempt")

    @contextmanager
    def condition(self, name):
        if name not in self.metadata["conditions"]:
            raise ValueError("Condition was not declared in the original sweep")
        condition = self.metadata["conditions"][name]
        if condition["status"] == "complete" or len(condition["attempts"]) >= self.metadata["max_attempts"]:
            raise ValueError("Completed conditions are retained; additional execution requires a new run")
        directory = self.directory / "conditions" / name / f"attempt_{len(condition['attempts']) + 1}"
        directory.mkdir(parents=True)
        attempt = {"path": directory.relative_to(self.directory).as_posix(),
                   "started_at": datetime.now(TIMEZONE).isoformat(), "status": "running"}
        condition["attempts"].append(attempt)
        condition["status"] = self.metadata["status"] = "running"
        self.save()
        try:
            yield directory
        except BaseException as exc:
            attempt.update(status="failed", error=f"{type(exc).__name__}: {exc}")
            condition["status"] = self.metadata["status"] = "failed"
            raise
        else:
            attempt["status"] = condition["status"] = "complete"
            self.metadata["status"] = "complete" if all(c["status"] == "complete" for c in self.metadata["conditions"].values()) else "running"
        finally:
            attempt["finished_at"] = datetime.now(TIMEZONE).isoformat()
            self.metadata = json.loads(self.path.read_text())
            self.metadata["conditions"][name] = condition
            states = [c["status"] for c in self.metadata["conditions"].values()]
            self.metadata["status"] = "failed" if "failed" in states else "complete" if all(x == "complete" for x in states) else "running"
            self.save()
