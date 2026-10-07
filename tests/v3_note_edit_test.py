#!/usr/bin/env python3
"""note-edit: append, replace_section and upsert_card edit bodies and never touch the header."""
import json
from pathlib import Path
import tempfile
import unittest

from v3_sync_test import load_module

LF = chr(10)
CR = chr(13)


class NoteEditTest(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory(prefix='mneme-note-edit-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.vault = self.root / 'vault'
        (self.vault / 'notes').mkdir(parents=True)
        self.engine = self.module.SyncEngine(self.vault, self.root / 'runtime')
        self.addCleanup(lambda: getattr(self.engine.store, 'close', lambda: None)())

    def write(self, name, text, newline=LF):
        (self.vault / 'notes' / name).write_bytes(text.replace(LF, newline).encode('utf-8'))

    def read(self, name):
        return (self.vault / 'notes' / name).read_bytes().decode('utf-8')

    def test_append_keeps_json_header_bytes(self):
        header = '---' + LF + json.dumps({'kind': 'note', 'id': 'a-1'}, indent=2) + LF + '---' + LF
        self.write('a.md', header + 'İlk satır.' + LF)
        self.engine.sync()
        out = self.engine.note_edit('notes/a.md', 'append', 'Çalışıyor: ğüşiöç.')
        self.assertEqual(out['status'], 'succeeded')
        text = self.read('a.md')
        self.assertTrue(text.startswith(header))
        self.assertTrue(text.endswith('İlk satır.' + LF + LF + 'Çalışıyor: ğüşiöç.' + LF))

    def test_yaml_header_is_preserved_verbatim(self):
        header = '---' + LF + 'title: Not' + LF + 'tags: [a, b]' + LF + '---' + LF
        self.write('y.md', header + 'Gövde' + LF)
        self.engine.sync()
        self.engine.note_edit('notes/y.md', 'append', 'Ek')
        self.assertTrue(self.read('y.md').startswith(header))

    def test_replace_section_only_changes_that_section(self):
        self.write('s.md', '# Not' + LF + LF + '## Bir' + LF + 'eski' + LF + LF + '### Alt' + LF + 'alt' + LF + LF + '## İki' + LF + 'dokunma' + LF)
        self.engine.sync()
        self.engine.note_edit('notes/s.md', 'replace_section', 'yeni', heading='## Bir')
        text = self.read('s.md')
        self.assertIn('## Bir' + LF + LF + 'yeni' + LF + LF + '## İki' + LF + 'dokunma', text)
        self.assertNotIn('eski', text)
        self.assertNotIn('### Alt', text)

    def test_replace_section_missing_heading_fails_or_creates(self):
        self.write('m.md', '# Not' + LF + 'x' + LF)
        self.engine.sync()
        with self.assertRaises(ValueError):
            self.engine.note_edit('notes/m.md', 'replace_section', 'y', heading='## Yok')
        self.engine.note_edit('notes/m.md', 'replace_section', 'y', heading='## Yok', create=True)
        self.assertIn('## Yok' + LF + LF + 'y', self.read('m.md'))

    def test_headings_inside_code_fence_are_ignored(self):
        fence = chr(96) * 3
        self.write('f.md', '## Bir' + LF + fence + LF + '## Sahte' + LF + fence + LF + '## İki' + LF + 'x' + LF)
        self.engine.sync()
        self.engine.note_edit('notes/f.md', 'replace_section', 'yeni', heading='Bir')
        text = self.read('f.md')
        self.assertNotIn('Sahte', text)
        self.assertIn('## İki' + LF + 'x', text)

    def test_upsert_card_inserts_on_top_then_replaces_by_key(self):
        self.write('l.md', '# Son oturum' + LF + LF + '## 2026-10-06 10:00 · eski · aaaa1111' + LF + '- eski kart' + LF)
        self.engine.sync()
        card = '## 2026-10-07 20:00 · yeni · bbbb2222' + LF + '- ilk hali'
        self.engine.note_edit('notes/l.md', 'upsert_card', card)
        text = self.read('l.md')
        self.assertLess(text.index('bbbb2222'), text.index('aaaa1111'))
        self.engine.note_edit('notes/l.md', 'upsert_card', card.replace('ilk hali', 'son hali'))
        text = self.read('l.md')
        self.assertEqual(text.count('bbbb2222'), 1)
        self.assertIn('son hali', text)
        self.assertNotIn('ilk hali', text)
        self.assertIn('- eski kart', text)

    def test_crlf_file_stays_crlf(self):
        self.write('c.md', 'Bir' + LF + 'İki' + LF, newline=CR + LF)
        self.engine.sync()
        self.engine.note_edit('notes/c.md', 'append', 'Üç')
        raw = (self.vault / 'notes' / 'c.md').read_bytes()
        self.assertNotIn(b'\n', raw.replace(b'\r\n', b''))

    def test_refusals(self):
        self.write('t.md', '---' + LF + json.dumps({'kind': 'task', 'id': 't-1'}) + LF + '---' + LF + 'görev' + LF)
        self.engine.sync()
        for source in ('notes/t.md', 'receipts/x.md', 'tasks/y.md', 'daily/v3/z.md', 'notes/yok.md', 'notes/a.txt'):
            with self.assertRaises(ValueError):
                self.engine.note_edit(source, 'append', 'x')
        self.write('ok.md', 'gövde' + LF)
        with self.assertRaises(ValueError):
            self.engine.note_edit('notes/ok.md', 'append', '---' + LF + 'sahte başlık')
        with self.assertRaises(ValueError):
            self.engine.note_edit('notes/ok.md', 'bilinmeyen', 'x')


if __name__ == '__main__':
    unittest.main()
