---
name: opencli
description: "Universal CLI for websites and browser automation."
---

# OpenCLI Skill

Universal CLI that transforms websites into command-line interfaces. 87+ built-in adapters + browser automation.

## 触发条件（满足任一即可）

- 用户提供 URL/网站地址
- 用户要"控制"、"操作"、"自动化"某个网站
- 用户要"提取"网页数据
- 用户提到：Twitter, Reddit, Bilibili, HackerNews, 小红书, Zhihu, Amazon
- 用户说：浏览网页、点击按钮、填表单、截屏
- 用户说：帮我看看这个网站、这个页面内容
- 用户粘贴网址链接

## 快速使用

```bash
# 内置网站命令
opencli hackernews top --limit 5
opencli bilibili hot --limit 5
opencli twitter search "AI news"
opencli reddit hot --limit 10
opencli zhihu hot
opencli amazon search "laptop"

# 浏览器自动化
opencli browser open <url>
opencli browser click "#btn"
opencli browser type "#input" "text"
opencli browser get "h1"
opencli browser screenshot

# 探索新网站
opencli explore <url>    # 发现网站能力
opencli generate <url>    # 生成 CLI adapter
```

## 内置网站 (87+)

| 网站 | 命令前缀 |
|------|----------|
| HackerNews | `opencli hackernews` |
| Reddit | `opencli reddit` |
| Bilibili | `opencli bilibili` |
| Twitter/X | `opencli twitter` |
| 小红书 | `opencli xiaohongshu` |
| Zhihu | `opencli zhihu` |
| Amazon | `opencli amazon` |
| 1688 | `opencli 1688` |
| Gemini | `opencli gemini` |

## 示例触发话术

| 用户可能说的话 | 解析 |
|--------------|------|
| "帮我看看 https://github.com" | 触发 opencli |
| "提取这个页面的内容" | 触发 opencli |
| "帮我登录 Twitter 发个推" | 触发 opencli |
| "Bilibili 热门视频有哪些" | 触发 opencli |
| "控制这个网站，点一下登录按钮" | 触发 opencli |
| "打开 youtube.com" | 触发 opencli |
| "抓取这个网页的数据" | 触发 opencli |

## 环境要求

- Node.js >= 21.0.0 或 Bun >= 1.0
- Chrome/Chromium + OpenCLI 扩展

## 何时不用

- 桌面软件 → 用 `cli-anything`
- GitHub 搜索 → 用 `github-suite`
- 视频转写 → 用 `web-content-learner`
