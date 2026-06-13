# JSON Envelope

The Nollm JSON envelope is a dependency-free bridge format for external tools.

It is not MCP. It does not start a server, open a socket, call a model, or add a transport layer.

## Request

```json
{
  "protocol": "nollm.tool.v0.1",
  "request_id": "req_001",
  "action": "nollm.recall",
  "notebook_path": "/path/to/notebook",
  "actor": "codex",
  "actor_type": "tool",
  "input": {
    "query_or_task": "why not make Nollm Cognee-like?"
  }
}
```

## Success Response

```json
{
  "ok": true,
  "protocol": "nollm.tool.v0.1",
  "request_id": "req_001",
  "action": "nollm.recall",
  "result": {},
  "warnings": [],
  "ledger_events": [],
  "addresses": []
}
```

## Error Response

```json
{
  "ok": false,
  "protocol": "nollm.tool.v0.1",
  "request_id": "req_001",
  "action": "nollm.unknown",
  "error": {
    "code": "unknown_action",
    "message": "Unknown tool action."
  },
  "warnings": []
}
```

Errors are structured values. Unknown actions, malformed JSON files, non-object JSON requests, and missing required fields must not escape as unhandled exceptions.

`request_id` is optional. If present, it is echoed in success and error responses.

Allowed tool bridge `actor_type` values are `human`, `llm`, `tool`, and `system`. The default bridge actor is `tool_user` with `actor_type: tool`.

## Path Resolution

`notebook_path` is resolved relative to the current working directory of the `nollm tool` process.

It is not resolved relative to the request JSON file.

Repository example requests that are marked runnable state their working directory explicitly. The OpenClaw scale-scan recall example is run from `reference/python`:

```bash
cd reference/python
python3 -m nollm.cli tool ../../examples/tool_requests/recall_scale_scan.json
```

The request uses `notebook_path: "../../examples/openclaw"` because that path resolves from the process working directory.
