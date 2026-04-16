---
name: github-tracker
description: "GitHub 项目持续跟踪器。监控 commit/release/issue 变化，生成日报/周报/月报增量分析。Use when 跟踪项目, 项目动态, 周报, 月报, 项目变化, 持续监控."
version: 1.0.0
author: kingking
allowed-tools:
  - Bash(gh *)
  - Read
  - Write
  - Edit
  - Grep
  - Glob
triggers:
  - 跟踪项目
  - 项目动态
  - 周报
  - 月报
  - 项目变化
  - 持续监控
  - github-tracker
---

# GitHub Tracker SKILL v1.0.0

> 持续跟踪 GitHub 项目的增量分析工具。监控 commit/release/issue/PR 变化，生成日报/周报/月报。

## Instructions

### 命令

```
/github-tracker init <repo-url>   → 初始化跟踪，设置基线
/github-tracker daily             → 生成日报（今日 commit + 关键变化）
/github-tracker weekly            → 生成周报（本周统计 + 贡献者活跃度）
/github-tracker monthly           → 生成月报（月度趋势 + 健康度评估）
/github-tracker status            → 查看所有跟踪项目状态
```

## 数据存储

```
~/.claude/skill-registry/github-tracker/
└── <owner>-<repo>/
    ├── baseline.json        # 基线数据
    ├── config.json          # 跟踪配置
    └── history/             # 历史报告
        ├── daily/
        ├── weekly/
        └── monthly/
```

## 工作流

### Phase 1: 命令解析

解析用户输入，识别命令和参数：
- `init` — 需要 repo URL 或 owner/repo
- `daily/weekly/monthly` — 可选指定 repo（默认全部跟踪项目）
- `status` — 无参数

### Phase 2: 执行

根据命令分发到对应处理流程。

---

## INIT — 初始化跟踪

### 输入
- `<repo-url>` 或 `<owner/repo>` 格式

### 步骤

1. **验证仓库**: `gh repo view <owner/repo> --json name,owner,description,stargazerCount,forkCount,issues,pullRequests`
2. **采集基线数据**:
   ```bash
   # 最新 commit
   gh api repos/<owner>/<repo>/commits?per_page=1
   # stars/forks/issues/PRs 计数
   gh repo view <owner/repo> --json stargazerCount,forkCount,issues,pullRequests
   # 最新 release
   gh release list -R <owner/repo> --limit 1
   # 贡献者数
   gh api repos/<owner>/<repo>/contributors?per_page=1 -i | grep -i 'link:' 
   # open issues 数
   gh issue list -R <owner/repo> --state open --limit 1 --json number | jq length
   # open PRs 数
   gh pr list -R <owner/repo> --state open --limit 1 --json number | jq length
   ```
3. **写入 baseline.json**:
   ```json
   {
     "repo": "<owner>/<repo>",
     "initialized_at": "ISO-8601",
     "latest_commit_sha": "abc123",
     "latest_commit_date": "ISO-8601",
     "latest_release": "v1.0.0",
     "stars": 1234,
     "forks": 56,
     "open_issues": 78,
     "open_prs": 12,
     "contributors": 45,
     "description": "..."
   }
   ```
4. **创建目录结构**: `history/daily/`, `history/weekly/`, `history/monthly/`
5. **输出确认**: 显示基线摘要

---

## DAILY — 日报生成

### 触发条件
有新 commit（对比 baseline 中的 `latest_commit_sha`）。无新 commit 则输出"今日无变更"。

### 步骤

1. **读取基线**: 加载 `baseline.json`
2. **采集增量数据**:
   ```bash
   # 自上次 commit 以来的新 commit
   gh api repos/<owner>/<repo>/commits?since=<last_date>&per_page=100
   # 当前 stars/forks/issues/PRs
   gh repo view <owner/repo> --json stargazerCount,forkCount
   gh issue list -R <owner/repo> --state open --json number
   gh pr list -R <owner/repo> --state open --json number
   # 今日新 release
   gh release list -R <owner/repo> --limit 5
   ```
3. **生成日报** (`history/daily/YYYY-MM-DD.md`):
   ```markdown
   # <repo> 增量日报 — YYYY-MM-DD
   ## 提交范围
   From: <old_sha> → To: <new_sha> (N commits)
   ## Commit 摘要
   | SHA | Author | Message |
   |-----|--------|---------|
   ## 关键指标变化
   | 指标 | 昨日 | 今日 | 变化 |
   |------|------|------|------|
   | Stars | ... | ... | +N |
   | Open Issues | ... | ... | +/-N |
   | Open PRs | ... | ... | +/-N |
   ## 新 Release
   (如有)
   ## 建议关注
   - 变化较大的指标提醒
   ```
4. **更新基线**: 更新 `latest_commit_sha`、`latest_commit_date` 和指标数值

---

## WEEKLY — 周报生成

### 数据来源
汇总本周日报 + 补充采集周度数据。

### 步骤

1. **收集本周日报**: 读取 `history/daily/` 中本周文件
2. **采集周度数据**:
   ```bash
   # 本周 commit 统计（按作者分组）
   gh api repos/<owner>/<repo>/commits?since=<week_start>&until=<week_end>&per_page=100
   # 本周新开/关闭的 issue
   gh issue list -R <owner/repo> --state all --json number,createdAt,closedAt,title
   # 本周新开/合并的 PR
   gh pr list -R <owner/repo> --state all --json number,createdAt,mergedAt,title,author
   # 贡献者活跃度
   gh api repos/<owner>/<repo>/stats/contributors
   ```
3. **生成周报** (`history/weekly/YYYY-WNN.md`):
   ```markdown
   # <repo> 周报 — YYYY 第 NN 周
   ## 周期: MM-DD ~ MM-DD
   ## 概览
   - 总 commit 数: N
   - 活跃贡献者: N
   - 新 issue: N / 关闭 issue: N
   - 新 PR: N / 合并 PR: N
   ## Commit 统计（按作者）
   | Author | Commits | 主要变更 |
   |--------|---------|----------|
   ## 指标周度变化
   | 指标 | 周初 | 周末 | 变化 |
   |------|------|------|------|
   ## 重要 Issue/PR
   (列出本周关键 issue 和 PR)
   ## 贡献者活跃度
   | 贡献者 | 本周 Commits | 趋势 |
   |--------|-------------|------|
   ## 下周关注建议
   - 未关闭的重要 issue
   - 待合并的 PR
   ```

---

## MONTHLY — 月报生成

### 数据来源
汇总本月周报 + 月度趋势分析。

### 步骤

1. **收集本月周报**: 读取 `history/weekly/` 中本月文件
2. **采集月度数据**:
   ```bash
   # 月度 commit 总量
   gh api repos/<owner>/<repo>/commits?since=<month_start>&until=<month_end>&per_page=100
   # Release 列表
   gh release list -R <owner/repo> --limit 10
   # 月度贡献者统计
   gh api repos/<owner>/<repo>/stats/contributors
   ```
3. **生成月报** (`history/monthly/YYYY-MM.md`):
   ```markdown
   # <repo> 月报 — YYYY-MM
   ## 月度概览
   - 总 commit: N | 活跃贡献者: N
   - 新 issue: N / 关闭: N | 新 PR: N / 合并: N
   - 新 release: N
   ## 指标月度变化
   | 指标 | 月初 | 月末 | 变化 | 趋势 |
   |------|------|------|------|------|
   ## 里程碑
   - 本月 release 列表及关键变更
   ## 健康度评估
   | 维度 | 评分 | 说明 |
   |------|------|------|
   | 开发活跃度 | A/B/C | commit 频率 + 贡献者数 |
   | Issue 响应 | A/B/C | 平均关闭时间 + 积压量 |
   | PR 合并效率 | A/B/C | 平均合并时间 + 积压量 |
   | Release 节奏 | A/B/C | 发布频率 + 版本规范 |
   | 社区参与 | A/B/C | 新贡献者 + star 增长 |
   ## 趋势分析
   - 与上月对比的关键变化
   - 需关注的风险信号
   ## 下月建议
   ```

---

## STATUS — 查看跟踪状态

### 步骤

1. **扫描注册目录**: `~/.claude/skill-registry/github-tracker/`
2. **读取每个项目的 baseline.json**
3. **输出汇总表**:
   ```markdown
   # GitHub Tracker 状态
   | 项目 | Stars | 上次更新 | 日报数 | 周报数 | 月报数 |
   |------|-------|----------|--------|--------|--------|
   ```

---

## 评分标准

健康度评分基于以下阈值：

| 等级 | 标准 |
|------|------|
| A | 指标优秀（活跃度高、响应快、节奏稳定） |
| B | 指标正常（有一定活跃度，偶有延迟） |
| C | 指标偏低（活跃度不足、积压较多） |

## 注意事项

- 所有 `gh` 命令需要 GitHub CLI 已认证
- 大型仓库的 API 调用可能触发 rate limit，注意分页
- 日报在无新 commit 时跳过生成
- 基线数据在每次日报后自动更新
- 报告使用 Markdown 格式，可直接在 Obsidian 中查看
