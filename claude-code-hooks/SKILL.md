---
name: claude-code-hooks
description: "Dispatch Claude Code tasks with automatic Telegram callback. Use when you need to run a code task and notify a Telegram group when done."
---

# Claude Code Hooks

Dispatch Claude Code tasks with **automatic Telegram callback**.

## When to use this skill

✅ **Use hooks skill when:**
- Task result needs to be sent to a Telegram group
- Background task with notification
- User wants to be notified when task completes

❌ **Use code skill instead when:**
- Simple one-off code tasks
- No callback needed
- Direct output to console

## Quick Start

```bash
# Basic dispatch with Telegram notification
~/.claude/skills/claude-code-hooks/scripts/dispatch-claude-code.sh \
  -p "Your task prompt here" \
  -n "task-name" \
  -g "-1003856805564"

# With working directory
~/.claude/skills/claude-code-hooks/scripts/dispatch-claude-code.sh \
  -p "Your task prompt here" \
  -n "task-name" \
  -g "-1003856805564" \
  -w /path/to/workspace
```

## Parameters

| Flag | Description | Required |
|------|-------------|----------|
| `-p` | Task prompt | ✅ Yes |
| `-n` | Task name (for tracking) | No |
| `-g` | Telegram group ID for callback | No |
| `-t` | Telegram topic/thread ID (forum topic) | No |
| `-w` | Working directory | No |
| `--agent-teams` | Enable Agent Teams mode | No |
| `--permission-mode` | Permission mode (plan/auto-approve) | No |

## How it works

1. Writes task metadata to `~/.claude/data/claude-code-results/task-meta.json`
2. Runs Claude Code via the local `claude_code_run.py` runner in this skill
3. When Claude Code finishes, Stop hook fires automatically
4. Hook reads metadata and output, then writes `latest.json` and `pending-wake.json`
5. Optional OpenClaw delivery can read those Claude-local artifacts and relay results

## Environment Variables

| Variable | Description |
|----------|-------------|
| `CLAUDE_CODE_BIN` | Path to claude binary (default: `claude`) |
| `ANTHROPIC_AUTH_TOKEN` | Anthropic API token |
