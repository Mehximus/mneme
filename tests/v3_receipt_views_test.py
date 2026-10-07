#!/usr/bin/env python3
"""Receipt views after a state reset: adoption, unrelated conflicts, rebuild."""
import json
from pathlib import Path
import tempfile
import unittest

from v3_sync_test import load_module

VIEW = 'knowledge/v3/outcomes.md'


class ReceiptViewsTest(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory(prefix='mneme-views-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.vault = self.root / 'vault'
        (self.vault / 'notes').mkdir(parents=True)
        (self.vault / 'notes' / 'a.md').write_text('# a\ngövde\n', encoding='utf-8')
        self.engines = []
        self.first = self.engine('stateA')
        self.first.sync()
        for index in range(3):
            self.first.receipt('ev%d' % index, 'özet %d' % index, ['notes/a.md'], 'claude')

    def engine(self, name):
        engine = self.module.SyncEngine(self.vault, self.root / name)
        self.addCleanup(lambda: getattr(engine.store, 'close', lambda: None)())
        return engine

    def entries(self):
        return (self.vault / VIEW).read_text(encoding='utf-8').count('Source:')

    def test_fresh_state_adopts_a_generated_view_and_keeps_a_backup(self):
        path = self.vault / VIEW
        text = path.read_text(encoding='utf-8')
        path.write_text(text.split('- ', 2)[0] + '- 2000-01-01: eski özet\n  Source: [[receipts/old.md]]\n', encoding='utf-8', newline='')
        second = self.engine('stateB')
        result = second.sync()
        self.assertEqual(result['conflicts'], [])
        self.assertEqual(self.entries(), 3)
        self.assertEqual(len(list((self.root / 'stateB' / 'receipt-views-backup').glob('*.bak'))), 1)

    def test_view_without_generated_marker_is_still_preserved(self):
        (self.vault / VIEW).write_text('Elle yazdığım not.\n', encoding='utf-8', newline='')
        result = self.engine('stateB').sync()
        self.assertEqual([c['reason'] for c in result['conflicts']], ['manual receipt view edit preserved'])
        self.assertEqual((self.vault / VIEW).read_text(encoding='utf-8'), 'Elle yazdığım not.\n')

    def test_receipt_survives_a_view_conflict(self):
        (self.vault / VIEW).write_text('Elle yazdığım not.\n', encoding='utf-8', newline='')
        second = self.engine('stateB')
        out = second.receipt('ev-new', 'yeni özet', ['notes/a.md'], 'claude')
        self.assertEqual(out['status'], 'succeeded')

    def test_rebuild_receipts_clears_the_cutover_watermark(self):
        second = self.engine('stateB')
        second.sync()
        names = sorted(p.relative_to(self.vault).as_posix() for p in (self.vault / 'receipts').glob('*.md'))
        (self.root / 'stateB' / 'v2-migration.json').write_text(json.dumps({'historical_receipts': names}), encoding='utf-8')
        for view in list((self.vault / 'daily' / 'v3').glob('*.md')) + [self.vault / VIEW]:
            view.unlink()
        second.sync()
        self.assertFalse((self.vault / VIEW).exists())  # everything is historical: nothing to project
        out = second.rebuild_receipts()
        self.assertEqual(out['watermark_cleared'], 3)
        self.assertEqual(out['conflicts'], [])
        self.assertEqual(self.entries(), 3)
        self.assertTrue((self.root / 'stateB' / 'v2-migration.json.before-rebuild').exists())


if __name__ == '__main__':
    unittest.main()
