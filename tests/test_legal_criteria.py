"""Criteria provenance and prompt integration checks (not legal or accuracy validation)."""
import hashlib
import json
from pathlib import Path
import unittest

from nara.inference import Predictor
from test_inference import Model, Retriever, final, record

ROOT = Path(__file__).resolve().parents[1]


class LegalCriteriaTests(unittest.TestCase):
    def test_all_items_and_source_provenance(self):
        criteria = json.loads((ROOT / 'nara/legal_criteria.json').read_text())
        table = json.loads((ROOT / 'data/항목표.json').read_text())['항목']
        self.assertEqual(set(criteria['items']), set(table))
        for key, rule in criteria['items'].items():
            self.assertEqual(rule['name'], table[key]['항목명'])
            for field in ['applies_if', 'violation_if', 'exceptions']:
                self.assertTrue(rule[field].strip(), (key, field))
            self.assertTrue(rule['references'] or key == 'v24')
            for ref in rule['references']:
                self.assertIn(ref.split()[0], criteria['sources'])
        for source in criteria['sources'].values():
            path = ROOT / source['path']
            self.assertTrue(path.resolve().is_relative_to((ROOT / 'data/법령패키지').resolve()))
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), source['sha256'])

    def test_opt_in_group_scoping_and_input_isolation(self):
        table = json.loads((ROOT / 'data/항목표.json').read_text())['항목']
        schema = json.loads((ROOT / 'data/정답스키마_디코딩.json').read_text())['properties']['판정']
        baseline = Predictor(Model(final), Retriever(), table, schema)
        enriched = Predictor(Model(final), Retriever(), table, schema, legal_criteria=True)
        groups = [list(table)[:6], list(table)[6:12], list(table)[12:18], list(table)[18:]]
        for group in groups:
            old = baseline._messages(record(), group)
            new = enriched._messages(record(), group)
            self.assertEqual(old[1], new[1])
            self.assertNotIn('DO NOT LEAK', new[1]['content'])
            for key, rule in enriched.criteria['items'].items():
                if key in group:
                    self.assertIn(rule['violation_if'], new[0]['content'])
                else:
                    self.assertNotIn(f'[{key}] 적용:', new[0]['content'])
            self.assertNotIn('항목별 법령 판단 기준', old[0]['content'])
