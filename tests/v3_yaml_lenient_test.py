#!/usr/bin/env python3
"""A header beyond the YAML subset must not drop the note body from the index."""
from pathlib import Path
import tempfile
import unittest

from v3_sync_test import load_module


class LenientYamlTest(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory(prefix='mneme-yaml-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.vault = self.root / 'vault'
        (self.vault / 'notes').mkdir(parents=True)
        self.engine = self.module.SyncEngine(self.vault, self.root / 'runtime')
        self.addCleanup(lambda: getattr(self.engine.store, 'close', lambda: None)())

    def write(self, name, text):
        (self.vault / 'notes' / name).write_text(text, encoding='utf-8', newline='')

    def test_deeply_nested_design_header_still_indexes_body(self):
        self.write('design.md', '---\ntypography:\n  display:\n    family: Geist\n---\nMarka tasarım ölçeği burada.\n')
        result = self.engine.sync()
        self.assertEqual(result['warnings'], [])
        self.assertEqual(result['status'], 'succeeded')
        self.assertEqual(result['indexed'], 1)
        self.assertEqual([n['source'] for n in result['notices']], ['notes/design.md'])

    def test_header_mentioning_a_gate_word_stays_excluded(self):
        for index, word in enumerate(('visibility: private', 'sensitivity: sensitive', 'trusted: false')):
            self.write(f'gated{index}.md', f'---\ngroup:\n  deep:\n    {word}\n---\nGizli gövde.\n')
        result = self.engine.sync()
        self.assertEqual(result['indexed'], 0)
        self.assertEqual(len(result['warnings']), 3)

    def test_plain_yaml_and_json_headers_are_unchanged(self):
        self.write('yaml.md', '---\ntitle: Basit\ntags:\n  - a\n---\nDüz YAML gövde.\n')
        self.write('json.md', '---\n{"kind": "note", "visibility": "internal"}\n---\nJSON gövde.\n')
        result = self.engine.sync()
        self.assertEqual(result['warnings'], [])
        self.assertEqual(result['notices'], [])
        self.assertEqual(result['indexed'], 2)


if __name__ == '__main__':
    unittest.main()
