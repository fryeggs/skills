---
name: github-finder
# version: 2.0
description: |
  GitHub项目发现器 v2.0。根据需求搜索GitHub上的开源项目，
  多源多角度搜索，自适应评估，可调用github-analyzer进行深度调研。
  v2.0: 术语预研、双语搜索、多框架查询、自适应星级、搜索后扩展、
  Topics浏览、社区源、竞品对比、引用图、时间感知、分类法先行。
  Use when 寻找开源项目, 技术选型, 找GitHub项目, 搜索开源方案.
  触发词: 找项目, 搜索GitHub, 开源选型, 寻找方案, 项目发现
allowed-tools: WebSearch, WebFetch, Agent, AskUserQuestion, Skill
---

# /github-finder - GitHub项目发现器 v2.0

根据需求多源多角度搜索GitHub开源项目，自适应评估匹配度，可链式调用github-analyzer深度分析。

v2.0 核心升级：术语预研 → 双语搜索 → 多角度查询 → 自适应阈值 → 搜索后扩展 → 多源验证。

## Instructions

### 工作流程

```
Step 0: 术语预研（P1-1）
├─ 检查用户输入是否包含可能的产品名/专有名词/代号
│   例: "反重力" → 搜索 "反重力 是什么" / "Antigravity Google"
├─ 确认关键词是否为品牌名、产品名、项目代号
│   例: "Antigravity" = Google 内部 OAuth 项目代号
├─ 扩展为精确搜索词（品牌名 + 泛化词并行）
│   例: "Antigravity auth" + "Gemini API proxy"
├─ 方法: WebSearch "[术语] 是什么" / "[术语] what is"
└─ 输出: 关键词清单（精确名 + 泛化词 + 同义词）

Step 1: 需求分析（增强）
├─ 理解用户需求（功能、技术栈、场景）
├─ 双语关键词生成（P1-2）
│   ├─ 检测用户输入语言
│   ├─ 中文输入 → 50% 中文查询 + 50% 英文查询
│   │   例: "gemini 代理" → "gemini 代理" + "gemini proxy"
│   ├─ 英文输入 → 70% 英文 + 30% 中文查询
│   │   例: "gemini proxy" → "gemini proxy" + "gemini 代理 开源"
│   └─ 中文查询额外覆盖: CSDN / 知乎 / V2EX 社区
├─ 多框架角度规划（P1-3）
│   ├─ 角度 1: 直接工具 — "X tool/library"
│   ├─ 角度 2: 生态插件 — "X plugin/extension for [平台]"
│   ├─ 角度 3: 基础设施 — "X gateway/balancer/proxy"
│   ├─ 角度 4: 社区推荐 — "awesome-X" / "best X [年份]"
│   └─ 角度 5: 替代方案 — "alternative to [已知项目]"
│   （每次搜索必须覆盖 ≥3 个角度）
├─ 分类法先行（P3-11，复杂/模糊需求时启用）
│   ├─ 分析需求，生成 3-5 个解决方案子类
│   │   例: "Gemini API 服务化" → {代理网关, 负载均衡, 认证插件, API聚合器, 自托管}
│   ├─ 每个子类独立搜索 1-2 条
│   └─ 触发条件: 需求模糊 OR 首轮结果 <3 个
├─ 自适应星级阈值（P1-4）
│   ├─ 成熟生态 (>3年): stars:>1000
│   ├─ 成长生态 (1-3年): stars:>200
│   ├─ 新兴生态 (<1年): stars:>50
│   ├─ 任何情况: 保留 1-2 个低星高相关项目（标注 🆕）
│   └─ 判断依据: 搜索生态首个 GitHub 项目的创建时间
└─ 确定搜索计划

Step 2: 多源搜索（大幅增强）
├─ GitHub 搜索（≥3 角度，中英双语）
│   ├─ 角度 1: "[关键词] site:github.com"
│   ├─ 角度 2: "[关键词] plugin/extension site:github.com"
│   ├─ 角度 3: "[关键词] gateway/proxy site:github.com"
│   ├─ 角度 4: "awesome-[关键词]" / "best [关键词] [年份]"
│   └─ 中英文各搜索一遍
├─ 社区源搜索（P2-7）
│   ├─ Hacker News: "[关键词] site:news.ycombinator.com"
│   ├─ Reddit: "[关键词] site:reddit.com r/programming OR r/opensource"
│   ├─ V2EX (中文场景): "[关键词] site:v2ex.com"
│   └─ 仅取 1-2 条高赞讨论中提到的项目名，补充搜索
├─ 时间感知（P3-10）
│   ├─ 搜索词默认附加当前年份: "gemini proxy 2026"
│   ├─ 新创建 (<6月) 的项目额外标注 🆕
│   └─ 长期未更新 (>1年) 的项目标注 ⚠️ 维护风险
└─ 收集 8-15 个候选项目

Step 2.5: 搜索扩展（P2-5/6/8/P3-9）
├─ README 引用提取（P2-5）
│   ├─ 读取 TOP 3 项目的 README（WebFetch）
│   ├─ 提取 "See also"、"Alternatives"、"Related projects" 段落
│   ├─ 提取 README 中的 GitHub 链接
│   ├─ 对新发现的项目名做补充搜索
│   └─ 合并到候选列表（标注 📎 来源于引用扩展）
├─ GitHub Topics 浏览（P2-6）
│   ├─ 从已发现项目的 GitHub 页面提取 Topics 标签
│   │   例: gemini-api, google-ai, proxy
│   ├─ WebSearch "site:github.com/topics/[tag]" 浏览同类项目
│   └─ 至少检查 TOP 项目的 2-3 个 Topics
├─ 竞品对比搜索（P2-8）
│   ├─ "[TOP 1 项目] vs" — 找评测文章
│   ├─ "alternative to [TOP 1 项目]" — 找替代方案
│   └─ 仅对 TOP 1 项目执行，避免搜索爆炸
└─ 引用图探索（P3-9，结果不足 5 个时触发）
    ├─ 检查 TOP 1 项目作者的其他仓库
    ├─ 检查 "Used by" / "Dependents" 数量
    └─ 仅在候选不足 5 个时触发

Step 3: 项目筛选（评估矩阵更新）
├─ 使用 WebFetch 获取项目 README
├─ 自适应星级（非固定阈值，按生态年龄调整）
├─ 保留 1-2 个低星高相关项目（标注 🆕）
├─ 新兴项目标注 🆕，长期未更新标注 ⚠️
├─ 多源发现加分（非仅 GitHub 首页搜索发现的项目）
└─ 生成候选列表（TOP 5-8）

Step 4: 快速评估
├─ 对每个候选项目：
│   - 阅读 README 核心内容
│   - 查看项目结构
│   - 评估与需求匹配度
│   - 标注发现渠道（GitHub搜索/社区推荐/README引用/Topics/竞品对比）
└─ 给出推荐排序

Step 5: 深度调研（可选）
├─ 询问用户是否需要深度调研
├─ 如需要，调用 /github-analyzer
│   Skill(skill: "github-analyzer", args: "项目URL 深度调研")
└─ 等待分析结果
```

### 搜索策略

#### 术语预研（Step 0）

在任何搜索开始前，先确认用户输入中的专有名词：

| 信号 | 处理方式 | 示例 |
|------|---------|------|
| 看起来像产品名/代号 | WebSearch "[词] 是什么" | "Antigravity" → Google OAuth 代号 |
| 中英文混合术语 | 分别查中英文含义 | "反重力认证" → Antigravity auth |
| 缩写/首字母 | 展开全称后搜索 | "LLM" → Large Language Model |
| 知名公司+未知词 | 搜索公司+词 | "Google Antigravity" → 具体项目 |

#### 双语搜索策略（P1-2）

| 用户语言 | 中文查询比例 | 英文查询比例 | 额外源 |
|---------|------------|------------|--------|
| 中文输入 | 50% | 50% | CSDN, 知乎, V2EX |
| 英文输入 | 30% | 70% | — |
| 混合输入 | 40% | 60% | 按内容判断 |

#### 多角度搜索矩阵（P1-3）

每次搜索必须覆盖 **≥3 个角度**：

| 角度 | 搜索模式 | 示例 |
|------|---------|------|
| 直接工具 | `X tool/library site:github.com` | `gemini api client site:github.com` |
| 生态插件 | `X plugin/extension for [平台]` | `gemini extension for langchain` |
| 基础设施 | `X gateway/balancer/proxy` | `gemini api gateway proxy` |
| 社区推荐 | `awesome-X` / `best X [年份]` | `awesome-gemini` / `best gemini tools 2026` |
| 替代方案 | `alternative to [已发现项目]` | `alternative to one-api` |

#### 自适应星级阈值（P1-4）

**删除固定 `stars:>1000` 过滤**，改为动态阈值：

| 生态年龄 | 星级阈值 | 判断依据 |
|---------|---------|---------|
| 成熟 (>3年) | stars:>1000 | 首个相关项目创建于 3 年前 |
| 成长 (1-3年) | stars:>200 | 首个相关项目创建于 1-3 年前 |
| 新兴 (<1年) | stars:>50 | 首个相关项目创建于 1 年内 |
| 任何情况 | 无下限 | 保留 1-2 个低星但高相关项目（🆕） |

#### 社区源搜索（P2-7）

| 源 | 搜索模式 | 目的 |
|----|---------|------|
| Hacker News | `[关键词] site:news.ycombinator.com` | 技术社区口碑 |
| Reddit | `[关键词] site:reddit.com r/programming OR r/opensource` | 开发者讨论 |
| V2EX | `[关键词] site:v2ex.com` | 中文技术社区 |
| 知乎 | `[关键词] site:zhihu.com` | 中文深度讨论 |

仅取 1-2 条高赞讨论中提到的项目名做补充搜索，不需要全面抓取。

#### 时间感知（P3-10）

- 搜索词默认附加当前年份（如 "gemini proxy 2026"）
- 标注规则：
  - 🆕 新创建 (<6个月) 的项目
  - ⚠️ 长期未更新 (>1年) 的项目

### 搜索扩展策略（Step 2.5）

#### README 引用提取（P2-5）

对 TOP 3 项目的 README 执行以下提取：

```
提取目标:
├─ "See also" / "Related" / "Similar" / "Alternatives" 段落
├─ "Comparison" / "vs" 表格
├─ README 正文中的 github.com 链接
└─ "Inspired by" / "Based on" 引用
```

新发现的项目标注 📎 表示来源于引用扩展。

#### GitHub Topics 浏览（P2-6）

```
执行步骤:
├─ 从 TOP 项目的 GitHub 页面提取 Topics 标签
│   方法: WebFetch 项目页面，查找 topic 标签
├─ 对 2-3 个高相关 Topics 做搜索
│   方法: WebSearch "site:github.com/topics/[tag]"
└─ 将新发现的项目加入候选列表
```

#### 竞品对比搜索（P2-8）

仅对 TOP 1 项目执行：

```
搜索模式:
├─ "[项目名] vs" — 找评测/对比文章
├─ "alternative to [项目名]" — 找替代方案列表
└─ "[项目名] comparison" — 找对比表
```

#### 引用图探索（P3-9）

仅在候选结果不足 5 个时触发：

```
探索路径:
├─ TOP 1 项目作者的 GitHub 主页 → 查看其他仓库
├─ TOP 1 项目的 "Used by" 依赖者
└─ TOP 1 项目的 Contributors 列表 → 查看贡献者其他项目
```

### 评估矩阵

```
项目评估矩阵 v2.0：
┌────────────┬────────┬────────────────────────────────────┐
│ 指标       │ 权重   │ 标准                                │
├────────────┼────────┼────────────────────────────────────┤
│ 功能匹配   │ 30%    │ 核心功能符合需求（v2.0 权重提升）     │
│ Stars      │ 15%    │ 自适应阈值，非绝对值（v2.0 权重降低） │
│ 活跃度     │ 20%    │ 3月内有提交                         │
│ 文档质量   │ 15%    │ README完整、有示例                   │
│ 社区生态   │ 10%    │ Issues活跃、有贡献者                 │
│ 发现渠道   │ 10%    │ 多源发现加分（v2.0 新增）             │
└────────────┴────────┴────────────────────────────────────┘

发现渠道加分规则:
├─ 仅 GitHub 搜索首页发现 → 0 分
├─ 社区讨论(HN/Reddit/V2EX)提及 → +3 分
├─ README 引用/See also 提及 → +3 分
├─ GitHub Topics 浏览发现 → +2 分
└─ 竞品对比搜索发现 → +2 分
（满分 10 分）
```

### 输出格式

```markdown
## 🔍 GitHub项目发现报告 v2.0

### 搜索需求
[用户原始需求描述]

### 术语预研（Step 0）
- 识别术语: [术语] → [实际含义]
- 关键词清单: [精确名, 泛化词, 同义词]

### 搜索策略
- 双语关键词: [中文词] / [英文词]
- 搜索角度: [角度1, 角度2, 角度3, ...]
- 星级阈值: [自适应阈值] (生态年龄: [X年])
- 搜索轮次: 首轮搜索 + 扩展搜索

### 候选项目列表

#### 1️⃣ [项目名称](项目URL) ⭐ Stars数 [标注]
- **定位**: 一句话描述
- **技术栈**: Go / Python / ...
- **最近更新**: YYYY-MM-DD
- **匹配度**: ★★★★☆ (4/5)
- **发现渠道**: GitHub搜索 / 社区推荐📢 / README引用📎 / Topics / 竞品对比
- **推荐理由**: [为什么推荐]
- **潜在问题**: [可能的局限]

#### 2️⃣ ... 🆕 (新兴项目)

#### 3️⃣ ... ⚠️ (维护风险)

### 搜索扩展发现
- 📎 通过 README 引用发现: [项目列表]
- 🏷️ 通过 Topics 浏览发现: [项目列表]
- 🆚 通过竞品对比发现: [项目列表]
- 📢 通过社区讨论发现: [项目列表]

### 推荐结论
基于需求分析，推荐 **[项目名]**，理由：...

### 搜索覆盖度自检
- [x] 术语预研完成
- [x] 中英双语搜索
- [x] ≥3 个搜索角度
- [x] 社区源补充
- [x] README 引用扩展
- [x] Topics 浏览
- [ ] 竞品对比（TOP 1 项目）
- [ ] 引用图探索（仅结果不足时）

### 下一步
- [ ] 是否需要对推荐项目进行深度调研？
```

## Examples

### 基础搜索
```
用户: /github-finder 我需要一个Go语言的CLI框架
流程:
1. Step 0: "CLI framework" 非专有名词，跳过术语预研
2. Step 1: 双语 "Go CLI框架"/"golang cli framework", 成熟生态 stars:>1000
3. Step 2: 搜索 3 角度 (直接工具/社区推荐/替代方案)
4. Step 2.5: cobra 的 README → 发现 urfave/cli, kong
5. 输出: cobra, urfave/cli, kong, charmbracelet/bubbletea 等对比
```

### 技术选型（双语搜索生效）
```
用户: /github-finder 找一个替代Notion的开源笔记软件
流程:
1. Step 0: "Notion" 是产品名，确认为笔记/协作工具
2. Step 1: 双语 "开源笔记 替代Notion"/"notion alternative open source"
3. Step 2: 搜索角度(直接工具/基础设施/社区推荐), HN/Reddit
4. Step 2.5: Obsidian README → 发现 Logseq, Joplin, AppFlowy
5. 输出: 完整对比，含多源发现标注
```

### 新兴生态（自适应星级生效）
```
用户: /github-finder 基于 Google Antigravity/Gemini API 的开源项目
流程:
1. Step 0: "Antigravity" → WebSearch → 发现是 Google 内部 OAuth 项目代号
   关键词清单: ["antigravity auth", "gemini api proxy", "gemini 代理", "google ai gateway"]
2. Step 1: 成长生态(1-3年) → 阈值 stars:>200, 保留低星高相关
   双语: "gemini api 代理 开源"/"gemini api proxy open source"
3. Step 2: 3+ 角度搜索, 时间感知附加 "2026", 社区源(V2EX/Reddit)
4. Step 2.5: TOP 项目 README 引用扩展 → 发现更多同类; 引用图探索(候选不足时)
5. 输出:
   - one-api ⭐ 20k+ (API聚合网关)
   - opencode-antigravity-auth ⭐ 8.9k (术语预研发现)
   - Gemini-Balance ⭐ 5.8k 📢 (双语/社区源发现)
   - OpenGem ⭐ 23 🆕 (低星高相关保留)
```

### 完整流程（发现+分析）
```
用户: /github-finder 找一个AI代码编辑器，找到后深度分析
流程:
1. Step 0: "AI代码编辑器" 非专有名词，跳过
2. Step 1-2: 多角度搜索 cursor, continue, aider, opencode 等
3. Step 2.5: README引用 + Topics(ai-coding, code-editor) + 竞品对比("aider vs")
4. Step 3-4: 快速评估，推荐 opencode
5. Step 5: 调用 /github-analyzer 对 opencode 深度调研
6. 输出: 完整的项目发现+深度分析报告
```

### 分类法先行（复杂需求）
```
用户: /github-finder 我想把各种AI API统一管理起来
流程:
1. Step 0: 术语检查 — 无专有名词
2. Step 1: 需求模糊 → 启用分类法先行
   子类: {API网关/聚合器, 负载均衡/路由, 密钥管理, 用量监控, SDK封装}
   每个子类独立搜索
3. Step 2: 5 子类 × 2 查询 = 10 条搜索
4. Step 2.5: 扩展发现
5. 输出: 按子类分组的项目推荐
```

## Quick Reference

| 参数 | 说明 |
|------|------|
| 搜索角度 | ≥3 个 (直接工具/生态插件/基础设施/社区推荐/替代方案) |
| 双语比例 | 中文输入 50:50, 英文输入 30:70, 混合 40:60 |
| 星级阈值 | 成熟 >1000, 成长 >200, 新兴 >50, 低星高相关保留 |
| 候选数量 | 首轮 8-15 个 → 筛选至 TOP 5-8 |
| 标注符号 | 🆕 新创建(<6月), ⚠️ 未更新(>1年), 📎 引用扩展, 📢 社区发现 |
| 深度调研 | 可选，调用 `/github-analyzer` |

## Related Skills

- **github-analyzer**: 深度源码分析器，本 SKILL 的下游。发现项目后可链式调用 analyzer 进行 6 维度深度调研
- **smart-router** (可选): 如已安装，可通过路由器自动触发本 SKILL
