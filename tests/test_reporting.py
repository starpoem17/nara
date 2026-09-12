"""Reports stay in docs while links still locate original artifacts."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nara.evaluation.reporting import report_path, write_report


class ReportingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'project'
        self.root.mkdir()
        self.root_patch = patch('nara.evaluation.reporting.ROOT', self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def test_report_links_follow_documents_and_preserve_artifacts(self):
        run = self.root / 'analysis/run'
        run.mkdir(parents=True)
        artifact = run / 'scores (검증).csv'
        artifact.write_text('score\n1\n')
        source = run / 'source/docs/old.md'
        source.parent.mkdir(parents=True)
        source.write_text('frozen')
        original = run / 'comparison.md'
        result = write_report(original,
            '# Comparison\n[score](<scores (검증).csv>)\n'
            '[evaluation](evaluation.md#metrics)\n'
            '[frozen](source/docs/old.md)\n'
            '[web](https://example.com/a) [section](#local)\n')
        self.assertEqual(result, self.root / 'docs/reports/analysis/run/comparison.md')
        self.assertFalse(original.exists())
        text = result.read_text()
        self.assertIn('](<../../../../analysis/run/scores (검증).csv>)', text)
        self.assertIn('](<evaluation.md#metrics>)', text)
        self.assertIn('](<../../../../analysis/run/source/docs/old.md>)', text)
        self.assertIn('[web](https://example.com/a) [section](#local)', text)
        self.assertEqual(source.read_text(), 'frozen')
        self.assertEqual(artifact.read_text(), 'score\n1\n')

    def test_output_and_analysis_reports_do_not_collide(self):
        analysis = self.root / 'analysis/same/evaluation.md'
        output = self.root / 'output/same/evaluation.md'
        self.assertNotEqual(report_path(analysis), report_path(output))
        self.assertEqual(report_path(report_path(output)), report_path(output))

    def test_external_run_paths_are_distinct_and_stay_under_docs(self):
        one = Path(self.temp.name) / 'one/run/evaluation.md'
        two = Path(self.temp.name) / 'two/run/evaluation.md'
        self.assertNotEqual(report_path(one), report_path(two))
        result = write_report(one, '# External evaluation\n[comparison](comparison.md)\n')
        self.assertTrue(result.is_relative_to(self.root / 'docs/reports/external'))
        self.assertFalse(one.exists())
        self.assertIn('[comparison](<comparison.md>)', result.read_text())


if __name__ == '__main__':
    unittest.main()
