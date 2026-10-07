#!/usr/bin/env python3
"""Search quality floor: the standard ranking must not regress on the frozen benchmarks."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests' / 'fixtures' / 'v3'


def evaluate(fixture):
    done = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'evaluate_v3_search.py'), '--fixture', str(fixture), '--json'],
                          capture_output=True, timeout=300, env=dict(__import__('os').environ, PYTHONIOENCODING='utf-8'))
    if done.returncode:
        raise AssertionError(done.stderr.decode('utf-8', 'replace'))
    return json.loads(done.stdout.decode('utf-8'))['modes']['non_strict']


class SearchQualityTest(unittest.TestCase):
    def test_engineering_benchmark_floor(self):
        modes = evaluate(FIXTURES / 'search_benchmark.json')
        self.assertGreaterEqual(modes['recall_at_1'], 0.90)
        self.assertGreaterEqual(modes['mrr'], 0.95)
        self.assertEqual(modes['recall_at_5'], 1.0)

    def test_turkish_vault_benchmark_floor(self):
        modes = evaluate(FIXTURES / 'search_benchmark_tr.json')
        self.assertEqual(modes['recall_at_1'], 1.0)
        self.assertEqual(modes['mrr'], 1.0)


if __name__ == '__main__':
    unittest.main()
