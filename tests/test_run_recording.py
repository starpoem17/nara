"""Retained sweep and follow-up behavior through the common recording interface."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo
from nara.experiments.recording import Run


class RunRecordingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def create(self, **kwargs):
        return Run.create("scheduling", "comparison", "Compare grouping", {"groups12": {"tokens": 512}, "groups21": {"tokens": 512}}, root=self.root, **kwargs)

    def test_one_sweep_has_independent_conditions_and_does_not_imply_adoption(self):
        run = self.create()
        for name in ("groups12", "groups21"):
            with run.condition(name) as directory:
                (directory / "result.json").write_text('{"ok":true}')
        saved = Run(run.directory)
        self.assertEqual(saved.metadata["status"], "complete")
        self.assertEqual(saved.metadata["judgment"], "not assessed")
        self.assertEqual(len(list((self.root / "docs/experiments/scheduling").rglob(run.directory.name + ".md"))), 1)
        self.assertIn(run.report.name, (run.report.parent / "README.md").read_text())
        with self.assertRaisesRegex(ValueError, "new run"):
            with run.condition("groups12"):
                pass

    def test_failure_retains_evidence_and_only_declared_retries_are_allowed(self):
        run = self.create(max_attempts=2)
        with self.assertRaisesRegex(RuntimeError, "failure"):
            with run.condition("groups12") as failed:
                (failed / "partial.json").write_text("partial")
                raise RuntimeError("failure")
        self.assertEqual(Run(run.directory).metadata["status"], "failed")
        with run.condition("groups12") as retry:
            self.assertNotEqual(retry, failed)
        self.assertEqual((failed / "partial.json").read_text(), "partial")
        self.assertEqual(len(run.metadata["conditions"]["groups12"]["attempts"]), 2)
        with self.assertRaises(ValueError):
            with run.condition("unplanned"):
                pass

    def test_result_triggered_same_condition_execution_is_bidirectionally_linked(self):
        old = self.create()
        new = self.create(predecessor=old.directory.name, reason="Repeat after observing the result")
        self.assertNotEqual(old.directory, new.directory)
        prior = Run(old.directory)
        relation = new.metadata["predecessors"][0]
        self.assertEqual(relation["condition_changes"]["unchanged"], ["groups12", "groups21"])
        self.assertEqual(prior.metadata["followups"][0]["run_id"], new.directory.name)
        self.assertIn(new.report.name, old.report.read_text())
        self.assertIn(old.report.name, new.report.read_text())
        with self.assertRaisesRegex(ValueError, "reason"):
            self.create(predecessor=old.directory.name)

    def test_start_time_collision_does_not_overwrite_existing_run(self):
        fixed = datetime(2026, 9, 13, 12, 30, 45, tzinfo=ZoneInfo("Asia/Seoul"))
        with patch("nara.experiments.recording.datetime") as clock:
            clock.now.return_value = fixed
            one, two = self.create(), self.create()
        self.assertEqual(one.directory.name, "20260913_123045_comparison")
        self.assertEqual(two.directory.name, "20260913_123045_comparison_2")

    def test_actual_uncommitted_source_bytes_are_retained(self):
        path = self.root / "source.py"
        path.write_text("uncommitted = True\n")
        run = self.create()
        run.capture([path])
        snapshot = run.directory / "source/source.py"
        self.assertEqual(snapshot.read_bytes(), path.read_bytes())
        self.assertEqual(run.metadata["sources"]["source.py"], hashlib.sha256(path.read_bytes()).hexdigest())
        path.write_text("later = True\n")
        self.assertNotEqual(snapshot.read_bytes(), path.read_bytes())

    def test_source_recapture_cannot_rewrite_evidence(self):
        source = self.root / "code.py"
        source.write_text("original")
        run = self.create(); run.capture([source])
        source.write_text("changed")
        with self.assertRaisesRegex(ValueError, "overwritten"):
            run.capture([source])
        source.write_text("original")
        with run.condition("groups12"):
            pass
        with self.assertRaisesRegex(ValueError, "frozen"):
            run.capture([source])

    def test_routine_verification_has_no_experiment_report(self):
        run = self.create(verification=True)
        self.assertEqual(run.metadata["record_kind"], "verification")
        self.assertTrue(run.report.is_relative_to(self.root / "docs/maintenance/checks"))
        self.assertFalse((self.root / "experiments").exists())

    def test_changed_sources_are_not_mislabeled_as_unchanged_conditions(self):
        path = self.root / "prompt.txt"; path.write_text("first")
        old = self.create(); old.capture([path])
        path.write_text("revised")
        new = self.create(predecessor=old.directory.name, reason="Prompt revision after observed errors")
        new.capture([path]); new.compare_provenance()
        changes = new.metadata["predecessors"][0]["provenance_changes"]
        self.assertEqual(changes["sources"]["changed"], ["prompt.txt"])
        self.assertEqual(changes["asset_references"]["status"], "not comparable")
        self.assertEqual(Run(old.directory).metadata["followups"][0]["provenance_changes"], changes)

    def test_active_attempt_rejects_completed_paths_and_changed_conditions(self):
        run = self.create()
        with run.condition("groups12") as directory:
            run.require_active_attempt(directory, {"tokens": 512})
            with self.assertRaisesRegex(ValueError, "declared"):
                run.require_active_attempt(directory, {"tokens": 1024})
        with self.assertRaisesRegex(ValueError, "active"):
            Run(run.directory).require_active_attempt(directory, {"tokens": 512})
