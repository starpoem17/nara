"""Run one planned grouping sweep with retained conditions and provenance."""
import argparse
from pathlib import Path
import sys
from nara.experiments import pipeline
from nara.experiments.recording import ROOT, Run


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grouping", nargs="+", choices=("groups12", "groups21"), default=["groups12"])
    parser.add_argument("--summary", default="grouping")
    parser.add_argument("--question", default="How do the planned grouping conditions affect dev200 judgments and runtime?")
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--smoke-only", action="store_true")
    parser.add_argument("--experiment", action="store_true", help="Treat a standalone preparation/smoke check as an explicit hypothesis experiment")
    parser.add_argument("--predecessor", help="Prior run ID when this execution follows observed results")
    parser.add_argument("--reason", help="Reason for the result-triggered additional execution")
    args = parser.parse_args(argv)
    if len(set(args.grouping)) != len(args.grouping):
        parser.error("Each grouping may appear only once in a sweep")
    phase = "preparation" if args.prepare_only else "smoke" if args.smoke_only else "full200"
    conditions = {name: {"grouping": name, "phase": phase, "output_tokens": 512,
                         "thinking": False, "seed": 0} for name in args.grouping}
    run = Run.create("inference-scheduling", args.summary, args.question, conditions,
        predecessor=args.predecessor, reason=args.reason,
        verification=phase != "full200" and not args.experiment,
        command=["nara-experiment", *(sys.argv[1:] if argv is None else argv)])
    try:
        sources = [p for p in (ROOT / "src").rglob("*") if p.is_file() and "__pycache__" not in p.parts]
        sources += [ROOT / p for p in ("pyproject.toml", "uv.lock", "data/dev.jsonl", "data/항목표.json", "data/정답스키마_디코딩.json")]
        run.capture(sources)
        run.reference([ROOT / "models/gemma-4-26B-A4B-it-NVFP4", ROOT / "models/bge-m3", ROOT / "model/legal_index"])
        run.compare_provenance()
        for grouping in args.grouping:
            with run.condition(grouping) as directory:
                pipeline.execute(directory, grouping, prepare_only=args.prepare_only, smoke_only=args.smoke_only)
        if phase == "full200" and len(args.grouping) == 2:
            from nara.evaluation.compare_dev_runs import compare
            compare(run.directory / "conditions" / args.grouping[0] / "attempt_1",
                    run.directory / "conditions" / args.grouping[1] / "attempt_1")
    except BaseException as exc:
        run = Run(run.directory)
        run.metadata.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        run.save()
        raise
    print(f"Run: {run.directory}\nReport: {run.report}")
    return run


if __name__ == "__main__":
    main()
