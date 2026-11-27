import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nollm import local_gate


class LocalGateManifestReuseTests(unittest.TestCase):
    def report(self, manifest=None, error=None):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(local_gate, 'cleanup_runtime_cache_artifacts', return_value=[]), \
                 patch.object(local_gate, '_run_component', return_value=local_gate.GateComponent(ok=True)), \
                 patch.object(local_gate, '_dream_triage_component', return_value=local_gate.GateComponent(ok=True)), \
                 patch.object(local_gate, 'build_all_dream_checks_manifest', return_value=manifest, side_effect=error) as build:
                report = local_gate.build_local_gate_report(Path(directory))
                build.assert_called_once_with(Path(directory).resolve())
                return report

    def test_healthy_report_keeps_defaults_and_skipped_pytest(self):
        report = self.report({'ok': True})
        self.assertTrue(report['ok'])
        self.assertEqual(report['forbidden_semantics'], dict.fromkeys(local_gate.FORBIDDEN_FLAG_KEYS, False))
        self.assertEqual(report['components']['dream_checks_manifest'], {
            'ok': True, 'included': True, 'returncode': 0,
            'detail': 'dream checks manifest', 'timeout_seconds': 0,
        })
        self.assertFalse(report['components']['pytest']['included'])

    def test_flags_and_component_use_the_same_manifest(self):
        report = self.report({'ok': True, 'forbidden_semantics': {'parent_child': True}})
        self.assertFalse(report['ok'])
        self.assertTrue(report['forbidden_semantics']['parent_child'])
        self.assertTrue(report['components']['dream_checks_manifest']['ok'])

    def test_failed_manifest_still_fails_the_report(self):
        report = self.report({'ok': False})
        self.assertFalse(report['ok'])
        self.assertEqual(report['components']['dream_checks_manifest']['returncode'], 1)

    def test_builder_error_is_not_retried_or_hidden(self):
        report = self.report(error=ValueError('unreadable report'))
        self.assertFalse(report['ok'])
        self.assertEqual(report['components']['dream_checks_manifest']['detail'],
                         'dream checks manifest failed: unreadable report')


if __name__ == '__main__':
    unittest.main()
