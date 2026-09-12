"""Replay a relocated experiment without editing its frozen source snapshots."""
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['score', 'audit', 'run'])
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    previous = 'ljm_static_law_v2_v8_20260912'
    filename = {'score': 'score.py', 'audit': 'audit_extraction.py', 'run': 'run.py'}[args.stage]
    snapshot = root / 'source' / filename
    # Only presentation/output paths change in memory; original bytes/hashes stay intact.
    code = snapshot.read_text().replace(previous, root.name)
    code = code.replace(f'analysis/{root.name}/source/score.py',
                        f'analysis/{root.name}/reproduce.py score')
    namespace = {'__name__': '_relocated_experiment', '__file__': str(snapshot)}
    exec(compile(code, str(snapshot), 'exec'), namespace)
    if args.stage == 'score':
        namespace['main']()
    elif args.stage == 'run':
        namespace['run']()
    # The original audit module runs its checks at module scope.


if __name__ == '__main__':
    main()
