# fryeggs Skills

Claude Code Skills 合集，包含 10 个自定义技能，覆盖 GitHub 项目分析、AI 新闻聚合、团队协作、任务分发等场景。

---

## 目录结构

```
skills/
├── github-suite/           # GitHub 项目分析套件（5个skill）
│   ├── github-finder/     # GitHub 项目发现器
│   ├── github-analyzer/   # GitHub 项目深度分析器
│   ├── github-comparator/ # GitHub 项目竞品对比器
│   ├── github-tracker/    # GitHub 项目持续跟踪器
│   └── github-valuator/   # GitHub 项目价值评估器
├── claude-code-dispatch/  # Claude Code 任务分发器（支持Agent Teams）
├── claude-code-hooks/     # Claude Code 任务钩子（支持Telegram回调）
├── reddit-ai-feeds-skill/ # Reddit AI 社区热帖聚合
├── team-tasks/            # 多Agent流水线任务管理器
└── web-content-learner/   # 网页/视频内容提取 + 智能搜索
```

---

## Skill 详细介绍

### 1. github-finder — GitHub 项目发现器

**功能：** 根据需求多源多角度搜索 GitHub 开源项目。

**核心能力：**
- 术语预研：先确认搜索词是否为品牌名/专有名词
- 双语搜索：中文输入 50% 中文 + 50% 英文，英文输入 70% 英文 + 30% 中文
- 多角度搜索：直接工具 / 生态插件 / 基础设施 / 社区推荐 / 替代方案
- 自适应星级阈值：成熟生态 stars>1000，成长生态 stars>200，新兴 stars>50
- 搜索后扩展：README 引用提取 / GitHub Topics 浏览 / 竞品对比

**使用场景：** 找开源项目、技术选型、寻找方案

**触发词：** 找项目、搜索GitHub、开源选型、寻找方案、项目发现

---

### 2. github-analyzer — GitHub 项目深度分析器

**功能：** 基于 D01-D16 评分体系（16维度）对 GitHub 项目进行深度源码分析。

**核心能力：**
- 深度调研模式：16维度全量分析（架构设计/代码质量/安全性/API设计/性能等）
- 快速概览模式：6核心维度扫描，快速了解项目
- 对比分析模式：多项目横向对比（调用 github-comparator）
- 价值评估模式：四维价值深度评估（调用 github-valuator）
- 能力矩阵：聚合为 6-10 个能力域，★1-5 星成熟度评级

**使用场景：** 源码调研、技术选型、投资评估、架构学习

**触发词：** 源码分析、GitHub调研、项目分析、深度分析、16维度、能力矩阵、竞品对比

---

### 3. github-comparator — GitHub 项目竞品对比器

**功能：** 多项目横向对比，生成能力矩阵和差异分析。

**核心能力：**
- 支持 2-5 个项目同时对比
- 标准 6 维度：架构设计 / 代码质量 / 功能完整度 / 生态与社区 / AI/Agent能力 / 安全与合规
- 加权总分计算 + 综合排名
- 场景化推荐：不同场景下的最佳选择

**使用场景：** 竞品对比、项目对比、技术选型对比

**触发词：** 竞品分析、项目对比、横向对比、能力矩阵、技术选型

---

### 4. github-tracker — GitHub 项目持续跟踪器

**功能：** 监控 commit/release/issue/PR 变化，生成日报/周报/月报。

**核心能力：**
- `init`：初始化跟踪，设置基线数据
- `daily`：生成日报，对比基线发现增量变化
- `weekly`：生成周报，统计贡献者活跃度
- `monthly`：生成月报，分析月度趋势和健康度
- `status`：查看所有跟踪项目状态

**使用场景：** 项目动态跟踪、周报生成、月报分析、持续监控

**触发词：** 跟踪项目、项目动态、周报、月报、项目变化、持续监控

---

### 5. github-valuator — GitHub 项目价值评估器

**功能：** 从技术/产品/生态/AI 四维度独立评估项目价值。

**核心能力：**
- 技术价值（25%）：架构/代码质量/安全/API/性能
- 产品价值（25%）：API设计/跨平台/通道架构/文档
- 生态价值（25%）：依赖健康/演进趋势/测试质量/社区
- AI/Agent价值（25%）：AI架构成熟度/Skill生态
- S/A/B/C/D 五级评分体系

**使用场景：** 项目价值评估、投资参考、技术选型

**触发词：** 价值评估、技术评估、项目评分、值不值得用、投资价值

---

### 6. claude-code-dispatch — Claude Code 任务分发器

**功能：** 向 Claude Code 分发开发任务，支持完成后自动回调通知。

**核心能力：**
- Agent Teams 模式：多Agent并行开发（自动生成 Testing Agent）
- 成本控制：--max-budget-usd、--max-turns、模型回退
- Git worktree 隔离：独立分支开发
- 自定义子Agent：通过 --agents JSON 定义专属Agent
- MCP server 集成
- PTY wrapper 避免 exec 环境挂起

**使用场景：** 任务分发、后台执行、多Agent协作

**触发词：** dispatch、run a task、build/develop/create X

---

### 7. claude-code-hooks — Claude Code 任务钩子

**功能：** 基于 Stop/TaskCompleted/SessionEnd 钩子实现 Claude Code 任务完成通知。

**核心能力：**
- 自动 Telegram 群组回调
- 任务元数据记录（task-meta.json）
- 多次触发去重（.hook-lock 30秒窗口）
- 可选 HTTP Hook 支持

**使用场景：** 长时间任务后台执行 + 完成后通知

**触发词：** hook、callback、notify

---

### 8. reddit-ai-feeds-skill — Reddit AI 社区热帖聚合

**功能：** 从 24 个 AI 相关 Reddit 社区抓取最新/热门帖子，附中文摘要。

**覆盖社区：**
- Core LLM：LocalLLaMA、ollama
- Major AI Providers：Anthropic、ClaudeAI、ClaudeCode、OpenAI、ChatGPT、DeepSeek、GeminiAI、google_antigravity、kimi
- AI Coding Tools：cursor、kiroIDE
- OpenClaw Ecosystem：openclaw、clawdbot、moltbot
- Other AI Tools：notebooklm、LangChain、nanobanana
- Research & General：MachineLearning、singularity

**支持排序：** hot / new / top / rising

**使用场景：** AI 新闻追踪、社区氛围了解、技术热点发现

---

### 9. team-tasks — 多Agent流水线任务管理器

**功能：** 通过共享 JSON 任务文件协调多Agent开发流水线。

**核心能力：**
- **Mode A (Linear)：** 固定顺序流水线 `code → test → docs → monitor`
- **Mode B (DAG)：** 任务声明依赖，依赖满足时并行分发
- 任务状态追踪：pending / in-progress / done / failed / skipped
- DAG 可视化 + 循环依赖检测
- 失败隔离：部分失败不影响独立分支

**使用场景：** 多Agent协作开发、顺序/并行工作流、团队任务协调

---

### 10. web-content-learner — 网页/视频内容提取 + 智能搜索

**功能：** 从网页和视频中提取内容并转文字，支持智能搜索。

**核心能力：**
- **网页提取：** Jina AI API → HTML 抓取回退
- **视频转文字：** yt-dlp + Whisper GPU 加速
- **智能搜索：** Brave Search + 页面抓取 + LLM 总结（类似 Tavily）
- **智能分流：** 自动判断输入是搜索/网页/视频任务
- 意图识别：search / question / webpage / video_download / video_transcribe

**使用场景：** 网页内容提取、视频字幕生成、AI搜索问答

---

## 安装方式

将对应 skill 目录复制到 `~/.claude/skills/` 即可：

```bash
cp -r <skill-name> ~/.claude/skills/
```

## 依赖

部分 skill 需要额外工具：

| Skill | 依赖 |
|-------|------|
| web-content-learner | Python 3.10+, Jina API Key, Brave API Key (可选), yt-dlp, Whisper |
| reddit-ai-feeds-skill | Python 3, RSS feed 访问 |
| github-tracker | GitHub CLI (`gh`) |
| github-comparator | GitHub CLI (`gh`) |
| github-valuator | GitHub CLI (`gh`) |

---

## License

MIT
