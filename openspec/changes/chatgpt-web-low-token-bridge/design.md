## Context

`chatgpt-web` 当前通过 Python helper 调用 OpenCLI 的真实 Chrome 桥接，将提示词发送到已登录的 `chatgpt.com`，等待响应后打印完整网页答案。该方式已经能够复用网页端额度与历史会话，但完整回传长答案会重新占用 Codex 上下文；打开 automation window 也可能打断用户正在进行的桌面操作。

用户要求 Codex 继续作为主控：网页端仅承担长调研；本机执行、代码变更、审核与验证由 Codex 负责。网页端必须继续最近会话，除非用户明确要求新建；窗口必须使用正常已登录 Chrome 会话，按需创建、尽可能最小化并完成后清理，不得常驻。实现阶段由 OpenCode/MiMo 修改代码，Codex 按此设计审核。

## Goals / Non-Goals

**Goals:**

- 让网页端的长答案默认不进入 Codex 上下文，仅回传受限的结构化精华与网页会话 URL。
- 将会话路由、失败保护、单任务互斥、轻量指标记录实现为确定性脚本逻辑。
- 在发送用户任务前只操作本次唯一识别出的 Chrome automation window，并将其最小化；任务结束无论成功失败都清理本次窗口。
- 通过单元测试、静态校验和一次用户知情的真实窗口测试验证行为。

**Non-Goals:**

- 不实现 MCP server、后台常驻 Chrome、任务队列、挂起恢复或定时重试任务系统。
- 不使用无痕窗口、独立临时 Profile、headless 浏览器、Cookie/API Key 导出或直接调用 ChatGPT 私有接口。
- 不保证在未做真实窗口验收前完全无视觉闪现。
- 不自动向 GitHub 推送或部署到活跃 skill 路径。

## Decisions

### 1. 保留 skill + Python helper + OpenCLI 架构

继续扩展既有 `scripts/chatgpt_web.py`，不先引入 MCP。Python 负责状态、协议、截断、锁与指标；OpenCLI 仅负责真实登录网页的导航和 DOM 交互。

**理由：** token 成本由回传内容决定，而非接口外壳；沿用已验证链路的变更面更小。

**替代方案：** MCP 可在协议稳定后封装；API 可实现完全后台，但会改用另一套额度；ChatGPT Desktop adapter 会主动激活窗口，干扰更强。

### 2. 三种回传模式，默认 `capsule`

命令新增稳定参数，例如 `--return-mode {receipt,capsule,full}` 和 `--max-chars`。`ask` 与 `delegate` 默认均为 `capsule`；`full` 仅在显式参数下使用。

- `receipt`: 等待网页任务结束并只打印状态、话题标题和 URL。
- `capsule`: 在提示词尾追加结构化输出协议，读取网页答案后只打印提取并截断后的 JSON。
- `full`: 保持兼容能力，打印完整网页答案。

网页端在 `capsule` 模式必须在答案末尾输出：

```text
<codex_capsule>
{"conclusion":"...","evidence":[{"claim":"...","source":"..."}],"uncertainties":["..."],"actions_for_codex":["..."]}
</codex_capsule>
```

解析失败时输出失败状态与网页 URL，不打印原始答案。`max_chars` 作用于最终打印内容，默认 `2000` 个字符。

### 3. 会话路由继续以本地状态为主

沿用 `~/.agents/state/chatgpt-web.json` 中的最近话题与已保存列表：

- 未传入 `--new` 与特定 `--topic` 时续接 `last_topic_id`。
- `--new` 是创建网页会话的唯一脚本入口，skill 仅在用户明确要求新话题时使用它。
- `list` 仅读本地状态，不打开浏览器；`discover` 才刷新网页侧边栏。
- 续接已保存 URL 时，在发送前校验加载后的 conversation ID；不匹配则中止。

### 4. 使用原子单任务锁，不做队列

在 `~/.agents/state/chatgpt-web.lock` 用独占创建实现互斥，内容只包含运行 ID、PID、开始时间和命令类别。获得锁失败立即返回“已有网页任务运行”状态，由 Codex决定稍后顺序发起；不存储排队任务或提示词正文。

**理由：** 避免两个调用共用同一 automation window/会话并降低过期任务与意外额度消耗。

### 5. 仅对唯一识别的本次 Chrome 窗口最小化和清理

实现 macOS 专用窗口生命周期层，并保留非 macOS 的明确降级错误/现有行为选择：

1. 为每次运行生成随机 `run_id` 与唯一 marker URL/title。
2. 通过普通 Chrome 已登录 Profile 建立本次 OpenCLI automation window；窗口不得为无痕或临时 Profile。
3. 在发送 ChatGPT 提示词前，以 marker 或 OpenCLI 返回 target 结合 Chrome 窗口 tab URL，确认只命中一个本次 owned window。
4. 仅对该唯一窗口执行最小化；若无法唯一确认或最小化失败，中止发送并清理可确认归属的本次资源，不操作其他窗口。
5. 使用同一 owned target 导航至选定 ChatGPT 会话并完成交互。
6. `finally` 中关闭 OpenCLI automation window；不得退出整个 Chrome 应用，也不得关闭无法确认归属的窗口。

实现前必须先研究 OpenCLI 返回 target 与 Chrome AppleScript 可见 URL/窗口的对应关系；不允许用“当前最前窗口”作为归属依据。

### 6. 只记录非敏感指标

指标文件使用 `~/.agents/state/chatgpt-web-metrics.jsonl`，每次完成可记录：

- 时间、运行 ID、回传模式、是否成功。
- 网页响应字符数、实际打印字符数、近似避免进入上下文的字符数/估算 token 数。
- 是否最小化成功、是否完成清理。

不得记录提示词正文、网页回答正文、Cookie、认证 header 或 API Key。指标 token 数明确标为估算，不宣称计费证据。

### 7. 在 Git 基线中实施，部署前保持活跃 skill 不变

当前活跃目录 `/Users/qingshan/.agents/skills/chatgpt-web` 不属于 Git 仓库，且 `fryeggs/skills` 远端尚无此 skill。因此已将其原样导入本地 `fryeggs/skills` 克隆的基线分支，后续在 GSD 隔离工作树开发。Codex 验收完成前，不覆盖活跃目录、不推送远端。

## Risks / Trade-offs

- [Risk] OpenCLI/Chrome 窗口与 target 的对应方式不足以安全识别 owned window。 -> [Mitigation] 将唯一识别和最小化作为先行技术验收；不能证明唯一性则不发送提示、不部署该窗口功能。
- [Risk] automation window 仍可能在最小化前短暂可见。 -> [Mitigation] 默认不聚焦、尽早最小化，并在用户知情的短任务中记录真实体验；无法接受时重新评估 API 路线。
- [Risk] 网页 UI 变化导致 capsule 或 composer 解析失败。 -> [Mitigation] 将 selector 和解析逻辑集中、提供测试；失败只返回状态/链接，不全文泄漏。
- [Risk] `capsule` 丢失长报告中的细节。 -> [Mitigation] 保留网页会话 URL，并提供用户显式 `full` 选项。
- [Risk] 指标或状态文件泄露敏感内容。 -> [Mitigation] 仅保存元数据并测试不存在正文/密钥字段。
- [Risk] MiMo 越界修改活跃路径或规格。 -> [Mitigation] 仅赋予 Git 开发副本范围，Codex审核 diff 与测试后才决定部署。

## Migration Plan

1. 在本地 Git 基线中提交现有 `chatgpt-web` 原始版本及经验证的 OpenSpec 文档。
2. 通过 GSD 建立隔离 milestone/worktree；由 OpenCode/MiMo 在限定文件范围实现功能与测试。
3. Codex 审核 diff，运行纯脚本测试、skill validator、OpenSpec strict validation。
4. 在用户知情的短时段运行一次真实 Chrome/OpenCLI 测试，验证窗口唯一识别、最小化、续聊与关闭。
5. 若所有验收通过，再将审核过的 skill 文件部署至活跃目录；远端推送另行确认。
6. 回滚方式为恢复活跃目录的原始四个基线文件；状态/指标新增文件可保留或在明确授权后清理。

## Open Questions

- OpenCLI automation window 的 target ID 能否在 macOS AppleScript 中可靠映射到唯一 Chrome 窗口，需要在实现前的只影响临时窗口测试中验证。
- 本次完成后是否将 `chatgpt-web` 推送加入公开 `fryeggs/skills` 仓库，由用户在部署审核阶段决定。
