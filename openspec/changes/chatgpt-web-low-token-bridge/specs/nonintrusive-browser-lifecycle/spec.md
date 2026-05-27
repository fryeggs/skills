## ADDED Requirements

### Requirement: 使用正常认证 Chrome 的临时 owned window
系统 SHALL 使用用户正常 Chrome 登录态执行 ChatGPT 网页操作，且 SHALL 为每次任务按需管理本次专属 automation window，而非常驻窗口、无痕窗口或临时空白 Profile。

#### Scenario: 执行网页研究任务
- **WHEN** 系统开始需要网页端的任务
- **THEN** 系统使用正常认证 Chrome/OpenCLI 通道建立本次临时 automation window，并在任务结束时释放该窗口

### Requirement: 唯一识别后才能最小化和发送
系统 MUST 在发送用户研究提示前确认将要操作和最小化的窗口唯一属于本次运行，且 MUST NOT 对无法确认归属的窗口进行最小化或关闭。

#### Scenario: 唯一识别成功
- **WHEN** 系统通过运行标识或受验证的 target 映射唯一定位本次 owned window
- **THEN** 系统最小化该窗口后才继续导航和发送研究任务

#### Scenario: 无法唯一识别
- **WHEN** 系统找不到或找到多个符合本次标识的窗口
- **THEN** 系统中止发送任务、返回失败原因，并不改变用户其他 Chrome 窗口状态

### Requirement: 清理仅限本次拥有的窗口
系统 SHALL 在网页任务完成或失败后关闭本次已确认归属的 automation window，且 MUST NOT 退出整个 Chrome 应用或关闭用户原有窗口。

#### Scenario: 执行成功或发生异常
- **WHEN** 网页交互结束或过程中抛出异常
- **THEN** 系统在清理阶段关闭本次 owned window 并释放单任务锁

### Requirement: 单任务互斥且无默认队列
系统 SHALL 通过原子锁防止多个网页任务并发控制同一通道，并 SHALL NOT 自动排队、挂起或持久化用户待执行提示词。

#### Scenario: 已有任务运行
- **WHEN** 第二个网页任务在锁已被有效持有时启动
- **THEN** 系统立即返回已有任务运行状态而不打开新窗口、不保存待执行正文
