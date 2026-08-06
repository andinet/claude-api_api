# Claude Code CLI → HTTP API

Expose the **Claude Code CLI** (`claude -p`) as a local HTTP API, then call it from any Python project using the included client library.

```
claude-cli-api/
├── server/
│   ├── server.py          # FastAPI server wrapping the claude CLI
│   └── requirements.txt
├── client/
│   ├── claude_client.py   # Python client library
│   ├── examples.py        # Runnable usage examples
│   └── requirements.txt
└── docs/
    ├── endpoints.md       # API endpoint reference
    └── faq.md             # Common questions
```

---

## Prerequisites

- **Claude Code CLI** installed and authenticated (`claude --version` should work)
- Python 3.11+
- Your Claude Team or Enterprise plan — usage draws from your subscription

---

## Quickstart

### 1. Start the server

```bash
cd server
pip install -r requirements.txt
uvicorn server:app --reload --port 3000
```

The server is now running at `http://localhost:3000`.  
Visit `http://localhost:3000/docs` for the interactive Swagger UI.

### 2. Call it from your project

```bash
cd client
pip install -r requirements.txt
python examples.py
```

Or use the client in your own code:

```python
from claude_client import ClaudeClient

client = ClaudeClient(base_url="http://localhost:3000")

# Simple read-only question
response = client.ask("What does this codebase do?", working_dir="/path/to/project")
print(response.text())

# Full run with file access
response = client.run(
    prompt="Find and fix all type errors in src/",
    working_dir="/path/to/project",
    max_turns=5,
)
print(response.text())
print(f"Cost: ${response.cost_usd}")
```

---

## Client methods

| Method | Description | Tools |
|---|---|---|
| `client.ask(prompt, working_dir?)` | Read-only Q&A — cannot write or execute | Read, Glob, Grep, LS |
| `client.run(prompt, ...)` | Full run — all tools available | All (or pass `allowed_tools`) |
| `client.stream(prompt, ...)` | Stream output chunk by chunk | All |
| `client.health()` | Check if server is up | — |

---

## Key options

```python
client.run(
    prompt="...",
    max_turns=3,           # Max agentic loop steps. Keep low to control usage.
    working_dir="/path",   # Directory Claude operates in.
    allowed_tools=["Read", "Glob"],  # Restrict what Claude can touch.
)
```

> **`max_turns`** is the most important guardrail. Each turn can consume tokens,
> so for background automation keep this at 3–5. Raise it only for complex multi-step tasks.

---

## Endpoints summary

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness check |
| POST | `/run` | Full run, returns complete response |
| POST | `/run/stream` | Streaming run via SSE |
| POST | `/run/read-only` | Locked to read-only tools |

Full reference → [`docs/endpoints.md`](docs/endpoints.md)

---

## FAQ

See [`docs/faq.md`](docs/faq.md) for common questions about billing, tool permissions, and deployment.
