## Why

当前 `chatgpt-web` 能把研究任务发送到 ChatGPT 网页端，但会将完整长答案重新打印回 Codex 上下文，抵消了节省 token 的主要收益；同时网页自动化窗口的出现会干扰用户桌面操作。现在需要把它升级为低回传、会话可控、窗口影响最小且可验证的研究桥接 skill。

## What Changes

- 默认将网页端长调研结果压缩为结构化 `capsule` 返回给 Codex，并保留会话链接；只有用户明确要求时才返回全文。
- 提供 `receipt`、`capsule`、`full` 三种回传模式，设置硬长度限制与失败时禁止全文回退的规则。
- 默认续接最近一次已保存且可访问的网页会话；仅在用户明确要求时新建网页会话；保留历史列表与选择能力。
- 加入单任务锁与最小统计记录，不实现默认任务排队或挂起机制。
- 使用已有认证状态的正常 Chrome/OpenCLI 会话，按需创建本次专属 automation window；在唯一识别成功后最小化，并在任务结束后仅关闭本次窗口。
- 增加脚本级测试与 skill 验证，确保不记录 Cookie/API Key/完整网页答案，不盲目操作用户其他 Chrome 窗口。

## Capabilities

### New Capabilities

- `low-token-research-return`: 网页端研究任务的 `receipt`/`capsule`/`full` 回传模式、结构化提取、长度控制与统计边界。
- `chatgpt-conversation-routing`: 最近会话续聊、显式新建、历史列出/选择及失效会话保护行为。
- `nonintrusive-browser-lifecycle`: 正常认证 Chrome automation window 的按需创建、唯一识别、最小化、清理与单任务锁。

### Modified Capabilities

- 无；当前项目尚无已登记的 OpenSpec capability。

## Impact

- 受影响代码：`chatgpt-web/scripts/chatgpt_web.py`、`chatgpt-web/SKILL.md`、`chatgpt-web/agents/openai.yaml`，以及新增测试文件。
- 受影响系统：本机 OpenCLI daemon/Chrome 扩展、已登录的 `chatgpt.com` 网页会话、本地 `~/.agents/state/` 状态记录。
- 不引入 API Key 管理、无痕浏览器 Profile、常驻后台网页窗口、默认任务队列或 MCP 封装。
- 编码实施由用户指定的 OpenCode/MiMo 完成；Codex 负责规格、监督、审查与最终真实验证，GSD 负责里程碑与 Git 隔离。
