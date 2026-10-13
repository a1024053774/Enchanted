# 每会话普通速度覆盖：无模型探针与换执行器（2026-10-13）

依据：answer `20261013T142903Z-ideation-answer-001`，用户原话"B 先探针，再每会话覆盖 (Recommended)"。用户全局 `~/.codex/config.toml` 设 `service_tier = "priority"`；执行主控不改它。

## 探针（不花模型额度）
`python3 evidence/2026-10-13-tier-probe/probe.py <新输出>`：对每个候选覆盖启动 `codex app-server --listen stdio://`，调用 initialize、`config/read`（含层）和 ephemeral `thread/start`（不发回合），读回 CLI 实际生效值。结果 `probe-01.json`（codex-cli 0.162.1）：

| 覆盖 | config/read | thread/start 实际 |
| --- | --- | --- |
| 无 | priority（继承全局） | priority |
| `-c service_tier="default"` | default | **default** |
| `-c service_tier="flex"` | flex | flex（降级档） |
| auto / standard / 空串 | 原样 | null（未知值被丢弃） |

`codex debug models` 显示 gpt-6.1-sol 仅有 `priority`（名为 Fast）一档附加速度、default_service_tier 为空。结论：**`-c service_tier="default"` 能压过全局 priority，且会话实际回报 default（普通速度）**。PASS。

## 换执行器（会话内改不了速度，按换执行器处理）
旧 worker 进程挂在共享 app-server daemon（pid 80882，由 T-077 worker 进程 10-13 10:24 重启时拉起），关闭 pane 后 daemon 一度仍持有会话写锁（"This conversation is open in another app"）；三个 pane 都关闭后锁于 10:33 释放。launcher 因此加 `--no-daemon`（与产品 Panes 一致），并始终显式传 `-c service_tier="default"`。未终止任何 daemon 进程。

| 新 agent / pane | launch | 续接原生会话 | 会话日志读回 |
| --- | --- | --- | --- |
| s13-t076-2s / wF:p3D | launch-632ff9488406442585d7e3ec1aa6fa35 | 01a12bbb-d44f-74e2-a218-b44fb0fa283b | service_tier "default"（14:33:40Z）|
| s13-t077s / wF:p3E | launch-b0cde095f0074c90b81a340ab320ed97 | 01a12b31-fd0c-7c92-9977-f14e7fae4a81 | "default" |
| s13-t078s / wF:p3F | launch-dfbd5e5f2f124805bb5aecd26762ca11 | 01a12b32-017d-7de0-8b81-77b382a05f7e | "default" |

中途 s13-t076-2s 首次启动于 wF:p3C 被会话锁拦下（launch-a6c190bb651b4893bfefe80730bfbe59），未输入任何内容即关闭 pane，记为失败启动。产品 `workbench/src/panes.ts` 为被测 worker/reviewer 也须显式加 `-c service_tier="default"`（隔离 CODEX_HOME 不继承全局设置，但按决定第 4 条仍显式带上）。
