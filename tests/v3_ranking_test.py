#!/usr/bin/env python3
"""Explicit search ranks by idf, length normalization and title hits, not by raw word count."""
import json
from pathlib import Path
import tempfile
import unittest

from v3_sync_test import load_module


def note(vault, name, body, **metadata):
    header = json.dumps(dict({'kind': 'note', 'visibility': 'internal'}, **metadata), ensure_ascii=False, indent=2)
    (vault / 'notes' / name).write_text('---\n' + header + '\n---\n' + body + '\n', encoding='utf-8', newline='')


class RankingTest(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory(prefix='mneme-ranking-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.vault = self.root / 'vault'
        (self.vault / 'notes').mkdir(parents=True)
        self.engine = self.module.SyncEngine(self.vault, self.root / 'runtime')
        self.addCleanup(lambda: getattr(self.engine.store, 'close', lambda: None)())

    def sources(self, query, limit=5):
        self.engine.sync()
        result = self.engine.store.retrieve(query, limit=limit)
        return [record['source'] for record in result['records']]

    def test_short_note_about_the_query_beats_long_note_that_mentions_it(self):
        filler = ' '.join('alan%d' % i for i in range(300))
        note(self.vault, 'long.md', 'Plan belgesi. Dogrulama kelimesi bir kez geciyor. ' + filler, id='long-plan', title='Uzun plan')
        note(self.vault, 'short.md', 'Dogrulama kelimesi mavi ahtapot.', id='short-word', title='Dogrulama kelimesi')
        self.assertEqual(self.sources('dogrulama kelimesi')[0], 'notes/short.md')

    def test_rare_term_outweighs_common_term(self):
        for i in range(5):
            note(self.vault, 'common%d.md' % i, 'proje durum notu sayi%d' % i, id='common-%d' % i, title='Ortak %d' % i)
        note(self.vault, 'rare.md', 'zirkonyum tedarik notu', id='rare-1', title='Tedarik')
        note(self.vault, 'both.md', 'proje durum', id='both-1', title='Genel')
        self.assertEqual(self.sources('proje durum zirkonyum')[0], 'notes/rare.md')


if __name__ == '__main__':
    unittest.main()
