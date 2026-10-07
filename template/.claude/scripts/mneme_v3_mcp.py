#!/usr/bin/env python3
"""Minimal stdio MCP server for a Mneme vault (standard library only).

Newline-delimited JSON-RPC 2.0. Every tool runs the vault's own `mneme.py --json <command>`,
so redaction, revision checks, refusals and projection readback are exactly the CLI's.
No tool deletes anything; note-create refuses to overwrite; note-edit refuses tasks,
receipts and generated views.
"""
import json
from pathlib import Path
import subprocess
import sys

PROTOCOL_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")
SERVER_INFO = {"name": "mneme", "version": "1"}
OUTPUT_LIMIT = 60000

_STRING = {"type": "string"}
TOOLS = [
    {"name": "mneme_search",
     "description": "Search the vault's source-backed memory. Returns matching notes with their source paths.",
     "inputSchema": {"type": "object", "required": ["query"], "properties": {
         "query": _STRING, "project": _STRING, "limit": {"type": "integer", "minimum": 1, "maximum": 20}}}},
    {"name": "mneme_note_create",
     "description": "Create a new Markdown note under notes/ or knowledge/. Never overwrites an existing file.",
     "inputSchema": {"type": "object", "required": ["source", "text"], "properties": {
         "source": {"type": "string", "description": "notes/<name>.md or knowledge/<name>.md"},
         "text": {"type": "string", "description": "Body only, no frontmatter"},
         "metadata": {"type": "object", "description": "Optional frontmatter fields: id, kind, project, visibility, facts, supersedes"}}}},
    {"name": "mneme_note_edit",
     "description": "Edit the body of an existing note. append adds to the end; replace_section replaces the section under heading; upsert_card replaces or inserts a card whose first line is a heading.",
     "inputSchema": {"type": "object", "required": ["source", "op", "text"], "properties": {
         "source": _STRING, "op": {"enum": ["append", "replace_section", "upsert_card"]}, "text": _STRING,
         "heading": _STRING, "key": _STRING, "create": {"type": "boolean"}}}},
    {"name": "mneme_supersede",
     "description": "Mark an older note as replaced by a newer one. Nothing is deleted.",
     "inputSchema": {"type": "object", "required": ["new", "old"], "properties": {"new": _STRING, "old": _STRING}}},
    {"name": "mneme_doctor",
     "description": "Report vault memory health.",
     "inputSchema": {"type": "object", "properties": {}}},
]


def _require(arguments, *names):
    for name in names:
        if not isinstance(arguments.get(name), str) or not arguments[name].strip():
            raise ValueError(name + " is required")


def command_for(name, arguments):
    """(argv after mneme.py --json, stdin JSON or None) for a tool call."""
    if not isinstance(arguments, dict):
        raise ValueError("arguments must be an object")
    if name == "mneme_search":
        _require(arguments, "query")
        argv = ["context", arguments["query"]]
        limit = arguments.get("limit", 5)
        if type(limit) is not int or not 1 <= limit <= 20:
            raise ValueError("limit must be 1-20")
        argv += ["--limit", str(limit)]
        if isinstance(arguments.get("project"), str) and arguments["project"].strip():
            argv += ["--project", arguments["project"]]
        return argv, None
    if name == "mneme_note_create":
        _require(arguments, "source", "text")
        payload = {"source": arguments["source"], "text": arguments["text"]}
        if arguments.get("metadata") is not None:
            payload["metadata"] = arguments["metadata"]
        return ["note-create", "--file", "-"], payload
    if name == "mneme_note_edit":
        _require(arguments, "source", "op", "text")
        payload = {key: arguments[key] for key in ("source", "op", "text", "heading", "key", "create") if key in arguments}
        return ["note-edit", "--file", "-"], payload
    if name == "mneme_supersede":
        _require(arguments, "new", "old")
        return ["supersede", "--new", arguments["new"], "--old", arguments["old"]], None
    if name == "mneme_doctor":
        return ["doctor"], None
    raise KeyError(name)


def make_runner(vault):
    entry = Path(vault) / "mneme.py"

    def run(argv, payload):
        completed = subprocess.run(
            [sys.executable, str(entry), "--json"] + argv,
            input=json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else b"",
            capture_output=True, cwd=str(vault), timeout=120,
            env=dict(__import__("os").environ, PYTHONIOENCODING="utf-8"))
        text = (completed.stdout if completed.returncode == 0 else completed.stderr or completed.stdout).decode("utf-8", "replace")
        return completed.returncode, text
    return run


def _result(request_id, result):
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id, code, message):
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def handle(message, run):
    """One JSON-RPC message in, response dict out (None for notifications)."""
    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
        return _error(message.get("id") if isinstance(message, dict) else None, -32600, "invalid request")
    method, request_id = message.get("method"), message.get("id")
    if request_id is None:
        return None  # notifications, e.g. notifications/initialized
    params = message.get("params") or {}
    if method == "initialize":
        asked = params.get("protocolVersion")
        version = asked if asked in PROTOCOL_VERSIONS else PROTOCOL_VERSIONS[0]
        return _result(request_id, {"protocolVersion": version, "capabilities": {"tools": {}}, "serverInfo": SERVER_INFO})
    if method == "ping":
        return _result(request_id, {})
    if method == "tools/list":
        return _result(request_id, {"tools": TOOLS})
    if method == "tools/call":
        name = params.get("name")
        try:
            argv, payload = command_for(name, params.get("arguments") or {})
        except KeyError:
            return _error(request_id, -32602, "unknown tool: " + str(name))
        except ValueError as exc:
            return _result(request_id, {"content": [{"type": "text", "text": str(exc)}], "isError": True})
        try:
            code, text = run(argv, payload)
        except Exception as exc:  # a failed subprocess is a tool error, not a protocol error
            return _result(request_id, {"content": [{"type": "text", "text": type(exc).__name__ + ": " + str(exc)}], "isError": True})
        if len(text) > OUTPUT_LIMIT:
            text = text[:OUTPUT_LIMIT] + "\n[truncated]"
        return _result(request_id, {"content": [{"type": "text", "text": text}], "isError": bool(code)})
    return _error(request_id, -32601, "method not found: " + str(method))


def serve(vault, stdin=None, stdout=None):
    run = make_runner(vault)
    stdin = stdin or sys.stdin.buffer
    stdout = stdout or sys.stdout.buffer
    for raw in stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            response = handle(json.loads(raw.decode("utf-8")), run)
        except ValueError:
            response = _error(None, -32700, "parse error")
        if response is not None:
            stdout.write((json.dumps(response, ensure_ascii=False) + "\n").encode("utf-8"))
            stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(serve(Path(__file__).resolve().parents[2]))
