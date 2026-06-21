# fryeggs Skills

MacBook 自定义 Agent Skills 主仓库。Codex 是共享技能的主来源，Claude 与 Agents 通过软链接复用，避免维护重复副本。

## 当前技能

| Skill | 作用 | 典型场景 |
|---|---|---|
| `repo-mastery` | 目标功能驱动，边学仓库边实现功能 | “学习这个项目并增加 X 功能” |
| `github-suite` | 搜索、分析、比较、跟踪、评估 GitHub 项目 | 开源选型、项目调研 |
| `reddit-ai-feeds-skill` | 聚合 Reddit AI 社区动态并生成中文摘要 | AI 新闻和趋势 |
| `web-content-learner` | 下载媒体、提取字幕、Whisper 转写 | 视频/音频内容学习 |
| `claude-code-dispatch` | 向 Claude Code 分发任务 | Claude-only 后台执行 |
| `claude-code-hooks` | Claude Code 完成通知 | Claude-only 回调 |

`github-suite` 包含 `github-finder`、`github-analyzer`、`github-comparator`、`github-tracker` 和 `github-valuator`。

## Repo Mastery

默认采用 **目标功能驱动、边学边做**。用户提供仓库链接或描述需要寻找的项目，再说明目标功能即可：

```text
帮我学习 https://github.com/example/project，并增加离线同步功能。
```

流程会聚焦目标功能所需的架构、领域知识、调用链、测试和扩展点；复杂改动使用规格与隔离 worktree，完成后必须给出验证证据。

## 安装模型

维护源码后，将共享技能安装到 `~/.codex/skills/<name>`：

```bash
ln -s /Users/qingshan/.codex/skills/<name> /Users/qingshan/.claude/skills/<name>
ln -s /Users/qingshan/.codex/skills/<name> /Users/qingshan/.agents/skills/<name>
```

不要建立 `~/.ai-tools`，也不要在 Claude 侧保存共享技能实体副本。Claude-only 技能可以保留在 Claude/Agents 目录。

## 工具边界

- 重复桌面流程优先使用 Record and Replay 录制为专用 skill。
- 稳定浏览器 DOM 自动化保留 Browser/Chrome + `node_repl`。
- 不支持的视觉桌面操作使用 Computer Use。
- `claude-hud` 是启用中的 Claude-only 状态栏插件，不属于本仓库技能。
- 普通网页研究使用现有浏览器/网页工具；`web-content-learner` 仅处理媒体下载、字幕和转写。

## 验证

```bash
python3 -m unittest discover -s tests -v
python3 /Users/qingshan/.codex/skills/.system/skill-creator/scripts/quick_validate.py repo-mastery
```

## License

MIT
