"""Keep observed Surface choices usable while preserving native traversal limits."""
from dataclasses import replace
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from install_skill import install
from nollm_access import (AccessDecision, AccessRuntime, FileHandleStore,
                         FileStatementStore, EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID)
from nollm_core import CoreRuntime
from project_memory import encounter, save_statement, RECALL_SURFACE_BUDGET


SOURCE = 'fixture:observed-page'


class EncounterPageHistoryTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.field = self.root / 'field'
        for index, q in enumerate((0, 6, 12)):
            save_statement(self.field, f'note-{index}', f'Complete judgment {index}.',
                           [SOURCE], (q, 0), None)

    def pages(self, **options):
        first = encounter(self.field, page_size=1, order=options.pop('order', 0),
                          steps=0, **options)
        second = encounter(self.field, ('next',), cursor=first['cursor'])
        return first, second

    def test_previous_page_choice_reopens_native_candidate_and_advances_calls(self):
        first, second = self.pages()
        chosen = first['candidates'][0]
        local = encounter(self.field, (chosen['id'],), cursor=second['cursor'])
        self.assertEqual(local['entry'], chosen['physical_cell'])
        self.assertEqual(local['items'][0]['text'], 'Complete judgment 0.')
        self.assertEqual(local['surface_calls'], second['surface_calls'] + 2)
        self.assertNotIn('surface_pages', local['cursor'])
        with self.assertRaisesRegex(ValueError, 'one physical entry'):
            encounter(self.field, (second['candidates'][0]['id'],), cursor=local['cursor'])

    def test_unobserved_candidate_is_not_accepted_from_another_traversal(self):
        first, second = self.pages()
        third = encounter(self.field, ('next',), cursor=second['cursor'])
        with self.assertRaisesRegex(ValueError, 'unavailable Surface candidate'):
            encounter(self.field, (third['candidates'][0]['id'],), cursor=second['cursor'])

    def test_removed_previous_candidate_is_rechecked_against_current_geometry(self):
        first, second = self.pages()
        with CoreRuntime(self.field) as core, AccessRuntime(
                core, FileStatementStore(self.field), FileHandleStore(self.field)) as access:
            access.apply(AccessDecision('remove', 'note-0', 'forget',
                         existing_handle=access.saved_handle('note-0'),
                         reason_text='Remove the previously observed cell for the stale-page check.'))
        with self.assertRaisesRegex(ValueError, 'unavailable Surface candidate'):
            encounter(self.field, (first['candidates'][0]['id'],), cursor=second['cursor'])

    def test_previous_page_does_not_reset_exhausted_call_budget(self):
        budget = replace(RECALL_SURFACE_BUDGET, max_calls=2)
        with patch('project_memory.RECALL_SURFACE_BUDGET', budget):
            first, second = self.pages()
            self.assertEqual(second['surface_calls'], 2)
            with self.assertRaisesRegex(RuntimeError, 'call limit'):
                encounter(self.field, (first['candidates'][0]['id'],), cursor=second['cursor'])

    def test_previous_coarse_page_descends_with_fresh_native_ids(self):
        first, second = self.pages(order=1)
        lower = encounter(self.field, (first['candidates'][0]['id'],), cursor=second['cursor'])
        self.assertEqual(lower['order'], 0)
        self.assertEqual(lower['surface_calls'], second['surface_calls'] + 2)
        local = encounter(self.field, (lower['candidates'][0]['id'],), cursor=lower['cursor'])
        self.assertEqual(local['entry'], [0, 0, 0])
        self.assertGreater(local['surface_calls'], lower['surface_calls'])

    def test_previous_physical_menu_choice_keeps_one_entry(self):
        field = self.root / 'multilayer'
        for layer in (0, 1, 2):
            save_statement(field, f'layer-{layer}', f'Layer {layer}.', [SOURCE],
                           (0, 0), None, layer=layer,
                           write_policy_id=EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID)
        page = encounter(field, layers=(0, 1, 2), surface_layers=(0, 1, 2),
                         order=0, page_size=1, steps=0)
        first = encounter(field, (page['candidates'][0]['id'],), cursor=page['cursor'])
        self.assertEqual(first['kind'], 'physical')
        second = encounter(field, ('next',), cursor=first['cursor'])
        local = encounter(field, (first['candidates'][0]['id'],), cursor=second['cursor'])
        self.assertEqual(local['entry'], first['candidates'][0]['physical_cell'])
        self.assertEqual(local['surface_calls'], second['surface_calls'] + 1)

    def test_cli_width_help_and_errors_preserve_field_and_cursor(self):
        runtime = install(self.root / 'runtime')
        cursor = self.root / 'session.json'
        command = [sys.executable, '-B', '-I', str(runtime / 'scripts/memory.py'),
                   'project', '--field', str(self.root / 'unopened-field'),
                   'encounter', '--cursor-file', str(cursor)]
        help_result = subprocess.run([*command, '--help'], text=True, capture_output=True)
        self.assertEqual(help_result.returncode, 0)
        self.assertIn('1 to 8', help_result.stdout)
        for value in ('0', '16'):
            result = subprocess.run([*command, '--page-size', value], text=True, capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('1 to 8', result.stderr)
            self.assertNotIn('Traceback', result.stderr)
        self.assertFalse(cursor.exists())
        self.assertFalse((self.root / 'unopened-field').exists())


if __name__ == '__main__':
    unittest.main()
