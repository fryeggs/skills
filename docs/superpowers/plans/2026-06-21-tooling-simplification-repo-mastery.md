# Tooling Simplification and Repo Mastery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace redundant learning/tool wrappers with one target-feature-driven `repo-mastery` skill and publish a verified compact local/GitHub tool inventory.

**Architecture:** Maintain source skills in `fryeggs/skills`, install canonical copies under `~/.codex/skills`, and expose shared skills to Claude/Agents through symlinks. Keep stable native plugins and MCP servers; remove stale registrations, duplicate caches, and obsolete public skill entry points only after a sanitized backup.

**Tech Stack:** Markdown Agent Skills, YAML, shell, Python structural tests, Git, GitHub CLI, Codex/Claude plugin and MCP CLIs.

---

### Task 1: Capture Baseline and Backup

**Files:**
- Create: `/Users/qingshan/.claude/backups/tooling-simplification-<timestamp>.tar.gz`
- Inspect: `/Users/qingshan/.codex/skills`
- Inspect: `/Users/qingshan/.claude/skills`
- Inspect: `/Users/qingshan/.agents/skills`
- Inspect: `/Users/qingshan/.codex/config.toml`

- [ ] Record installed skill names, plugin status, MCP names, symlink targets, and both Git repository states without printing credential values.
- [ ] Archive affected skills, ownership files, sanitized plugin/MCP inventories, and repository README files with `tar`; exclude dependency caches, browser profiles, cookies, tokens, keys, and environment values.
- [ ] Verify the archive is non-empty with `tar -tzf` and calculate its SHA-256 hash.
- [ ] Stop before mutation if the archive cannot be created or inspected.

### Task 2: Add Failing Structural Tests

**Files:**
- Create: `/Users/qingshan/myproject/skills/tests/test_repo_mastery_structure.py`

- [ ] Write tests asserting that `repo-mastery/SKILL.md` exists, defaults to target-feature-driven learning, includes safety and validation gates, and that removed repository paths and README names are absent.
- [ ] Run `python3 -m unittest tests/test_repo_mastery_structure.py -v`.
- [ ] Verify RED: tests fail because `repo-mastery` does not yet exist and legacy entries remain.
- [ ] Commit the failing tests separately.

### Task 3: Create Repo Mastery

**Files:**
- Create: `/Users/qingshan/myproject/skills/repo-mastery/SKILL.md`
- Create: `/Users/qingshan/myproject/skills/repo-mastery/agents/openai.yaml`
- Create: `/Users/qingshan/myproject/skills/repo-mastery/references/stages.md`

- [ ] Initialize `repo-mastery` with the system `init_skill.py` generator and explicit UI metadata.
- [ ] Write concise triggering metadata for GitHub discovery, repository learning, onboarding, architecture/domain explanation, diff analysis, and target feature implementation.
- [ ] Encode the default workflow: resolve repository, assess safety/maintenance, map architecture, learn only prerequisites for the requested feature, specify, implement, verify, and teach back.
- [ ] Keep detailed stage guidance in `references/stages.md`; do not create a skill-local README.
- [ ] Validate with `quick_validate.py` and rerun the structural tests until GREEN.
- [ ] Commit the new skill and tests.

### Task 4: Remove Obsolete Skills and Public Understand Entries

**Files:**
- Delete: `/Users/qingshan/myproject/skills/chatgpt-web`
- Delete: `/Users/qingshan/myproject/skills/team-tasks`
- Delete: `/Users/qingshan/.codex/skills/chatgpt-web`
- Delete: `/Users/qingshan/.codex/skills/opencli`
- Delete: `/Users/qingshan/.codex/skills/team-tasks`
- Delete: `/Users/qingshan/.codex/skills/cli-anything`
- Delete: matching Claude/Agents links or copies
- Delete: public `understand*` links under Codex, Claude, and Agents
- Create: shared `repo-mastery` links under Claude and Agents

- [ ] Use `apply_patch` for tracked repository deletions and edits; use path-checked removal only for live installed copies and symlinks covered by the verified backup.
- [ ] Uninstall `cli-anything@cli-anything` through `claude plugin uninstall -s user -y` before removing leftover wrappers.
- [ ] Keep the underlying `~/.understand-anything` source only as a non-public implementation dependency; do not expose eight duplicate user-facing links.
- [ ] Copy the verified repository `repo-mastery` directory to `~/.codex/skills/repo-mastery`, then create Claude/Agents symlinks to that canonical directory.
- [ ] Verify every removed path is absent and both symlinks resolve to the Codex canonical copy.

### Task 5: Narrow Web Content Learner

**Files:**
- Modify: `/Users/qingshan/myproject/skills/web-content-learner/SKILL.md`
- Modify: `/Users/qingshan/.codex/skills/web-content-learner/SKILL.md`
- Modify: `/Users/qingshan/.codex/skills/web-content-learner/scripts/web_content_learner.py`
- Modify: `/Users/qingshan/.codex/skills/web-content-learner/requirements.txt`

- [ ] Add failing tests for media URL detection, download/transcription dispatch, and rejection of generic web-search/page-extraction modes.
- [ ] Remove Jina, Brave, generic webpage extraction, question search, and LLM-summary branches from the canonical script and dependencies.
- [ ] Retain yt-dlp, subtitle extraction, media download, and Whisper transcription with configurable output paths suitable for macOS.
- [ ] Make the repository source match the canonical installed implementation, including tests and required scripts.
- [ ] Run unit tests and skill validation; commit when GREEN.

### Task 6: Remove Stale MCP and Plugin State

**Files:**
- Modify through CLI: `/Users/qingshan/.codex/config.toml`
- Remove stale cache: `/Users/qingshan/.codex/plugins/cache/openai-bundled/browser-use`

- [ ] Reconfirm `/Users/qingshan/.openclaw/plugins/memory-lancedb-pro/mcp-server.mjs` is absent.
- [ ] Run `codex mcp remove memory-lancedb-pro` and verify it no longer appears in `codex mcp list`.
- [ ] Confirm `browser-use` is not installed according to `codex plugin list`, then remove only its stale alpha cache directory.
- [ ] Verify `node_repl`, `computer-use`, and `event-stream` remain enabled and their configured executables resolve.
- [ ] Verify stable Browser, Chrome, Computer Use, Record and Replay, GitHub, Superpowers, document, PDF, presentation, and spreadsheet plugins remain installed.

### Task 7: Update Global and Repository Documentation

**Files:**
- Modify: `/Users/qingshan/.codex/AGENTS.md`
- Modify: `/Users/qingshan/.claude/CLAUDE.md`
- Modify: `/Users/qingshan/.claude/TOOL_OWNERSHIP.md`
- Modify: `/Users/qingshan/myproject/skills/README.md`
- Modify: `/Users/qingshan/myproject/ai-agent-config/tooling-backup/README.md`
- Modify: `/Users/qingshan/myproject/ai-agent-config/tooling-backup/TOOL_OWNERSHIP.md`

- [ ] Remove rules and examples requiring `chatgpt-web`, OpenCLI, CLI Anything, Team Tasks, and separate Understand skills.
- [ ] Document `repo-mastery`, its target-feature-driven default, Record and Replay preference, retained deterministic browser tools, and `claude-hud` as an enabled Claude-only status-line plugin.
- [ ] Keep global instruction files concise and preserve all safety, verification, Qwen, Tailscale, and network protection rules.
- [ ] Replace the outdated skills README inventory and install instructions with the actual canonical-source/symlink model.
- [ ] Verify no README contains stale removed-tool claims.

### Task 8: Rebuild Compact Private Backup

**Files:**
- Replace: `/Users/qingshan/myproject/ai-agent-config/tooling-backup/archives/*.tar.gz`
- Replace: `/Users/qingshan/myproject/ai-agent-config/tooling-backup/config/*.json`
- Replace: `/Users/qingshan/myproject/ai-agent-config/tooling-backup/SHA256SUMS`

- [ ] Rebuild only retained custom/shared skill, Claude-only skill, Codex plugin-definition, and Claude plugin-wrapper archives; exclude caches and dependencies.
- [ ] Export plugin/MCP inventories with credential values omitted or replaced by `[REDACTED]`.
- [ ] Include `claude-hud` in the Claude-only wrapper archive and inventory.
- [ ] Recompute `SHA256SUMS` and verify every archive with `tar -tzf`.
- [ ] Scan archive file lists and extracted text metadata for secret-like patterns without printing any found value.

### Task 9: Final Verification and Publish

**Files:**
- Verify all changed files in both repositories and all live paths.

- [ ] Run all repository tests, `quick_validate.py`, `git diff --check`, Markdown line-count checks, symlink resolution checks, plugin lists, and MCP lists.
- [ ] Scan changed content for API key, token, cookie, password, private-key, and bearer-secret patterns; report only risk status and redacted filenames.
- [ ] Confirm no Tailscale, Clash/Mihomo, SSH, VPN, DNS, routing, firewall, port, or server-network configuration changed.
- [ ] Commit focused changes in `fryeggs/skills` and `fryeggs/ai-agent-config`.
- [ ] Push both `main` branches and verify local HEAD, remote branch commit, and remote tree match.
- [ ] After remote verification, remove the temporary local timestamped backup to avoid accumulating local backup files; recoverability remains in verified private Git history.
