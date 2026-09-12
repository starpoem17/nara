"""Run the unmodified colleague package with local checkpoint/kernel adaptation."""
import os
os.environ.setdefault('HF_HUB_OFFLINE','1')
os.environ.setdefault('TRANSFORMERS_OFFLINE','1')
os.environ.setdefault('MAX_JOBS','2')
os.environ.setdefault('TOKENIZERS_PARALLELISM','false')
import hashlib
import importlib.util
import json
from pathlib import Path
import time

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'analysis/colleague200'
MODEL=ROOT/'models/gemma-4-26B-A4B-it-NVFP4'


def main():
    start=time.monotonic()
    if (OUT/'submission.csv').exists():raise ValueError('Existing output; refusing overwrite')
    spec=importlib.util.spec_from_file_location('colleague_original',OUT/'original/src/cli.py')
    original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
    prompts=[];calls=[];requests=[];engine={};stage_times={}
    original_fit=original.fit_to_budget
    def observed_fit(rec,*args,**kwargs):
        result=original_fit(rec,*args,**kwargs)
        msgs,tokens,chars=result
        prompts.append({'id':rec['id'],'messages':msgs,'counted_tokens':tokens,'max_chars':chars})
        return result
    original.fit_to_budget=observed_fit
    original_index=original.configure_law_index
    def observed_index(*args,**kwargs):
        tick=time.monotonic();result=original_index(*args,**kwargs)
        stage_times['law_index_seconds']=time.monotonic()-tick
        stage_times['law_articles']=len(original._LAW_INDEX_CACHE.articles) if original._LAW_INDEX_CACHE else 0
        return result
    original.configure_law_index=observed_index

    class ObservedLLM:
        def __init__(self,llm):self.llm=llm
        def __getattr__(self,k):return getattr(self.llm,k)
        def chat(self,batch,*args,**kwargs):
            tick=time.monotonic()
            try:outputs=self.llm.chat(batch,*args,**kwargs)
            except Exception as exc:
                calls.append({'batch_size':len(batch),'seconds':time.monotonic()-tick,'error':repr(exc)})
                raise
            calls.append({'batch_size':len(batch),'seconds':time.monotonic()-tick,'error':None})
            for messages,output in zip(batch,outputs):
                completion=output.outputs[0] if output.outputs else None
                request={'request_id':output.request_id,'id':messages[1]['content'].splitlines()[0].removeprefix('[공고 ID] '),
                         'input_tokens':len(output.prompt_token_ids),'cached_tokens':output.num_cached_tokens,
                         'output_tokens':len(completion.token_ids) if completion else 0,
                         'finish_reason':completion.finish_reason if completion else None,
                         'response':completion.text if completion else ''}
                requests.append(request)
            return outputs

    class LocalRunner(original.VLLMRunner):
        def __init__(self,*args,**kwargs):
            import vllm
            stock=vllm.LLM
            def local_llm(**options):
                # Native local NVFP4 needs this backend on Blackwell; preserve all other defaults.
                options['kernel_config']={'moe_backend':'cutlass'}
                engine['requested_options']=options.copy()
                llm=stock(**options)
                cfg=llm.llm_engine.vllm_config
                engine['resolved']={
                    'max_model_len':cfg.model_config.max_model_len,
                    'quantization':cfg.model_config.quantization,
                    'max_num_seqs':cfg.scheduler_config.max_num_seqs,
                    'max_num_batched_tokens':cfg.scheduler_config.max_num_batched_tokens,
                    'enable_prefix_caching':cfg.cache_config.enable_prefix_caching,
                    'gpu_memory_utilization':cfg.cache_config.gpu_memory_utilization,
                    'reasoning_parser':cfg.structured_outputs_config.reasoning_parser}
                return ObservedLLM(llm)
            vllm.LLM=local_llm
            try:super().__init__(*args,**kwargs)
            finally:vllm.LLM=stock
            # Assert current checkpoint's default template is thinking OFF; no template override.
            sample=[{'role':'user','content':'test'}]
            default=self.tok.apply_chat_template(sample,tokenize=False,add_generation_prompt=True)
            off=self.tok.apply_chat_template(sample,tokenize=False,add_generation_prompt=True,enable_thinking=False)
            engine['default_template_matches_thinking_off']=default==off
            stage_times['runner_load_seconds']=self.load_seconds
        def chat(self,batch):
            if 'inference_start' not in stage_times:stage_times['inference_start']=time.monotonic()-start
            return super().chat(batch)

    tick=time.monotonic()
    report=original.run(str(ROOT/'data/dev.jsonl'),str(OUT/'submission.csv'),LocalRunner,
                        limit=200,chunk=128,max_chars=12000,data_dir=str(ROOT/'data'),
                        model_dir=str(MODEL),quant=None,max_tokens=1536,seed=original.SEED,gpu_mem=0.92,tp=1)
    run_seconds=time.monotonic()-tick
    measured_seconds=time.monotonic()-start
    report.update({'run_seconds_precise':run_seconds,'wrapper_seconds_before_artifact_serialization':measured_seconds,
                   'stage_times':stage_times,'engine':engine,
                   'local_adaptations':['PPS model path uses existing local NVFP4 checkpoint; quant=None auto-detects checkpoint quantization.',
                                        'kernel_config.moe_backend=cutlass for local Blackwell NVFP4.',
                                        'Pass-through observers record prompts, requests and durations; original source unchanged.'],
                   'reported_competition_minutes':75,'competition_timing_source':'user report; timing scope/count pending clarification',
                   'model_chat_seconds':sum(c['seconds'] for c in calls),
                   'model_calls':len(calls),'successful_outputs':len(requests),
                   'input_tokens':sum(r['input_tokens'] for r in requests),
                   'output_tokens':sum(r['output_tokens'] for r in requests),
                   'cached_input_tokens':sum(r['cached_tokens'] or 0 for r in requests),
                   'cache_counts_available':all(r['cached_tokens'] is not None for r in requests)})
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    (OUT/'model_calls.json').write_text(json.dumps(calls,ensure_ascii=False,indent=2)+'\n')
    for filename,rows in [('prompts.jsonl',prompts),('responses.jsonl',requests)]:
        (OUT/filename).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
    originals=json.loads((OUT/'archive_manifest.json').read_text())
    assert all(hashlib.sha256((OUT/'original'/r['local_path']).read_bytes()).hexdigest()==r['sha256'] for r in originals['files'])
    print(json.dumps({'stage':'complete','run_seconds':run_seconds,'report':report},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
