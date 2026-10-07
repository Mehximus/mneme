#!/usr/bin/env python3
"""doctor must say why it asks for attention."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('mneme_entry_reasons', ROOT / 'scripts/mneme_entry.py')
entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entry)


class DoctorReasonsTest(unittest.TestCase):
    def human(self, **extra):
        doc = {'status': 'needs_attention', 'pending_events': 0, 'lifecycle': {}}
        doc.update(extra)
        return entry.human_result(doc, 'doctor')

    def test_degraded_sync_names_the_source_and_the_command(self):
        text = self.human(attention_reasons=[{'code': 'sync_degraded', 'count': 1,
                                              'examples': [{'source': 'diziler/DESIGN.md', 'reason': 'unsupported YAML'}]}])
        self.assertIn('Neden:', text)
        self.assertIn('diziler/DESIGN.md', text)
        self.assertIn('mneme.py sync', text)

    def test_every_reason_code_renders_a_line(self):
        reasons = [{'code': 'skill_conflicts', 'names': ['mneme']}, {'code': 'instruction_conflicts', 'count': 2},
                   {'code': 'hook_error'}, {'code': 'task_completion', 'count': 1}, {'code': 'validity', 'count': 3}]
        lines = [l for l in self.human(attention_reasons=reasons).splitlines() if l.startswith('Neden:')]
        self.assertEqual(len(lines), 5)

    def test_healthy_doctor_has_no_reason_lines(self):
        doc = {'status': 'observed_metadata', 'pending_events': 0, 'lifecycle': {}, 'attention_reasons': []}
        self.assertNotIn('Neden:', entry.human_result(doc, 'doctor'))


if __name__ == '__main__':
    unittest.main()
