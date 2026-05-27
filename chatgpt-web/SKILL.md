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
- Return only the final answer and essential metadata unless debugging is requested.
- Do not copy, export, or transmit browser cookies or login credentials.

## Commands

Helper path:

```bash
~/.agents/skills/chatgpt-web/scripts/chatgpt_web.py
```

Check and auto-wake OpenCLI/Chrome:

```bash
~/.agents/skills/chatgpt-web/scripts/chatgpt_web.py doctor
```

List saved topics:

```bash
~/.agents/skills/chatgpt-web/scripts/chatgpt_web.py list
```

Discover conversations currently visible in the ChatGPT sidebar:

```bash
~/.agents/skills/chatgpt-web/scripts/chatgpt_web.py discover
```

Select one visible conversation for future continuation:

```bash
~/.agents/skills/chatgpt-web/scripts/chatgpt_web.py select "$TOPIC_HINT"
```

Continue the latest topic:

```bash
~/.agents/skills/chatgpt-web/scripts/chatgpt_web.py ask "$PROMPT"
```

Continue a named or approximate topic:

```bash
~/.agents/skills/chatgpt-web/scripts/chatgpt_web.py ask "$PROMPT" --topic "$TOPIC_HINT"
```

Force a new topic only when the user asks:

```bash
~/.agents/skills/chatgpt-web/scripts/chatgpt_web.py ask "$PROMPT" --new --title "$TITLE"
```

Ask ChatGPT to use web search/current knowledge:

```bash
~/.agents/skills/chatgpt-web/scripts/chatgpt_web.py ask "$PROMPT" --search
```

Delegate a research/analysis task to the selected existing ChatGPT conversation:

```bash
~/.agents/skills/chatgpt-web/scripts/chatgpt_web.py delegate "$TASK"
```

Preview a delegation prompt without sending anything:

```bash
~/.agents/skills/chatgpt-web/scripts/chatgpt_web.py delegate "$TASK" --dry-run
```

## State

The helper stores conversation metadata in:

```bash
~/.agents/state/chatgpt-web.json
```

The state file stores topic title, URL, short summary, update time, and the last active topic. It does not store cookies or passwords.

## Failure Handling

| Failure | Action |
|---|---|
| `doctor` cannot connect | Report the helper's exact error. The usual manual fix is reloading `chrome://extensions/?id=fgjlgolohmlcolemabeejnojncnlkjhg`. |
| ChatGPT asks for login | Ask the user to log in in the normal Chrome profile. Do not move cookies. |
| Topic match is clearly ambiguous | Run `list`, show the likely topic titles, and ask the user which one to continue. |
| Script output is too long | Summarize the ChatGPT answer, but keep the topic URL and any source links. |

## Design Notes

OpenCLI is not a pure static CLI adapter for `chatgpt.com`; for ChatGPT web it works as a local browser bridge: a local daemon talks to a Chrome extension, which controls a real logged-in browser session. This is closer to a local MCP/browser bridge than a simple HTTP CLI.
