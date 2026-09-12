"""Share a notice's KV prefix; each feature-group conversation stays independent."""
from copy import deepcopy
import time
from nara.inference.compact_predictor import CompactPredictor, CRITERIA
from nara.inference.predictor import Prediction


class SourceFirstPredictor(CompactPredictor):
    def _messages(self, record, items):
        original = super()._messages(record, items)
        suffix = original[0]['content'][len(CRITERIA['common']):]
        return [{'role':'system','content':CRITERIA['common']},
                {'role':'user','content':original[1]['content']+'\n[판단 기준]\n'+suffix}]


def split_predictor(predictor, groups):
    keys = [k for group in groups for k in group]
    schema = deepcopy(predictor.judgment_schema)
    schema['properties'] = {k:schema['properties'][k] for k in keys}
    schema['required'] = keys
    return type(predictor)(predictor.model, predictor.retriever,
                           {k:predictor.items[k] for k in keys}, schema,
                           limits=predictor.limits)


def predict_notice(predictor, record, groups, phase_callback=None):
    """First group fills the prefix; the remaining groups reuse it in normal batches.

    No previous group response is added to any prompt. Do not clear the model's
    prefix cache between phases. Return one complete result plus phase metrics.
    """
    flat = [k for group in groups for k in group]
    if len(flat)!=len(set(flat)) or set(flat)!=set(predictor.items) or not all(groups):
        raise ValueError('Groups must partition predictor items')
    outputs, metrics = [], []
    phases = [('first',groups[:1]),('remaining',groups[1:])]
    for phase, selected in phases:
        if not selected:continue
        if phase_callback is not None:phase_callback(record['id'],phase)
        worker = split_predictor(predictor, selected)
        tick = time.monotonic()
        result = worker.predict([record],item_groups=selected)[0]
        metrics.append({'phase':phase,'seconds':time.monotonic()-tick,**worker.metrics})
        for task in result.trace:
            task['task_id'] = record['id']+':'+phase+':'+task['task_id']
        outputs.append(result)
    errors = [p.error for p in outputs if p.error]
    judgments = None if errors else {k:v for p in outputs for k,v in p.judgments.items()}
    return Prediction(record['id'],judgments,'; '.join(errors) or None,
                      [t for p in outputs for t in p.trace]), metrics
