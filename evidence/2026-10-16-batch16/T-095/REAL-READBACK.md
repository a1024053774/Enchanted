# T-095 真实探针读回（2026-10-18）

**INCOMPLETE。** 原件位于 `real-red-readback.json` 指向的外置盘目录；原始命令输出、ANSI 与原生记录未改写。`real-panel-inputs.json` 只摘录命令测试读取的小输入，原件仍保留在外置盘。

| 操作者阶段 | 同期两次 Herdr 原值 | 当前画面 | 能证明什么 |
| --- | --- | --- | --- |
| after-submit | done → working | Working、普通输入框和底栏 | 读取跨过状态变化，应输出 unknown；不是面板红态。 |
| collapsed | blocked → blocked | Working (2m 21s)、普通输入框和底栏；没有问题文字或面板控制条 | 主控声明这是折叠形态；屏幕本身没有专属提问标记。 |
| expanded | blocked → blocked | 问题标题、`› 1. A`、`enter submit`、`⌃] skip`、`option 1/3`、`⇧→ main prompt` | 这些位置和控制条组合可以作为提问面板的正向机械依据。识别不依赖问题正文或 A/B 内容。 |
| cancelled | working → working | Working (2m 58s)、Tip、普通输入框和底栏 | 在主控按 Ctrl+] skip 后恢复普通活动。该操作是手动跳过，不是自动答案，也不是 Esc。 |

原生记录只有一个根回合，工具调用为一次 `request_user_input_async` 和三次 `clock.sleep`；没有命令或文件修改工具调用。并行临时到 4 个的例外来自本次主控 #101 转述的用户当场确认，不扩展到后续运行。红态预算已用 1 根，绿态至多再用 1 根，由主控运行。

**原 ticket 的“两种形态当前读为 working”未复现。** 两种面板采样均为 blocked，不能把 Working 活动行当成 Herdr 的 working 值，也不能把之后取消问题时的 working 移到面板阶段。新增状态的缺失可以用原件回放做合同红态，但它不能替代原 ticket 中没有取得的错误分类证据；本 worker 不改验收条件或勾选 ticket。

这是隔离配置、Codex 0.163.0 / Herdr 0.9.4 下的一次观察，不据此否定原始 T-094 记录，也不补造两次现象不同的原因。折叠 ANSI 原件也只有活动行、输入框与底栏的样式，没有额外的提问控制标记。

**blocked + Working 不是当前证据下“等待主控回答”的充分判据。** Herdr 的 blocked 合并了批准和提问等 Action Required；本次折叠屏幕又缺少专属提问控制条。该组合只证明有操作等待与活动画面，不能证明等待的对象和类型。依照已确认的“只认面板 UI 结构组合，读不出时报 unknown”，本候选将此情况保留 unknown。要让折叠形态也稳定正判，需要主控另行确认增加可绑定的结构化提问事实来源，或提供折叠时可读的专属 UI 事实；不通过问题正文、标题语义或“不是 working 就是提问”推断。

同时发现两项准备代码的身份假设不成立：同一终端、同一个 Codex 前台 PID 23065 的 `revision` 从启动时 2 变为 225、240、252；它不是运行身份。隔离 CODEX_HOME 的这次 `agent get` 也未给出 `agent_session`。修正后的投影保持 launch / worker / pane / terminal / cwd 的登记关联，并核对读取前后稳定性；原生身份有登记或可观测时继续核对，没有时明确报告终端登记关联，不假称已核对原生身份。这是状态监视投影，不替代门禁的 fence 或运行时身份校验。

`/tmp/t095-panel-pg9mo4yh` 检查时只剩空的 `fixture/`，CODEX_HOME 确已不存在。已仅用 rmdir 清除这两个空目录，没有删除任何文件；见 `red-temp-cleanup.json`。
