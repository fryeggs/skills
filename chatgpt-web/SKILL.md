---
name: chatgpt-web
description: "Delegate research, web search, analysis, drafting, and brainstorming to the user's logged-in ChatGPT web session through OpenCLI, especially when conserving Codex usage; also use for topic continuation and second opinions."
---

# ChatGPT Web

Drive the user's logged-in `https://chatgpt.com/` session through OpenCLI and return ChatGPT's latest web answer inside the current CLI/agent response.

## Core Rules

- Use the helper script first; do not manually recreate the OpenCLI workflow unless the script fails.
- Use a real Chrome session plus the OpenCLI extension. Do not use headless browser mode.
- Run in the background as much as Chrome/OpenCLI allow. The helper auto-wakes Chrome with the OpenCLI extension popup when needed.
- Default behavior is continue the last saved topic. Create a new ChatGPT topic only when the user explicitly asks for a new topic.
- If a saved topic redirects to the home page or is no longer accessible, stop without sending a prompt; never silently turn continuation into a new conversation.
- If the user names a topic or gives a rough description, pass it with `--topic`; the helper will match saved topic titles, summaries, and URLs.
- Prefer delegation for research, web search, reading, comparisons, analysis, summaries, drafting, and brainstorming when the user wants to conserve Codex usage. Keep local operations, verification, and implementation in Codex.
- If delegated ChatGPT work reports a usage limit or cannot proceed, report that limitation and let Codex handle only the necessary fallback work.
- **Default return mode is `capsule`**: returns only structured JSON extract + URL, not the full web answer. Use `--return-mode full` only when explicitly needed.
- Do not copy, export, or transmit browser cookies or login credentials.

## Return Modes

The helper supports three return modes to control token usage:

| Mode | Description | Use Case |
|------|-------------|----------|
| `capsule` (default) | Structured JSON extract with conclusion, evidence, uncertainties, and actions | Most research tasks - saves tokens |
| `receipt` | Status + topic title + URL only | When you just need to know it's done |
| `full` | Complete web answer | When explicitly requested by user |

Capsule mode appends a protocol instruction to the prompt, asking ChatGPT to output a `<codex_capsule>` JSON block. If extraction fails, it returns failure status + URL without falling back to full text.

## Commands

Helper path:

```bash
~/.codex/skills/chatgpt-web/scripts/chatgpt_web.py
```

Check and auto-wake OpenCLI/Chrome:

```bash
~/.codex/skills/chatgpt-web/scripts/chatgpt_web.py doctor
```

List saved topics:

```bash
~/.codex/skills/chatgpt-web/scripts/chatgpt_web.py list
```

Discover conversations currently visible in the ChatGPT sidebar:

```bash
~/.codex/skills/chatgpt-web/scripts/chatgpt_web.py discover
```

Select one visible conversation for future continuation:

```bash
~/.codex/skills/chatgpt-web/scripts/chatgpt_web.py select "$TOPIC_HINT"
```

Continue the latest topic (default capsule mode):

```bash
~/.codex/skills/chatgpt-web/scripts/chatgpt_web.py ask "$PROMPT"
```

Continue with receipt mode (status + URL only):

```bash
~/.codex/skills/chatgpt-web/scripts/chatgpt_web.py ask "$PROMPT" --return-mode receipt
```

Continue with full answer mode:

```bash
~/.codex/skills/chatgpt-web/scripts/chatgpt_web.py ask "$PROMPT" --return-mode full
```

Continue a named or approximate topic:

```bash
~/.codex/skills/chatgpt-web/scripts/chatgpt_web.py ask "$PROMPT" --topic "$TOPIC_HINT"
```

Force a new topic only when the user asks:

```bash
~/.codex/skills/chatgpt-web/scripts/chatgpt_web.py ask "$PROMPT" --new --title "$TITLE"
```

Ask ChatGPT to use web search/current knowledge:

```bash
~/.codex/skills/chatgpt-web/scripts/chatgpt_web.py ask "$PROMPT" --search
```

Keep the automation tab open after completion (for debugging):

```bash
~/.codex/skills/chatgpt-web/scripts/chatgpt_web.py ask "$PROMPT" --keep-open
```

Delegate a research/analysis task to the selected existing ChatGPT conversation:

```bash
~/.codex/skills/chatgpt-web/scripts/chatgpt_web.py delegate "$TASK"
```

Preview a delegation prompt without sending anything:

```bash
~/.codex/skills/chatgpt-web/scripts/chatgpt_web.py delegate "$TASK" --dry-run
```

## State

The helper stores conversation metadata in:

```bash
~/.agents/state/chatgpt-web.json
```

The state file stores topic title, URL, short summary, update time, and the last active topic. It does not store cookies or passwords.

Single-task lock file:

```bash
~/.agents/state/chatgpt-web.lock
```

Metrics (non-sensitive metadata only):

```bash
~/.agents/state/chatgpt-web-metrics.jsonl
```

## Window Management (macOS)

On macOS, the helper:
1. Generates a unique run ID for each task
2. Creates a dedicated background window via `opencli browser <unique-session> --window background open` with a marker URL (`https://chatgpt.com/#chatgpt-web-<run_id>`) and parses the returned target ID to establish ownership
3. Identifies the Chrome window containing the owned tab by scanning for the marker URL; **only minimizes if the owned tab is the sole tab in that window**
4. Navigates the same target to the ChatGPT topic URL
5. All subsequent browser operations use `--tab <targetId>` to target only the owned tab
6. Closes only the uniquely owned OpenCLI session window via `browser <unique-session> close` after completion (unless `--keep-open` is passed)

**Safety**: If the helper cannot uniquely identify the owned window, or if the owned tab shares a window with other tabs, it aborts before sending the prompt. Cleanup always attempts to close the owned tab even if identification fails, because the target ID proves ownership.

**Verified lifecycle**: A live OpenCLI/Chrome acceptance check confirmed that `--window background open` created a single-tab automation window and releasing the unique session removed it without sending a ChatGPT prompt. If a later environment places the owned tab in a shared window, the script will still stop before sending the prompt instead of minimizing a shared window.

## Failure Handling

| Failure | Action |
|---|---|
| `doctor` cannot connect | Report the helper's exact error. The usual manual fix is reloading `chrome://extensions/?id=fgjlgolohmlcolemabeejnojncnlkjhg`. |
| ChatGPT asks for login | Ask the user to log in in the normal Chrome profile. Do not move cookies. |
| Topic match is clearly ambiguous | Run `list`, show the likely topic titles, and ask the user which one to continue. |
| Script output is too long | Summarize the ChatGPT answer, but keep the topic URL and any source links. |
| Capsule extraction failed | Return failure status + URL only. Never fall back to full text in capsule mode. |
| Cannot identify owned window | Abort before sending prompt. Do not operate on user windows. |
| Owned tab shares window with other tabs | Abort before sending prompt. Close only the owned tab. |
| Another task is already running | Return error about existing lock. Wait for it to finish. |

## Design Notes

OpenCLI is not a pure static CLI adapter for `chatgpt.com`; for ChatGPT web it works as a local browser bridge: a local daemon talks to a Chrome extension, which controls a real logged-in browser session. This is closer to a local MCP/browser bridge than a simple HTTP CLI.

Token savings: Capsule mode reduces context usage compared to full mode by returning only structured extracts. Savings are estimated per recorded run in `chatgpt-web-metrics.jsonl`.
