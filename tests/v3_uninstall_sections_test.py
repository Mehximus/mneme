"""Uninstall removes only Mneme's section of a shared file the user has also edited."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from v3_package_helpers import inherited_env

ROOT = Path(os.environ.get('MNEME_TEST_REPO', Path(__file__).resolve().parents[1]))
START, END = '<!-- mneme-v3:start -->', '<!-- mneme-v3:end -->'
RULES = '# Kurallarım\nUSER_RULE_SENTINEL\n'
LF = chr(10)


class UninstallSectionsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='mneme-uninstall-sections-')
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.vault = self.base / 'vault'
        self.vault.mkdir()
        self.state = self.base / 'state'
        self.env = inherited_env(MNEME_V3_NO_SPAWN='1', PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8')
        (self.vault / 'AGENTS.md').write_text(RULES, encoding='utf-8', newline='')

    def cli(self, *extra):
        return subprocess.run([sys.executable, str(ROOT / 'scripts/install_v3.py'), '--vault', str(self.vault),
                               '--state', str(self.state), *extra], capture_output=True, text=True, encoding='utf-8',
                              env=self.env, cwd=self.vault, timeout=120)

    def installed(self):
        done = self.cli()
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_router_with_user_text_added_inside_the_file_loses_only_the_block(self):
        self.installed()
        agents = self.vault / 'AGENTS.md'
        agents.write_text(agents.read_text(encoding='utf-8') + LF + 'Sonradan eklediğim kural.' + LF, encoding='utf-8', newline='')
        done = self.cli('--uninstall')
        self.assertEqual(done.returncode, 0, done.stderr)
        text = agents.read_text(encoding='utf-8')
        self.assertNotIn(START, text)
        self.assertIn('USER_RULE_SENTINEL', text)
        self.assertIn('Sonradan eklediğim kural.', text)
        self.assertEqual(json.loads(done.stdout)['sections_stripped'], ['AGENTS.md'])
        self.assertTrue((self.state / 'uninstall-backup' / 'AGENTS.md').exists())

    def test_settings_with_a_user_hook_keeps_it(self):
        self.installed()
        settings = self.vault / '.claude' / 'settings.local.json'
        data = json.loads(settings.read_text(encoding='utf-8'))
        data['permissions'] = {'allow': ['Bash(ls:*)']}
        data['hooks'].setdefault('Stop', []).append({'hooks': [{'type': 'command', 'command': 'echo benim-kancam'}]})
        settings.write_text(json.dumps(data, indent=2), encoding='utf-8', newline='')
        done = self.cli('--uninstall')
        self.assertEqual(done.returncode, 0, done.stderr)
        after = json.loads(settings.read_text(encoding='utf-8'))
        self.assertEqual(after['permissions'], {'allow': ['Bash(ls:*)']})
        commands = [h['command'] for groups in after['hooks'].values() for g in groups for h in g['hooks']]
        self.assertEqual(commands, ['echo benim-kancam'])

    def test_plan_changes_nothing_and_reports_actions(self):
        self.installed()
        agents = self.vault / 'AGENTS.md'
        agents.write_text(agents.read_text(encoding='utf-8') + 'ek' + LF, encoding='utf-8', newline='')
        before = agents.read_bytes()
        done = self.cli('--plan-uninstall')
        self.assertEqual(done.returncode, 0, done.stderr)
        plan = json.loads(done.stdout)
        self.assertEqual(plan['status'], 'plan')
        self.assertIn({'file': 'AGENTS.md', 'action': 'strip-block'}, plan['actions'])
        self.assertEqual(agents.read_bytes(), before)
        self.assertTrue((self.state / 'v3-install.json').exists())

    def test_real_conflict_lists_every_file_and_changes_nothing(self):
        self.installed()
        hook = self.vault / '.claude' / 'scripts' / 'mneme_v3_hook.py'
        hook.write_text(hook.read_text(encoding='utf-8') + '# elle değişti' + LF, encoding='utf-8', newline='')
        before = hook.read_bytes()
        done = self.cli('--uninstall')
        self.assertEqual(done.returncode, 1)
        self.assertIn('Uninstall conflict: managed file changed; preserve and reconcile', done.stderr)
        self.assertIn('mneme_v3_hook.py', done.stderr)
        self.assertEqual(hook.read_bytes(), before)
        self.assertTrue((self.state / 'v3-install.json').exists())
        self.assertEqual(self.cli('--plan-uninstall').returncode, 1)


if __name__ == '__main__':
    unittest.main()
