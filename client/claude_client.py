"""
claude_client.py
A simple Python client for the Claude Code CLI API server.

Usage:
    from claude_client import ClaudeClient

    client = ClaudeClient(base_url="http://localhost:3000")
    response = client.run("Summarise the main purpose of this repo")
    print(response.result)
"""

import json
import requests
from dataclasses import dataclass
from typing import Optional, Generator


@dataclass
class ClaudeResponse:
    request_id: str
    prompt: str
    result: str | dict
    cost_usd: Optional[float]
    duration_ms: int
    timestamp: str

    def text(self) -> str:
        """Extract plain text from result regardless of format."""
        if isinstance(self.result, dict):
            # Claude JSON output nests the answer under different keys
            return (
                self.result.get("result")
                or self.result.get("content")
                or json.dumps(self.result, indent=2)
            )
        return str(self.result)


class ClaudeClient:
    """
    Thin HTTP wrapper around the Claude Code CLI API server.

    Args:
        base_url:   Where the server is running, e.g. "http://localhost:3000"
        timeout:    Request timeout in seconds (default 300)
    """

    def __init__(self, base_url: str = "http://localhost:3000", timeout: int = 300):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    # ── health ────────────────────────────────────────────────────────────────

    def health(self) -> bool:
        """Return True if the server is reachable and healthy."""
        try:
            r = self.session.get(f"{self.base_url}/health", timeout=5)
            return r.status_code == 200
        except requests.RequestException:
            return False

    # ── core run ──────────────────────────────────────────────────────────────

    def run(
        self,
        prompt: str,
        max_turns: int = 3,
        working_dir: Optional[str] = None,
        allowed_tools: Optional[list[str]] = None,
    ) -> ClaudeResponse:
        """
        Send a prompt and wait for the full response.

        Args:
            prompt:        What you want Claude to do.
            max_turns:     Max agentic loop steps (keep low to control usage).
            working_dir:   Directory Claude will treat as its working root.
            allowed_tools: Whitelist of tools, e.g. ["Read", "Glob"].
                           Pass None to allow all tools.

        Returns:
            ClaudeResponse with .text() helper for easy access.

        Raises:
            requests.HTTPError on 4xx/5xx from the server.
        """
        payload = {
            "prompt": prompt,
            "max_turns": max_turns,
            "output_format": "json",
        }
        if working_dir:
            payload["working_dir"] = working_dir
        if allowed_tools:
            payload["allowed_tools"] = allowed_tools

        r = self.session.post(
            f"{self.base_url}/run",
            json=payload,
            timeout=self.timeout,
        )
        r.raise_for_status()
        data = r.json()
        return ClaudeResponse(**data)

    # ── read-only shortcut ────────────────────────────────────────────────────

    def ask(self, prompt: str, working_dir: Optional[str] = None) -> ClaudeResponse:
        """
        Read-only convenience method — Claude cannot write files or run commands.
        Good for Q&A, analysis, or summarisation tasks.
        """
        payload = {
            "prompt": prompt,
            "output_format": "json",
        }
        if working_dir:
            payload["working_dir"] = working_dir

        r = self.session.post(
            f"{self.base_url}/run/read-only",
            json=payload,
            timeout=self.timeout,
        )
        r.raise_for_status()
        return ClaudeResponse(**r.json())

    # ── streaming ─────────────────────────────────────────────────────────────

    def stream(
        self,
        prompt: str,
        max_turns: int = 3,
        working_dir: Optional[str] = None,
    ) -> Generator[dict, None, None]:
        """
        Stream Claude's response token-by-token via Server-Sent Events.

        Yields parsed JSON objects for each chunk.
        Stops when the server sends [DONE].

        Example:
            for chunk in client.stream("Explain this codebase"):
                print(chunk)
        """
        payload = {
            "prompt": prompt,
            "max_turns": max_turns,
            "output_format": "stream-json",
        }
        if working_dir:
            payload["working_dir"] = working_dir

        with self.session.post(
            f"{self.base_url}/run/stream",
            json=payload,
            stream=True,
            timeout=self.timeout,
        ) as r:
            r.raise_for_status()
            for raw_line in r.iter_lines():
                if not raw_line:
                    continue
                line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
                if line.startswith("data: "):
                    data = line[len("data: "):]
                    if data == "[DONE]":
                        return
                    try:
                        yield json.loads(data)
                    except json.JSONDecodeError:
                        yield {"raw": data}
