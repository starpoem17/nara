"""Experiment prompt compression only; source documents and inference stay intact."""
import json
from pathlib import Path
from nara.inference.predictor import Predictor, compact

CRITERIA = json.loads(Path(__file__).with_name('compact_criteria.json').read_text())

class CompactPredictor(Predictor):
    def _messages(self, record, items):
        rules = '\n'.join(f'[{key}] {CRITERIA["items"][key]}' for key in items)
        # Explicit absence IDs only when assigned; no removed feature instructions.
        absence = ','.join(key for key in items if self.items[key]['부재탐지'])
        system = CRITERIA['common'] + f'\nAbsence items: {absence}.\n' + rules
        documents = '\n\n'.join(f"[{d['type']}:{d['doc_id']}]\n{d['text']}" for d in record['docs'])
        user = f"[공고 ID] {record['id']}\n[메타]\n" + compact(record['meta']) + '\n[문서]\n' + documents
        return [{'role': 'system', 'content': system}, {'role': 'user', 'content': user}]
