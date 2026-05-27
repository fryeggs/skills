---
name: gsd-2
description: "GSD (Get Shit Done) v2 — Autonomous agent execution with crash recovery, git isolation, and milestone tracking. Use for long-running dev tasks, multi-step features, or hands-off implementation."
---

# GSD 2 — Get Shit Done

Autonomous development agent framework built on Pi SDK with direct Claude Code harness control.

## 触发条件

- 用户说"自动执行"、"自主开发"
- 用户说"帮我实现这个功能"（复杂多步骤任务）
- 用户说"跑一下这个任务"
- 用户说"长时间开发任务"
- 用户想"离开，让 AI 自己干"

## Quick Start

```bash
gsd auto              # Start autonomous mode
gsd                   # Interactive session
gsd continue          # Resume interrupted session
```

## Key Features

| Feature | Description |
|---------|-------------|
| Fresh context per task | 200k tokens, no garbage |
| Git isolation | Worktree/branch per milestone |
| Crash recovery | Lock files + session forensics |
| Cost tracking | Real-time token/cost ledger |
| Stuck detection | Retry once, then stop |

## Architecture

```
Milestone → Slice → Task
           ↓
    Plan → Execute → Complete → Reassess → Validate
```

## Commands

| 命令 | 说明 |
|------|------|
| `/gsd auto` | 自主执行模式 |
| `/gsd auto --context <file>` | 带上下文文件自动执行 |
| `/gsd` | 交互式会话 |
| `/gsd continue` | 恢复中断的会话 |
| `/gsd sessions` | 列出所有会话 |

## With OpenSpec

GSD 2 + OpenSpec 工作流：
1. `openspec init --tools claude` — 项目初始化
2. `/opsx:propose "feature"` — 创建规格文档
3. `/opsx:apply` — 生成任务列表
4. `/gsd auto` — 执行实现

## 环境要求

- Node.js 20+
- Claude Code 或兼容的 AI 编码助手
