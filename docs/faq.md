# FAQ

---

### Does this use my Claude subscription or the paid API?

It uses your **Claude subscription** (Team or Enterprise plan).
The `claude -p` command draws from your account's daily usage limits — not from a separate pay-per-token API bill.
As of mid-2026, Anthropic paused a planned change that would have billed programmatic usage at API rates, so this remains subscription-based.

---

### Will my automated requests use up other team members' quota?

No. Each user has their own usage pool. Running automated jobs on your account does not affect anyone else on your team.

---

### What is `max_turns` and why does it matter?

Each "turn" is one step in Claude's agentic loop — read a file, write a file, run a command, etc.
More turns = more tokens consumed. Setting `max_turns=3` is a safety guardrail for background jobs so a loop doesn't accidentally exhaust your daily quota.

Recommended values:
- **Q&A / analysis**: 2–3
- **Code generation**: 3–5
- **Multi-file refactors**: 5–10

---

### What is `permission_mode`?

Controls how Claude handles actions it's not sure about:

| Mode | Behaviour |
|---|---|
| `bypassPermissions` | Never prompts — just does it. Good for full automation. |
| `acceptEdits` | Auto-accepts file edits but may pause on shell commands. |
| `default` | Interactive — pauses and asks. Not useful for headless use. |

For this API server, `bypassPermissions` is the default because there's no terminal to respond to prompts.

---

### How do I lock Claude to read-only?

Either use the `/run/read-only` endpoint, or pass `allowed_tools: ["Read", "Glob", "Grep", "LS"]` to `/run`.
Claude will be physically unable to write files or execute commands regardless of what the prompt says.

---

### Can I run multiple requests in parallel?

Yes, but be mindful of your usage limits.
Each request spawns a subprocess running `claude -p`. Running many in parallel will burn through your daily quota faster.
A safe pattern is to queue requests and process them one or a few at a time rather than firing them all simultaneously.

---

### How do I point Claude at a specific project folder?

Pass `working_dir` in the request body:
```json
{
  "prompt": "Find all TODO comments",
  "working_dir": "/home/user/myproject"
}
```
Claude will treat that directory as its working root for all file operations.

---

### Can I deploy this server somewhere other than localhost?

Yes — run it on any server with `uvicorn server:app --host 0.0.0.0 --port 3000`.
If you expose it publicly, add authentication (e.g. an API key header check) to prevent unauthorized use.
Since the server can execute Claude with `bypassPermissions`, leaving it open is a security risk.

---

### Where do I see the interactive API docs?

Start the server and visit: `http://localhost:3000/docs`
FastAPI generates a full Swagger UI automatically.
