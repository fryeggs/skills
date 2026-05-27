## ADDED Requirements

### Requirement: 默认结构化精华回传
系统 SHALL 为 `ask` 和 `delegate` 提供 `receipt`、`capsule` 与 `full` 回传模式，并 SHALL 将 `capsule` 作为默认模式。

#### Scenario: 未指定回传模式
- **WHEN** 用户或上游代理调用 `ask` 或 `delegate` 且未指定回传模式
- **THEN** 系统仅向 Codex 输出结构化 `capsule` 结果及网页会话链接，而非完整网页回答

#### Scenario: 用户明确要求全文
- **WHEN** 调用方显式选择 `full` 模式
- **THEN** 系统输出网页端完整回答，并在命令语义中表明这是显式选择的高回传模式

### Requirement: Capsule 协议提取与限制
系统 SHALL 要求网页端在 `capsule` 模式输出可解析的标记 JSON 精华包，且 SHALL 对打印回 Codex 的内容应用可配置硬长度限制。

#### Scenario: 有效 capsule
- **WHEN** 网页答案包含有效 `<codex_capsule>` JSON 段
- **THEN** 系统解析并仅打印受长度上限限制的精华包、状态与会话 URL

#### Scenario: Capsule 缺失或无效
- **WHEN** 网页答案不含有效 capsule JSON 或无法解析
- **THEN** 系统打印提取失败状态与会话 URL，并 MUST NOT 回退打印原始全文

### Requirement: 低敏感度指标
系统 SHALL 可记录用于估算上下文节省的非敏感元数据，且 MUST NOT 将提示词正文、网页正文、Cookie 或 API Key 写入指标记录。

#### Scenario: 完成一次 capsule 调研
- **WHEN** 网页调研完成并产生回传结果
- **THEN** 指标最多记录模式、状态、长度、估算节省量与窗口清理状态，不包含正文或认证数据
