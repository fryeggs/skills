# Tooling Simplification and Repo Mastery Design

## Goal

Reduce duplicate skills and unstable wrappers while preserving the smallest reliable toolset. Replace the public `understand-*` family with one `repo-mastery` skill whose default mode is target-feature-driven learning and implementation.

## Approved Decisions

- Remove `opencli` and `chatgpt-web` from Codex, Claude, Agents, repository documentation, and current tooling backups.
- Remove `team-tasks` and `cli-anything`; use Codex orchestration/GSD for development coordination and Record and Replay for repeatable desktop workflows.
- Keep `node_repl` for DOM and Playwright automation. Record and Replay does not replace programmatic browser control.
- Keep `computer-use` for unsupported visual UI actions and `event-stream` because Record and Replay depends on it.
- Keep Record and Replay as the preferred route for turning repeated desktop actions into dedicated skills.
- Keep `claude-hud` as an enabled Claude-only plugin and verify its status-line integration is active, not merely installed.
- Remove the stale `memory-lancedb-pro` MCP registration after confirming its configured server path is absent.
- Remove the duplicate alpha `browser-use` plugin and keep the stable Browser/Chrome plugins.
- Narrow `web-content-learner` to media download, subtitle extraction, and Whisper transcription; ordinary web research uses the available browser/web tooling.
- Keep Codex as the canonical source. Claude receives only symlinks for shared custom skills and retains Claude-only wrappers.

## Repo Mastery

`repo-mastery` is the only user-facing entry for learning a repository and extending it. Typical trigger:

> Find or use this GitHub repository, help me learn it, then add feature X.

Default workflow:

1. Resolve the repository URL or use GitHub discovery when no repository is supplied.
2. Check license, activity, maintenance signals, security-sensitive setup, and local workspace state.
3. Clone or locate the repository without overwriting an active directory.
4. Build a concise architecture and domain map with Codegraph and direct source inspection.
5. Derive a learning path focused on the requested feature, including the smallest prerequisite modules and executable exercises.
6. Produce a change specification covering files, interfaces, risks, tests, and acceptance commands.
7. Implement in an isolated worktree for complex changes; use the repository's existing tools and patterns.
8. Run static checks, tests, builds, and target-specific runtime verification.
9. Explain the final diff, architectural consequences, trade-offs, and follow-up learning tasks.

The previous `understand`, `understand-chat`, `understand-explain`, `understand-diff`, `understand-domain`, `understand-onboard`, `understand-dashboard`, and `understand-knowledge` functions become internal stages rather than separate public skills. Their source is retained only when required as an implementation dependency; duplicate Codex/Claude/Agents links are removed.

## Skill Structure

Create the canonical skill at `~/.codex/skills/repo-mastery` with:

- `SKILL.md`: concise trigger and orchestration rules.
- `agents/openai.yaml`: generated UI metadata.
- `references/stages.md`: optional stage details loaded only when needed.
- `tests/`: deterministic checks for structure, trigger coverage, default mode, safety gates, and legacy-name removal.

Claude and Agents receive symlinks to the Codex canonical directory. The GitHub `fryeggs/skills` repository contains the maintained source and user-facing README.

## Safety and Backup

Before deletion, archive all affected live paths and sanitized configuration into a timestamped temporary backup. Do not include API keys, tokens, cookies, passwords, SSH keys, environment values, dependency caches, or browser profiles. Preserve recoverability in Git history and the private `fryeggs/ai-agent-config` repository before removing the temporary local backup.

Do not modify Tailscale, Clash/Mihomo, SSH, VPN, DNS, routing, firewall, ports, or server network configuration.

## Documentation and GitHub

Update all current README/ownership files in:

- `fryeggs/skills`: current skill catalog, installation model, `repo-mastery` usage, and removed skills.
- `fryeggs/ai-agent-config`: compact retained-tool inventory, sanitized MCP/plugin inventory, archive descriptions, hashes, and ownership rules.
- Global `AGENTS.md` and `CLAUDE.md`: remove `chatgpt-web`, OpenCLI, and removed-skill rules; retain concise Record, browser, safety, verification, and Qwen guidance.

Do not rewrite remote Git history. Current commits and current backup contents are updated normally, then remote commit/tree state is verified.

## Validation

- Baseline tests must fail before `repo-mastery` exists or while legacy public entries remain.
- Validate skill frontmatter and generated metadata with the system skill validator.
- Verify `repo-mastery` resolves from Codex, Claude, and Agents to one canonical directory.
- Verify removed live paths and stale registrations are absent.
- Verify retained MCP servers and plugins still resolve, especially `node_repl`, `computer-use`, and `event-stream`.
- Scan changed Markdown, configuration, archives, and Git diffs for secret-like values; redact any findings.
- Verify both Git repositories are clean, pushed, and match their remotes.

## Non-Goals

- No network or remote-host configuration changes.
- No new shared `~/.ai-tools` directory.
- No recreation of deleted ChatGPT web automation.
- No replacement of stable CLI/API automation with recorded UI actions when deterministic tools are simpler.
