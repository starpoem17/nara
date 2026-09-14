"""Default dev200 experiment: twelve OFF groups, cross-notice prefill, engine16."""
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.benchmark_prefix_pipeline import main as run_pipeline


def main(argv=None):
    output = Path('output/experiments') / datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    run_pipeline(argv, verify_reference=False, default_output=output)


if __name__ == '__main__':
    main()
