"""Run token-budget pilots sequentially, then verify the fastest on full200."""
import json
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path('analysis/continuous200')
for budget in [8192,2048,16384]:
    with (ROOT/f'pilot_{budget}.log').open('w') as log:
        subprocess.run([sys.executable,'src/experiments/benchmark_continuous.py','--kind','pilot','--tokens',str(budget)],stdout=log,stderr=subprocess.STDOUT,check=True)
    print(json.dumps({'stage':'pilot_complete','tokens':budget}),flush=True)
reports=[json.loads((ROOT/f'pilot_continuous_{b}/report.json').read_text()) for b in [8192,2048,16384]]
valid=[r for r in reports if not r['failed_ids']]
if not valid:raise RuntimeError('No clean pilot; inspect failures before full runs')
winner=min(valid,key=lambda r:r['prediction_seconds'])['engine']['max_num_batched_tokens']
(ROOT/'selection.json').write_text(json.dumps({'selected_tokens':winner,'criterion':'Lowest measured continuous pilot walltime among complete runs; scores not used','pilot_seconds':{r['engine']['max_num_batched_tokens']:r['prediction_seconds'] for r in reports}},indent=2)+'\n')
for kind in ['six','mixed']:
    with (ROOT/f'{kind}_{winner}.log').open('w') as log:
        subprocess.run([sys.executable,'src/experiments/benchmark_continuous.py','--kind',kind,'--tokens',str(winner)],stdout=log,stderr=subprocess.STDOUT,check=True)
    print(json.dumps({'stage':'full_complete','kind':kind,'tokens':winner}),flush=True)
