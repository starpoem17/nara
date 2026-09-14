"""One sweep report retains condition sections and original evidence links."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from nara.experiments.recording import Run
from nara.evaluation.reporting import report_path, write_report


class ReportingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.patch = patch("nara.evaluation.reporting.ROOT", self.root)
        self.patch.start(); self.addCleanup(self.patch.stop)
        self.run = Run.create("grouping", "comparison", "Compare planned conditions", {"a": {}, "b": {}}, root=self.root)

    def test_condition_sections_share_one_report_and_preserve_judgment_history(self):
        with self.run.condition("a") as a:
            (a / "scores.csv").write_text("score\n1\n")
            frozen = a / "source/old.md"
            frozen.parent.mkdir(); frozen.write_text("frozen")
            first = write_report(a / "evaluation.md", "# A\n[score](scores.csv) [frozen](source/old.md)\n")
        with self.run.condition("b") as b:
            second = write_report(b / "evaluation.md", "# B\n")
        self.assertEqual(first, second)
        before = first.read_text()
        self.assertIn("# A", before); self.assertIn("# B", before)
        self.assertIn("Judgment history", before)
        write_report(a / "evaluation.md", "# Revised A\n")
        after = first.read_text()
        self.assertNotIn("# A\n", after); self.assertIn("# B", after)
        self.assertIn("Judgment history", after)
        self.assertEqual(frozen.read_text(), "frozen")
        self.assertFalse((a / "evaluation.md").exists())

    def test_distinct_runs_do_not_collide_and_existing_report_resolves(self):
        other = Run.create("grouping", "comparison", "Repeat", {"a": {}}, root=self.root)
        self.assertNotEqual(report_path(self.run.directory / "evaluation.md"), report_path(other.directory / "evaluation.md"))
        self.assertEqual(report_path(self.run.report), self.run.report)

    def test_unregistered_artifact_is_rejected_without_creating_a_report(self):
        with self.assertRaisesRegex(ValueError, "create a run"):
            write_report(self.root / "unregistered/evaluation.md", "orphan")
        self.assertFalse((self.root / "docs/reports").exists())

    def test_canonical_report_cannot_be_replaced(self):
        original = self.run.report.read_bytes()
        with self.assertRaisesRegex(ValueError, "cannot be overwritten"):
            write_report(self.run.report, "erase history")
        self.assertEqual(self.run.report.read_bytes(), original)

    def test_verification_writes_one_owning_report(self):
        run = Run.create("checks", "replay", "Saved replay", {"saved": {}}, root=self.root, verification=True)
        with run.condition("saved") as directory:
            destination = write_report(directory / "evaluation.md", "Replay observation")
        self.assertEqual(destination, run.report)
        self.assertFalse((directory / "evaluation.md").exists())
        self.assertIn("Replay observation", run.report.read_text())
