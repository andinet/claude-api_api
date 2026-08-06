"""
Claude Code CLI → HTTP API
Wraps `claude -p` (headless mode) as a REST API using FastAPI.

Requirements:
    pip install fastapi uvicorn

Run:
    uvicorn server:app --reload --port 3000
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI(
    title="Claude Code CLI API",
    description="Wraps the Claude Code CLI (claude -p) as an HTTP API",
    version="1.0.0",
)


# ── Request / Response models ─────────────────────────────────────────────────

class RunRequest(BaseModel):
    prompt: str
    max_turns: int = 3
    output_format: str = "json"                 # "json" | "text" | "stream-json"
    permission_mode: str = "bypassPermissions"
    working_dir: Optional[str] = None
    allowed_tools: Optional[list[str]] = None


class RunResponse(BaseModel):
    request_id: str
    prompt: str
    result: str | dict
    cost_usd: Optional[float]
    duration_ms: int
    timestamp: str


# ── Core helper ───────────────────────────────────────────────────────────────

def build_command(req: RunRequest) -> list[str]:
    cmd = [
        "claude",
        "--print",
        req.prompt,
        f"--permission-mode={req.permission_mode}",
        f"--max-turns={req.max_turns}",
        f"--output-format={req.output_format}",
    ]
    if req.allowed_tools:
        cmd += ["--allowedTools", ",".join(req.allowed_tools)]
    return cmd


async def run_claude(req: RunRequest) -> tuple[str, int]:
    cmd = build_command(req)
    start = asyncio.get_event_loop().time()
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=req.working_dir,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
    except asyncio.TimeoutError:
        proc.kill()
        raise HTTPException(status_code=504, detail="Claude CLI timed out after 300s")

    duration_ms = int((asyncio.get_event_loop().time() - start) * 1000)

    if proc.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"Claude CLI error (exit {proc.returncode}): {stderr.decode().strip()}",
        )
    return stdout.decode().strip(), duration_ms


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.post("/run", response_model=RunResponse)
async def run(req: RunRequest):
    """Run a prompt through Claude Code CLI and return the result."""
    raw, duration_ms = await run_claude(req)

    result: str | dict = raw
    cost_usd = None
    if req.output_format == "json":
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                # CLI returns a list of events; the result event holds the answer and cost
                result_event = next((e for e in parsed if e.get("type") == "result"), None)
                if result_event:
                    result = result_event.get("result", "")
                    cost_usd = result_event.get("total_cost_usd") or result_event.get("cost_usd")
                else:
                    result = parsed
            else:
                result = parsed
                cost_usd = parsed.get("cost_usd") or parsed.get("total_cost_usd")
        except json.JSONDecodeError:
            result = raw

    return RunResponse(
        request_id=str(uuid.uuid4()),
        prompt=req.prompt,
        result=result,
        cost_usd=cost_usd,
        duration_ms=duration_ms,
        timestamp=datetime.utcnow().isoformat(),
    )


@app.post("/run/stream")
async def run_stream(req: RunRequest):
    """Stream Claude's output as Server-Sent Events."""
    req.output_format = "stream-json"
    cmd = build_command(req)

    async def event_generator():
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=req.working_dir,
        )
        async for line in proc.stdout:
            text = line.decode().strip()
            if text:
                yield f"data: {text}\n\n"
        await proc.wait()
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/run/read-only")
async def run_read_only(req: RunRequest):
    """Lock Claude to read-only tools — safe for analysis tasks."""
    req.allowed_tools = ["Read", "Glob", "Grep", "LS"]
    req.permission_mode = "bypassPermissions"
    return await run(req)
