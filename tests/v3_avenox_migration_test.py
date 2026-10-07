#!/usr/bin/env python3
"""--from-avenox retires an Avenox beyin install without touching notes or user edits."""
import base64
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from v3_package_helpers import INSTALLER, ROOT, isolated_env, run_python, snapshot


def digest(data):
    return hashlib.sha256(data).hexdigest()


def b64(data):
    return base64.b64encode(data).decode('ascii')


def encoded_hook(script):
    command = "& 'python.exe' '" + script + "' --vault 'x'"
    return 'powershell.exe -NoProfile -EncodedCommand ' + b64(command.encode('utf-16-le'))


class AvenoxMigrationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='mneme-avenox-test-')
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.env = isolated_env(self.base / 'home')
        self.vault = self.base / 'Örnek Beyin'
        self.old_state = self.base / 'old-state'
        self.new_state = self.base / 'new-state'
        for folder in (self.vault / 'notes', self.vault / '.claude/scripts', self.old_state):
            folder.mkdir(parents=True)
        self.files = {}
        stock = {'beyin.py': b'print("beyin")\n', '.beyin-version': b'3.7.1\n',
                 '.beyin-runtime.json': json.dumps({'state': str(self.old_state), 'schema': 1}).encode(),
                 '.claude/scripts/beyin_v3_hook.py': b'# stock hook\n'}
        for name, data in stock.items():
            (self.vault / name).write_bytes(data)
            self.files[name] = {'installed_hash': digest(data), 'installed_content': b64(data), 'original': None}
        installed_settings = b'{"hooks": {}}\n'
        self.files['.claude/settings.local.json'] = {'installed_hash': digest(installed_settings),
                                                     'installed_content': b64(installed_settings), 'original': None}
        settings = {'permissions': {'allow': ['PowerShell(py -3 beyin.py:*)']},
                    'hooks': {'SessionStart': [{'hooks': [{'type': 'command', 'command': encoded_hook('beyin_v3_hook.py')}]}],
                              'Stop': [{'hooks': [{'type': 'command', 'command': 'echo benim kancam'}]}]}}
        (self.vault / '.claude/settings.local.json').write_text(json.dumps(settings), encoding='utf-8')
        original_claude = '# Benim talimatlarım\n'.encode()
        self.files['CLAUDE.md'] = {'installed_hash': digest(b'x'), 'installed_content': b64(b'x'), 'original': b64(original_claude)}
        (self.vault / 'CLAUDE.md').write_text('# Benim talimatlarım\n\nSon eklediğim kural.\n\n<!-- beyin-v3:start -->\nyönetilen\n<!-- beyin-v3:end -->\n\nSondaki not.\n', encoding='utf-8')
        (self.old_state / 'v3-install.json').write_text(json.dumps({'files': self.files, 'version': '3.7.1'}), encoding='utf-8')
        (self.vault / 'notes/not.md').write_text('# Kullanıcı notu\n', encoding='utf-8')

    def run_installer(self, *args):
        return run_python(INSTALLER, ['--vault', self.vault, '--state', self.new_state, *args], ROOT, self.env)

    def test_install_without_the_flag_explains_what_to_do(self):
        result = self.run_installer()
        self.assertEqual(result.returncode, 1)
        self.assertIn('--from-avenox', result.stderr.decode('utf-8'))
        self.assertTrue((self.vault / 'beyin.py').exists())

    def test_plan_changes_nothing(self):
        before = snapshot(self.vault)
        result = self.run_installer('--from-avenox', '--plan')
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(result.stdout)
        self.assertEqual(plan['status'], 'plan')
        self.assertIn('.claude/settings.local.json', plan['strip_hooks'])
        self.assertIn('CLAUDE.md', plan['strip_block'])
        self.assertEqual(snapshot(self.vault), before)

    def test_migration_keeps_notes_and_user_edits_then_installs_mneme(self):
        note = (self.vault / 'notes/not.md').read_bytes()
        result = self.run_installer('--from-avenox')
        self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8'))
        for name in ('beyin.py', '.beyin-version', '.beyin-runtime.json', '.claude/scripts/beyin_v3_hook.py'):
            self.assertFalse((self.vault / name).exists(), name)
        self.assertTrue((self.vault / '.mneme-version').exists())
        self.assertEqual((self.vault / 'notes/not.md').read_bytes(), note)
        settings = json.loads((self.vault / '.claude/settings.local.json').read_text(encoding='utf-8'))
        self.assertEqual(settings['permissions']['allow'], ['PowerShell(py -3 beyin.py:*)'])
        commands = json.dumps(settings['hooks'])
        self.assertIn('echo benim kancam', commands)
        self.assertNotIn('beyin_v3', commands)
        claude = (self.vault / 'CLAUDE.md').read_text(encoding='utf-8')
        self.assertIn('Son eklediğim kural.', claude)
        self.assertIn('Sondaki not.', claude)
        self.assertNotIn('beyin-v3', claude)
        self.assertTrue((self.new_state / 'avenox-migration-backup/files/CLAUDE.md').exists())
        self.assertTrue((self.new_state / 'avenox-migration-backup/v3-install.json').exists())

    def test_hand_edited_stock_file_blocks_before_any_change(self):
        (self.vault / '.claude/scripts/beyin_v3_hook.py').write_text('# benim değişikliğim\n', encoding='utf-8')
        before = snapshot(self.vault)
        result = self.run_installer('--from-avenox')
        self.assertEqual(result.returncode, 1)
        self.assertIn('beyin_v3_hook.py', result.stderr.decode('utf-8'))
        self.assertEqual(snapshot(self.vault), before)


if __name__ == '__main__':
    unittest.main()
