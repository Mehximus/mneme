#!/usr/bin/env python3
"""supersede command and the advisory fact-conflict notice."""
import json
from pathlib import Path
import tempfile
import unittest

from v3_sync_test import load_module


def note(vault, name, body, **metadata):
    header = json.dumps(dict({'kind': 'note', 'visibility': 'internal'}, **metadata), ensure_ascii=False, indent=2)
    (vault / 'notes' / name).write_text('---\n' + header + '\n---\n' + body + '\n', encoding='utf-8', newline='')


class SupersedeTest(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory(prefix='mneme-supersede-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.vault = self.root / 'vault'
        (self.vault / 'notes').mkdir(parents=True)
        self.engine = self.module.SyncEngine(self.vault, self.root / 'runtime')
        self.addCleanup(lambda: getattr(self.engine.store, 'close', lambda: None)())
        note(self.vault, 'old.md', 'Doğrulama kelimesi turuncu.', id='word-old', project='beyin', facts={'dogrulama': 'turuncu'})
        note(self.vault, 'new.md', 'Doğrulama kelimesi mavi.', id='word-new', project='beyin', facts={'dogrulama': 'mavi'})

    def test_conflicting_fact_values_raise_a_notice_not_a_warning(self):
        result = self.engine.sync()
        self.assertEqual(result['warnings'], [])
        self.assertTrue(any('fact conflict: beyin/dogrulama' in n['reason'] for n in result['notices']), result['notices'])

    def test_supersede_links_hides_old_and_clears_the_notice(self):
        self.engine.sync()
        out = self.engine.supersede('notes/new.md', 'word-old')
        self.assertEqual(out['status'], 'succeeded')
        self.assertIn('word-old', (self.vault / 'notes/new.md').read_text(encoding='utf-8'))
        self.assertTrue((self.vault / 'notes/old.md').exists())
        result = self.engine.sync()
        self.assertEqual([n for n in result['notices'] if 'fact conflict' in n['reason']], [])
        self.assertEqual(self.engine.supersede('word-new', 'word-old')['status'], 'unchanged')

    def test_refusals(self):
        self.engine.sync()
        with self.assertRaises(ValueError):
            self.engine.supersede('word-new', 'word-new')
        self.engine.supersede('word-new', 'word-old')
        with self.assertRaises(ValueError):
            self.engine.supersede('word-old', 'word-new')  # cycle
        (self.vault / 'notes/yaml.md').write_text('---\ntitle: Düz\n---\nYAML başlıklı not.\n', encoding='utf-8', newline='')
        self.engine.sync()
        with self.assertRaises(ValueError):
            self.engine.supersede('notes/yaml.md', 'word-old')
        with self.assertRaises(KeyError):
            self.engine.supersede('nope', 'word-old')


if __name__ == '__main__':
    unittest.main()
