"""Locate current sources while retaining historical manifest identifiers."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Old manifests are immutable. Only live-file lookup follows the reorganization.
SOURCE_RELOCATIONS = {'nara/__init__.py': 'src/__init__.py',
 'nara/batch_barrier.py': 'src/inference/batch_barrier.py',
 'nara/briefing_rule.py': 'src/rules/briefing.py',
 'nara/compact_criteria.json': 'src/inference/compact_criteria.json',
 'nara/compact_predictor.py': 'src/inference/compact_predictor.py',
 'nara/continuous.py': 'src/inference/continuous.py',
 'nara/conversation.py': 'src/inference/conversation.py',
 'nara/hybrid_experiment.py': 'src/inference/hybrid_experiment.py',
 'nara/hypothesis6.py': 'src/rules/qualification.py',
 'nara/inference.py': 'src/inference/predictor.py',
 'nara/legal_criteria.json': 'src/inference/legal_criteria.json',
 'nara/legal_index.py': 'src/retrieval/index.py',
 'nara/prefix_pipeline.py': 'src/inference/prefix_pipeline.py',
 'nara/prefix_predictor.py': 'src/inference/prefix_predictor.py',
 'nara/prompt.txt': 'src/inference/prompt.txt',
 'nara/recovery.py': 'src/inference/recovery.py',
 'nara/retrieval.py': 'src/retrieval/search.py',
 'nara/vllm_model.py': 'src/inference/engine.py',
 'script.py': 'src/cli.py',
 'scripts/analyze_v9_cod.py': 'src/evaluation/analyze_v9_cod.py',
 'scripts/benchmark_colleague200.py': 'src/experiments/benchmark_colleague200.py',
 'scripts/benchmark_compact200.py': 'src/experiments/benchmark_compact200.py',
 'scripts/benchmark_continuous.py': 'src/experiments/benchmark_continuous.py',
 'scripts/benchmark_grouping_time.py': 'src/experiments/benchmark_grouping_time.py',
 'scripts/benchmark_hybrid200.py': 'src/experiments/benchmark_hybrid200.py',
 'scripts/benchmark_hybrid_batch_controls.py': 'src/experiments/benchmark_hybrid_batch_controls.py',
 'scripts/benchmark_on0.py': 'src/experiments/benchmark_on0.py',
 'scripts/benchmark_prefix200.py': 'src/experiments/benchmark_prefix200.py',
 'scripts/benchmark_prefix_pipeline.py': 'src/experiments/benchmark_prefix_pipeline.py',
 'scripts/check_dynamic_rag.py': 'src/tools/check_dynamic_rag.py',
 'scripts/check_engine_request_parity.py': 'src/tools/check_engine_request_parity.py',
 'scripts/check_gemma_inference.py': 'src/tools/check_gemma_inference.py',
 'scripts/check_legal_criteria.py': 'src/tools/check_legal_criteria.py',
 'scripts/check_legal_retrieval.py': 'src/tools/check_legal_retrieval.py',
 'scripts/compare_dev_runs.py': 'src/evaluation/compare_dev_runs.py',
 'scripts/compare_v9_cod_off.py': 'src/evaluation/compare_v9_cod_off.py',
 'scripts/diagnose_continuous.py': 'src/tools/diagnose_continuous.py',
 'scripts/evaluate_dev.py': 'src/evaluation/evaluate_dev.py',
 'scripts/evaluate_grouping_effect.py': 'src/evaluation/evaluate_grouping_effect.py',
 'scripts/experiment_cod_fewshot5.py': 'src/experiments/experiment_cod_fewshot5.py',
 'scripts/experiment_cod_legal.py': 'src/experiments/experiment_cod_legal.py',
 'scripts/experiment_cod_plain.py': 'src/experiments/experiment_cod_plain.py',
 'scripts/experiment_v9_cod_off.py': 'src/experiments/experiment_v9_cod_off.py',
 'scripts/experiment_v9_group.py': 'src/experiments/experiment_v9_group.py',
 'scripts/finalize_v9_cod_off.py': 'src/evaluation/finalize_v9_cod_off.py',
 'scripts/jsonl_to_md.py': 'src/tools/jsonl_to_md.py',
 'scripts/measure_token_lengths.py': 'src/tools/measure_token_lengths.py',
 'scripts/merge_thinking_recovery.py': 'src/evaluation/merge_thinking_recovery.py',
 'scripts/probe_prefill_decode.py': 'src/experiments/probe_prefill_decode.py',
 'scripts/recover_compact200.py': 'src/experiments/recover_compact200.py',
 'scripts/recover_compact_extended.py': 'src/experiments/recover_compact_extended.py',
 'scripts/recover_continuous.py': 'src/experiments/recover_continuous.py',
 'scripts/recover_hybrid200.py': 'src/experiments/recover_hybrid200.py',
 'scripts/recover_prefix_batch11.py': 'src/experiments/recover_prefix_batch11.py',
 'scripts/render_legal_criteria.py': 'src/tools/render_legal_criteria.py',
 'scripts/reporting.py': 'src/evaluation/reporting.py',
 'scripts/run_batch_fallback.py': 'src/experiments/run_batch_fallback.py',
 'scripts/run_continuous_study.py': 'src/experiments/run_continuous_study.py',
 'scripts/run_experiment.py': 'src/experiments/run_experiment.py',
 'scripts/summarize_colleague200.py': 'src/evaluation/summarize_colleague200.py',
 'scripts/summarize_common_prompt.py': 'src/evaluation/summarize_common_prompt.py',
 'scripts/summarize_compact200.py': 'src/evaluation/summarize_compact200.py',
 'scripts/summarize_continuous.py': 'src/evaluation/summarize_continuous.py',
 'scripts/summarize_continuous_diagnosis.py': 'src/evaluation/summarize_continuous_diagnosis.py',
 'scripts/summarize_gemma4_experiments.py': 'src/evaluation/summarize_gemma4_experiments.py',
 'scripts/summarize_grouping_time.py': 'src/evaluation/summarize_grouping_time.py',
 'scripts/summarize_hybrid200.py': 'src/evaluation/summarize_hybrid200.py',
 'scripts/summarize_on0.py': 'src/evaluation/summarize_on0.py',
 'scripts/summarize_prefill_decode.py': 'src/evaluation/summarize_prefill_decode.py',
 'scripts/summarize_prefix200.py': 'src/evaluation/summarize_prefix200.py',
 'scripts/summarize_prefix_batch11.py': 'src/evaluation/summarize_prefix_batch11.py',
 'scripts/summarize_prefix_pipeline.py': 'src/evaluation/summarize_prefix_pipeline.py',
 'scripts/summarize_singleton_groups.py': 'src/evaluation/summarize_singleton_groups.py',
 'scripts/validate_compact200.py': 'src/tools/validate_compact200.py',
 'scripts/verify_engine_refactor.py': 'src/tools/verify_engine_refactor.py',
 'scripts/verify_recovery_saved.py': 'src/tools/verify_recovery_saved.py'}


def source_path(name):
    """Resolve a current or historical repository-relative source path."""
    path = Path(name)
    return ROOT / SOURCE_RELOCATIONS.get(path.as_posix(), path)


def recorded_source_key(hashes, name):
    """Find the original key without changing a recorded source digest."""
    if name in hashes:
        return name
    for old, current in SOURCE_RELOCATIONS.items():
        if current == name and old in hashes:
            return old
    raise KeyError(name)
