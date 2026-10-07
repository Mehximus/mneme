"""Native clickable wrappers around the single installed updater."""
import os
from pathlib import Path
import shlex
import sys


def _cmd_quote(value):
    value = str(value)
    if any(char in value for char in '\r\n\x00"'):
        raise ValueError('Unsupported launcher path')
    return '"' + value.replace('%', '%%') + '"'


def _desktop_quote(value):
    return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace('%', '%%') + '"'


def plan_launchers(vault, state):
    """Return only native launcher bytes; the installer owns permissions/journaling."""
    vault = Path(vault).resolve()
    entry = vault / 'mneme.py'
    if any(char in str(vault) + sys.executable for char in '\r\n\x00'):
        raise ValueError('Unsupported launcher path')
    if os.name == 'nt':
        # ASCII filename/content avoids cmd.exe's legacy codepage for Unicode paths;
        # use PowerShell's UTF-16 encoded script to carry exact path characters.
        import base64
        script = '& ' + ' '.join("'" + str(v).replace("'", "''") + "'" for v in [sys.executable, entry, 'update'])
        script += '; exit $LASTEXITCODE'
        encoded = base64.b64encode(script.encode('utf-16le')).decode('ascii')
        system = os.environ.get('SYSTEMROOT') or os.environ.get('WINDIR') or r'C:\Windows'
        launcher = Path(system) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
        body = ('@echo off\r\nsetlocal DisableDelayedExpansion\r\n' + _cmd_quote(launcher) +
                ' -NoProfile -NonInteractive -EncodedCommand ' + encoded + '\r\n' +
                'set "MNEME_UPDATE_EXIT=%errorlevel%"\r\npause\r\nexit /b %MNEME_UPDATE_EXIT%\r\n')
        return {'Mneme Guncelle.cmd': body.encode('ascii')}
    name = 'Mneme Güncelle.command' if sys.platform == 'darwin' else 'Mneme Güncelle.sh'
    shell = ('#!/bin/sh\n' + shlex.join([sys.executable, str(entry), 'update']) +
             '\nmneme_update_exit=$?\nprintf "\\nKapatmak icin Enter tusuna basin. "\n' +
             'read -r mneme_update_reply || true\nexit "$mneme_update_exit"\n')
    files = {name: shell.encode('utf-8')}
    if sys.platform.startswith('linux'):
        desktop = ('[Desktop Entry]\nType=Application\nName=Mneme Güncelle\n' +
                   'Comment=Kurulu beyni resmi yeni surume guncelle\nTerminal=true\n' +
                   'Exec=/bin/sh ' + _desktop_quote(vault / name) + '\nIcon=system-software-update\n')
        files['Mneme Güncelle.desktop'] = desktop.encode('utf-8')
    return files
