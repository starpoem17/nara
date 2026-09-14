"""Verify both finished runs before reading labels, and freeze raw output hashes."""

if __name__ == "__main__":
    raise SystemExit("Archived code: create a fresh registered run; see docs/operations.md.")

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from statistics import mean

from experiments.legacy_CJH_original_cards_v10_v18_20260913.code.colleague_cards import FEATURES, RUNS, dump, install_input_guard, read_jsonl, sha
from experiments.legacy_CJH_original_cards_v10_v18_20260913.code.evaluate_colleague_cards import _preflight_suite


def audit():
    install_input_guard()
    bundles = {author: _preflight_suite(author, out) for author, out in RUNS.items()}
    verified_at = datetime.now(timezone.utc).isoformat()
    for author, bundle in bundles.items():
        out = bundle['out']
        features = FEATURES[author]
        tasks = bundle['requests']
        timings = {r['task_id']: r for r in bundle['timings']}
        submits, completions, active = {}, {}, set()
        refills_with_other_requests_active = 0
        submission_occupancy = Counter()
        last_time = 0
        for event in bundle['lifecycle']:
            task = event['task_id']
            assert event['time'] >= last_time
            last_time = event['time']
            if event['event'] == 'submit':
                assert task not in active and task not in submits
                if active and completions:
                    refills_with_other_requests_active += 1
                active.add(task)
                submits[task] = event
                submission_occupancy[len(active)] += 1
                assert event['thinking_budget'] is None
            else:
                assert task in active and task not in completions
                active.remove(task)
                completions[task] = event
            assert event['inflight'] == len(active) <= 16
        assert not active and set(submits) == set(completions) == set(tasks)
        for task, request in tasks.items():
            response, timing = bundle['responses'][task], timings[task]
            assert len(request['prompt_token_ids']) == request['input_tokens']
            assert response['input_tokens'] == timing['input_tokens'] == submits[task]['input_tokens'] == request['input_tokens']
            assert response['output_tokens'] == timing['output_tokens'] == len(response['token_ids']) <= 512
            assert request['input_tokens'] + 512 <= 36864
            assert timing['thinking_budget'] is None
            assert timing['finish_reason'] == response['finish_reason']
            assert 0 <= timing['cached_tokens'] <= timing['input_tokens']
            assert isinstance(response['decoded_with_special_tokens'], str)
            assert len(request['messages']) == 1 and request['messages'][0]['role'] == 'user'
            if request['feature'] != features[0]:
                seed = request['id'] + ':' + features[0]
                assert completions[seed]['time'] <= submits[task]['time']
        scheduler = read_jsonl(out / 'scheduler.jsonl')
        assert scheduler and max(r['running'] for r in scheduler) <= 16
        preflight = json.loads((out / 'preflight.json').read_text())
        admissions = [r for r in bundle['admissions'] if r['event'] == 'admit']
        assert [r['id'] for r in admissions] == list(preflight['common_prefix_tokens'])
        for event in admissions:
            assert len(event['live_ids']) <= 3
            total = sum(preflight['common_prefix_tokens'][rid] for rid in event['live_ids'])
            assert event['live_source_tokens'] == total <= 48000
        seed_rows = [timings[rid + ':' + features[0]] for rid in bundle['record_ids']]
        follower_rows = [row for task, row in timings.items() if tasks[task]['feature'] != features[0]]
        raw_hashes = {str(p.relative_to(out)): sha(p) for pattern in
                      ('responses/*.jsonl', 'request_timings.jsonl', 'lifecycle.jsonl', 'admissions.jsonl',
                       'scheduler.jsonl', 'runtime.json', 'manifest.json', 'preflight_verification.json',
                       'environment.json', 'initialization_attempts.json') for p in out.glob(pattern)}
        value = {
            'author': author, 'verified_at_before_labels': verified_at,
            'requests': len(tasks), 'records': len(bundle['record_ids']),
            'one_first_pass_per_notice_feature': True,
            'no_label_access': True, 'input_token_counts_match_frozen_requests': True,
            'all_outputs_within_512_tokens': True,
            'thinking_off_template_and_no_thinking_budget': True,
            'seed_completed_before_each_independent_follower': True,
            'refill_submissions_while_other_requests_active': refills_with_other_requests_active,
            'submission_occupancy_histogram': dict(sorted(submission_occupancy.items())),
            'peak_inflight': bundle['peak_inflight'],
            'peak_running': max(r['running'] for r in scheduler),
            'peak_waiting': max(r['waiting'] for r in scheduler),
            'peak_kv_usage': max(r['kv_usage'] for r in scheduler),
            'preempted_requests_stat_sum': sum(r['preempted_requests'] for r in scheduler),
            'mean_cached_tokens_seed': mean(r['cached_tokens'] for r in seed_rows),
            'mean_cached_tokens_follower': mean(r['cached_tokens'] for r in follower_rows),
            'raw_output_hashes_frozen_before_labels': raw_hashes,
            'audit_source_sha256': sha(__file__),
        }
        dump(out / 'runtime_verification.json', value)
        print(json.dumps({k: v for k, v in value.items() if k != 'raw_output_hashes_frozen_before_labels'}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    raise SystemExit("Archived experiment: create a new registered run; see docs/operations.md. Historical evidence is read-only.")
    audit()
