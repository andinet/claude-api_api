"""
examples.py
Runnable examples showing how to use ClaudeClient in a real project.

Before running:
    1. Start the server:  cd ../server && uvicorn server:app --port 3000
    2. Run this file:     python examples.py
"""

from claude_client import ClaudeClient

client = ClaudeClient(base_url="http://localhost:3000")


# ── Example 1: Health check ───────────────────────────────────────────────────

def example_health_check():
    print("=== Health Check ===")
    if client.health():
        print("✅ Server is up\n")
    else:
        print("❌ Server is not reachable — is it running?\n")


# ── Example 2: Simple Q&A (read-only, safe) ───────────────────────────────────

def example_ask():
    print("=== Simple Q&A (read-only) ===")
    response = client.ask("What is the difference between a list and a tuple in Python?")
    print("Answer:", response.text())
    print(f"Took {response.duration_ms}ms\n")


# ── Example 3: Analyse a local project folder ─────────────────────────────────

def example_analyse_project():
    print("=== Analyse a project folder ===")
    # Point this at any local directory you want Claude to inspect
    project_path = "."  # current directory

    response = client.ask(
        prompt="List the main files in this project and summarise what each one does.",
        working_dir=project_path,
    )
    print(response.text())
    print(f"Cost: ${response.cost_usd or 'n/a'}\n")


# ── Example 4: Code generation (full tools, higher max_turns) ─────────────────

def example_code_generation():
    print("=== Code Generation ===")
    response = client.run(
        prompt="Write a Python function that reads a CSV file and returns a list of dicts.",
        max_turns=5,
    )
    print(response.text())
    print(f"Request ID: {response.request_id}\n")


# ── Example 5: Restricted tools (read + grep only) ────────────────────────────

def example_restricted_tools():
    print("=== Restricted Tools (Read + Grep only) ===")
    response = client.run(
        prompt="Find all files that import 'requests' and list them.",
        working_dir=".",
        allowed_tools=["Read", "Glob", "Grep", "LS"],
        max_turns=3,
    )
    print(response.text())
    print()


# ── Example 6: Streaming response ─────────────────────────────────────────────

def example_streaming():
    print("=== Streaming Response ===")
    print("Streaming chunks:\n")
    for chunk in client.stream(
        prompt="Explain what a REST API is in 3 sentences.",
        max_turns=2,
    ):
        # Each chunk is a parsed JSON dict from Claude's stream-json format
        print(chunk)
    print()


# ── Run all examples ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    example_health_check()
    example_ask()
    example_analyse_project()
    example_code_generation()
    example_restricted_tools()
    example_streaming()
