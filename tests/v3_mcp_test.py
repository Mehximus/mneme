#!/usr/bin/env python3
"""Stdio MCP server: protocol shape, argument mapping and subprocess protocol."""
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'template' / '.claude' / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import mneme_v3_mcp as mcp  # noqa: E402


def call(name, arguments, run):
    return mcp.handle({'jsonrpc': '2.0', 'id': 7, 'method': 'tools/call',
                       'params': {'name': name, 'arguments': arguments}}, run)


class McpTest(unittest.TestCase):
    def test_initialize_lists_tools_and_ignores_notifications(self):
        init = mcp.handle({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
                           'params': {'protocolVersion': '2024-11-05'}}, None)
        self.assertEqual(init['result']['protocolVersion'], '2024-11-05')
        self.assertIn('tools', init['result']['capabilities'])
        self.assertIsNone(mcp.handle({'jsonrpc': '2.0', 'method': 'notifications/initialized'}, None))
        listed = mcp.handle({'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'}, None)
        names = {tool['name'] for tool in listed['result']['tools']}
        self.assertEqual(names, {'mneme_search', 'mneme_note_create', 'mneme_note_edit', 'mneme_supersede', 'mneme_doctor'})
        self.assertEqual(mcp.handle({'jsonrpc': '2.0', 'id': 3, 'method': 'nope'}, None)['error']['code'], -32601)

    def test_unknown_protocol_version_falls_back_to_a_supported_one(self):
        init = mcp.handle({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '1999-01-01'}}, None)
        self.assertIn(init['result']['protocolVersion'], mcp.PROTOCOL_VERSIONS)

    def test_search_maps_to_context_command(self):
        seen = []
        out = call('mneme_search', {'query': 'doğrulama kelimesi', 'project': 'beyin', 'limit': 3},
                   lambda argv, payload: (seen.append((argv, payload)) or (0, '{"records": []}')))
        self.assertEqual(seen[0][0], ['context', 'doğrulama kelimesi', '--limit', '3', '--project', 'beyin'])
        self.assertFalse(out['result']['isError'])

    def test_write_tools_send_json_on_stdin(self):
        seen = []
        run = lambda argv, payload: (seen.append((argv, payload)) or (0, '{}'))
        call('mneme_note_create', {'source': 'notes/a.md', 'text': 'x', 'metadata': {'id': 'a'}}, run)
        call('mneme_note_edit', {'source': 'notes/a.md', 'op': 'append', 'text': 'y'}, run)
        self.assertEqual(seen[0], (['note-create', '--file', '-'], {'source': 'notes/a.md', 'text': 'x', 'metadata': {'id': 'a'}}))
        self.assertEqual(seen[1], (['note-edit', '--file', '-'], {'source': 'notes/a.md', 'op': 'append', 'text': 'y'}))

    def test_bad_arguments_and_cli_failures_are_tool_errors(self):
        out = call('mneme_search', {}, lambda *a: (0, ''))
        self.assertTrue(out['result']['isError'])
        out = call('mneme_search', {'query': 'x', 'limit': 99}, lambda *a: (0, ''))
        self.assertTrue(out['result']['isError'])
        out = call('mneme_doctor', {}, lambda *a: (1, '{"error": "ValueError"}'))
        self.assertTrue(out['result']['isError'])
        self.assertIn('ValueError', out['result']['content'][0]['text'])

        def boom(*a):
            raise OSError('gone')
        self.assertTrue(call('mneme_doctor', {}, boom)['result']['isError'])
        self.assertEqual(call('mneme_delete', {}, None)['error']['code'], -32602)

    def test_long_output_is_truncated(self):
        out = call('mneme_doctor', {}, lambda *a: (0, 'a' * (mcp.OUTPUT_LIMIT + 50)))
        self.assertTrue(out['result']['content'][0]['text'].endswith('[truncated]'))

    def test_serve_loop_over_streams_skips_garbage(self):
        lines = [json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'ping'}).encode(), b'not json', b'',
                 json.dumps({'jsonrpc': '2.0', 'method': 'notifications/initialized'}).encode()]
        stdin = io.BytesIO(b'\n'.join(lines) + b'\n')
        stdout = io.BytesIO()
        mcp.serve(SCRIPTS, stdin, stdout)
        responses = [json.loads(line) for line in stdout.getvalue().splitlines()]
        self.assertEqual(responses[0]['result'], {})
        self.assertEqual(responses[1]['error']['code'], -32700)
        self.assertEqual(len(responses), 2)

    def test_real_process_speaks_json_rpc(self):
        request = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'}) + '\n'
        done = subprocess.run([sys.executable, str(SCRIPTS / 'mneme_v3_mcp.py')], input=request.encode(),
                              capture_output=True, timeout=30)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(len(json.loads(done.stdout)['result']['tools']), 5)


if __name__ == '__main__':
    unittest.main()
