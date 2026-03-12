# claude-code-context-injector

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue) ![License: MIT](https://img.shields.io/github/license/VoxCore84/claude-code-context-injector) ![GitHub release](https://img.shields.io/github/v/release/VoxCore84/claude-code-context-injector)

Keyword-aware context injection for Claude Code -- smarter than git status on every prompt.

## The Problem

The common community pattern for Claude Code hooks is to inject `git status`, `git diff`, or other project state on **every single prompt**. That means typing "yes", "ok", or "continue" dumps hundreds of tokens of context that Claude already knows. It wastes your context window, adds noise, and slows things down.

## The Solution

This hook watches what you actually type. It pattern-matches keywords in your prompt against a configurable set of categories, and **only injects context when it is relevant**. Ask about Django? You get Django context. Ask about Docker? You get DevOps context. Say "yes"? Nothing injected. Zero waste.

## Architecture

```
User types prompt
       |
       v
 .claude/settings.local.json
 routes to UserPromptSubmit hook
       |
       v
 context-injector.py reads stdin
 (JSON: {"prompt": "..."})
       |
       v
 Load config.json categories
       |
       v
 Keyword matching (case-insensitive)
       |
       |-- No match, or prompt too short --> exit silently (no injection)
       |
       |-- Match one or more categories  --> stdout JSON:
       |                                     {"additionalContext": "..."}
       v
 Claude sees injected context
 as part of the conversation
```

## Features

- **Keyword-driven**: Only injects context when the prompt matches configured keywords
- **Multi-category**: A single prompt can trigger multiple categories (e.g., "write a Django test" hits both Python/Django and Testing)
- **Short-prompt skip**: Prompts under a configurable length (default: 10 characters) are ignored entirely -- "yes", "ok", "go" never trigger injection
- **Case-insensitive**: Keywords match regardless of capitalization
- **Config-driven**: All categories live in `config.json` -- no code changes needed to add, remove, or edit categories
- **Zero dependencies**: Pure Python 3, no pip packages required

## Installation

### 1. Copy the files into your project

```bash
# From your project root:
mkdir -p .claude/hooks
cp context-injector.py .claude/hooks/
cp config.json .claude/hooks/
```

### 2. Edit config.json

Replace the example categories with ones that match your project. See [Configuration](#configuration) below.

### 3. Add the hook to your Claude Code settings

Add the following to `.claude/settings.local.json` in your project root (create the file if it doesn't exist):

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"$CLAUDE_PROJECT_DIR/.claude/hooks/context-injector.py\""
          }
        ]
      }
    ]
  }
}
```

That's it. The hook runs automatically on every prompt, but only injects when keywords match.

## Configuration

All behavior is controlled by `config.json`, which sits alongside `context-injector.py`. The format:

```json
{
  "min_prompt_length": 10,
  "categories": [
    {
      "name": "Category Name",
      "keywords": ["keyword1", "keyword2", "keyword3"],
      "context": "CONTEXT [Category]: The text that gets injected when any keyword matches."
    }
  ]
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `min_prompt_length` | integer | Prompts shorter than this (after stripping whitespace) are skipped entirely. Default: `10`. |
| `categories` | array | List of category objects. |
| `categories[].name` | string | Human-readable label (not used by the script, just for your reference). |
| `categories[].keywords` | string[] | Keywords to match against the prompt. Case-insensitive substring match. |
| `categories[].context` | string | The context string injected into `additionalContext` when any keyword matches. |

### Tips for writing good categories

- **Be specific with keywords.** "test" is broad -- it will match "test", "latest", "contest". If that is too noisy, use more specific terms like "pytest", "jest", "test suite".
- **Keep context concise.** You are paying for these tokens on every matching prompt. State the essentials: where files live, what commands to run, what conventions to follow.
- **Prefix with `CONTEXT [Label]:`.** This makes it easy for Claude to distinguish injected context from user instructions.
- **Use multiple categories.** Five focused categories beat one giant blob. The hook injects only the ones that match.

### Example: adding a category for your API

```json
{
  "name": "REST API",
  "keywords": ["api", "endpoint", "route", "swagger", "openapi", "rest", "graphql"],
  "context": "CONTEXT [API]: API routes are in src/api/routes/. We use OpenAPI 3.1 specs in docs/api/. Authentication is JWT via the Authorization header. Rate limiting is configured in src/middleware/rateLimit.ts."
}
```

## How It Works

1. Claude Code fires the `UserPromptSubmit` hook, passing `{"prompt": "..."}` on stdin.
2. `context-injector.py` reads the JSON, extracts the prompt text.
3. If the prompt (after stripping whitespace) is shorter than `min_prompt_length`, the script exits silently -- nothing injected.
4. The prompt is lowercased and checked against each category's keywords (case-insensitive substring match).
5. Every matching category's `context` string is collected.
6. If any categories matched, the script writes `{"additionalContext": "..."}` to stdout (categories joined by double newlines).
7. If nothing matched, the script exits silently -- nothing injected.

## Comparison: Context Injector vs. Git-Status-On-Every-Prompt

| | Git status on every prompt | Context Injector |
|---|---|---|
| **Tokens per prompt** | Hundreds (full diff/status output) | Zero when not relevant; targeted text when relevant |
| **"yes" / "ok" / "continue"** | Full git status injected | Nothing injected |
| **Relevance** | Same blob regardless of topic | Only matching categories injected |
| **Configurability** | One-size-fits-all | Fully configurable per-project |
| **Multi-topic support** | N/A | Multiple categories can fire on one prompt |
| **Setup effort** | ~Same | ~Same (copy 2 files, add settings snippet) |

## Requirements

- Python 3.10+ (uses `list[str]` type hint syntax)
- Claude Code with hooks support

## License

MIT -- see [LICENSE](LICENSE).

---

Built by [VoxCore84](https://github.com/VoxCore84)
