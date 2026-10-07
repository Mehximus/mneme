# Mneme MCP sunucusu

Hook desteği olmayan istemciler (Claude Desktop, Cursor, Zed vb.) Mneme'yi MCP üzerinden kullanabilir. Sunucu standart kütüphaneyle yazılmıştır, ek paket gerekmez. Her araç vault'un kendi `mneme.py --json` komutunu çalıştırır; gizli bilgi süzme, revision kontrolü ve reddetme kuralları CLI ile aynıdır.

## Araçlar

| Araç | Ne yapar |
|---|---|
| `mneme_search` | Vault'ta kaynak bağlantılı arama (`query`, isteğe bağlı `project`, `limit`) |
| `mneme_note_create` | `notes/` veya `knowledge/` altında yeni not; var olanı ezmez |
| `mneme_note_edit` | Var olan notun gövdesini değiştirir (`append`, `replace_section`, `upsert_card`) |
| `mneme_supersede` | Eski notu yenisiyle değiştirilmiş işaretler; hiçbir şey silinmez |
| `mneme_doctor` | Hafıza sağlığı |

Silme aracı yoktur. Görev, receipt ve üretilmiş görünümler `note-edit` ile değiştirilemez.

## Kurulum

Claude Desktop (`claude_desktop_config.json`) veya benzeri bir istemci:

```json
{"mcpServers": {"mneme": {"command": "py", "args": ["-3", "C:\yol\vault\mneme.py", "mcp"]}}}
```

macOS/Linux'ta `"command": "python3"` ve `"args": ["/yol/vault/mneme.py", "mcp"]` kullan.

Claude Code için: `claude mcp add mneme -- py -3 C:\yol\vault\mneme.py mcp`
