#!/usr/bin/env python3
"""
Claude Code UserPromptSubmit Hook: Keyword-Aware Context Injection

Instead of injecting git status (or other boilerplate) on every single prompt,
this hook pattern-matches keywords in the user's message and injects only the
context that is actually relevant. Short prompts like "yes", "ok", and
"continue" get nothing injected -- zero wasted tokens.

Usage:
    Registered as a UserPromptSubmit hook in .claude/settings.local.json.
    Reads category definitions from config.json (same directory as this script,
    or $CLAUDE_PROJECT_DIR/.claude/hooks/).

Protocol:
    stdin  -> JSON with {"prompt": "..."}
    stdout <- JSON with {"additionalContext": "..."} (or empty for no injection)
"""

import json
import os
import sys
from pathlib import Path


def load_config() -> dict:
    """Load config.json from the same directory as this script, falling back to
    $CLAUDE_PROJECT_DIR/.claude/hooks/config.json."""
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir / "config.json",
    ]

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if project_dir:
        candidates.append(Path(project_dir) / ".claude" / "hooks" / "config.json")

    for path in candidates:
        if path.is_file():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)

    return {"categories": [], "min_prompt_length": 10}


def detect_and_inject(prompt: str, config: dict) -> list[str]:
    """Match prompt text against keyword categories and return context strings
    for every category that matches."""
    min_length = config.get("min_prompt_length", 10)
    if len(prompt.strip()) < min_length:
        return []

    prompt_lower = prompt.lower()
    context_parts: list[str] = []

    for category in config.get("categories", []):
        keywords = category.get("keywords", [])
        context = category.get("context", "")
        if not keywords or not context:
            continue
        if any(kw.lower() in prompt_lower for kw in keywords):
            context_parts.append(context)

    return context_parts


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        # Malformed input -- exit silently, don't block the user.
        sys.exit(0)

    prompt = data.get("prompt", "")
    if not prompt:
        sys.exit(0)

    config = load_config()
    injections = detect_and_inject(prompt, config)

    if injections:
        result = {"additionalContext": "\n\n".join(injections)}
        json.dump(result, sys.stdout)


if __name__ == "__main__":
    main()
