# API Endpoint Reference

Base URL: `http://localhost:3000` (default)

---

## GET `/health`

Liveness check.

**Response**
```json
{
  "status": "ok",
  "timestamp": "2026-08-06T10:00:00.000000"
}
```

---

## POST `/run`

Run a prompt through Claude Code CLI. Waits for the full response.

**Request body**

| Field | Type | Default | Description |
|---|---|---|---|
| `prompt` | string | required | The task or question |
| `max_turns` | int | `3` | Max agentic loop steps |
| `output_format` | string | `"json"` | `"json"` or `"text"` |
| `permission_mode` | string | `"bypassPermissions"` | `"bypassPermissions"`, `"default"`, or `"acceptEdits"` |
| `working_dir` | string | `null` | Directory Claude operates in |
| `allowed_tools` | string[] | `null` | Whitelist of tools (null = all allowed) |

**Example request**
```json
{
  "prompt": "Summarise what each file in the src/ folder does",
  "max_turns": 3,
  "working_dir": "/home/user/myproject",
  "allowed_tools": ["Read", "Glob", "LS"]
}
```

**Response**
```json
{
  "request_id": "3f9a2b1c-...",
  "prompt": "Summarise what each file...",
  "result": { ... },
  "cost_usd": 0.0012,
  "duration_ms": 4200,
  "timestamp": "2026-08-06T10:00:04.000000"
}
```

**Errors**

| Status | Meaning |
|---|---|
| 500 | Claude CLI exited with an error |
| 504 | Claude CLI timed out (300s limit) |

---

## POST `/run/stream`

Same as `/run` but streams output as **Server-Sent Events (SSE)**.

Each event is a JSON object on a `data:` line. The stream ends with `data: [DONE]`.

**Example SSE output**
```
data: {"type": "text", "text": "Here are the files..."}
data: {"type": "text", "text": " src/main.py handles routing"}
data: [DONE]
```

**Python consumption**
```python
for chunk in client.stream("Explain this project"):
    print(chunk)
```

---

## POST `/run/read-only`

Convenience wrapper around `/run` that locks `allowed_tools` to:
`["Read", "Glob", "Grep", "LS"]`

Claude **cannot** write files, run shell commands, or make network calls.
Use this for safe analysis and Q&A tasks.

**Request body** — same as `/run` (any `allowed_tools` you pass will be ignored).

---

## Available tools reference

| Tool | What it does |
|---|---|
| `Read` | Read file contents |
| `Glob` | Find files by pattern |
| `Grep` | Search file contents |
| `LS` | List directory contents |
| `Write` | Write or overwrite a file |
| `Edit` | Make targeted edits to a file |
| `Bash` | Run shell commands |
| `WebSearch` | Search the web |

Pass a subset to `allowed_tools` to restrict Claude's access to only those operations.
