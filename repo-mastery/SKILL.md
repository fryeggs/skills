---
name: repo-mastery
description: Use when a user wants to find, evaluate, learn, explain, onboard to, modify, or extend a GitHub repository or local codebase, especially when the goal is to understand enough architecture and domain context to implement a requested feature safely.
---

# Repo Mastery

Default to **target-feature-driven** learning: teach the smallest useful portion of the repository while delivering the requested feature. Do not force a full-project course before useful work begins.

## Core Workflow

1. Resolve the supplied repository or use GitHub tools to find candidates. Confirm the selected repository with evidence.
2. Check license, maintenance activity, security-sensitive setup, repository instructions, and local Git state before changing files.
3. Map the requested feature to entry points, modules, data flow, tests, and dependencies. Prefer Codegraph for indexed code and direct source inspection for gaps.
4. Explain only the prerequisite architecture and domain concepts needed for the requested feature. Give executable micro-exercises when they reduce uncertainty.
5. Define scope, files, interfaces, risks, tests, and acceptance commands before implementation. Use OpenSpec/GSD only for genuinely complex work.
6. Implement with existing project patterns. For complex changes, use an isolated worktree and preserve unrelated user changes.
7. Verify static checks, tests, builds, and the relevant runtime surface. Never claim completion without verification evidence.
8. Teach back the final diff: why it works, what changed architecturally, known trade-offs, and the next useful learning step.

Read [references/stages.md](references/stages.md) only when the task needs detailed stage selection, onboarding, domain mapping, diff analysis, or a learning curriculum.

## Boundaries

- Ask before destructive actions, publishing, account changes, or system/network changes.
- Never expose credentials, cookies, tokens, passwords, or private keys.
- State uncertainty and verify it; do not invent repository facts.
- Do not generate a full knowledge graph or dashboard unless it directly helps the requested outcome.
- Stop after analysis when the user asks only to learn, review, compare, or plan.

## Completion Contract

Return the selected repository/commit, focused learning map, implemented scope, verification evidence, remaining risks, and recovery path. If any required check cannot run, label it unverified.
