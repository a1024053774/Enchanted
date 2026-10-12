# 换执行器：三个 worker 改为 gpt-6.1-sol xhigh、普通速度（2026-10-11 晚）

依据：构思主控 answer `20261012T015257Z-ideation-answer-001`，用户原话"全继续，不用 fast了，用 6.1sol 普通速度"；AGENTS.md 已于 47370fd3 记录。

做法：确认旧 worker 为 idle 后关闭其 pane（不留两个进程写同一原生会话），用 `scripts/launch-worker --resume <原生会话> --model gpt-6.1-sol --effort xhigh --service-tier default` 在新 pane 续接同一原生会话，保留上下文；argv 不再含 `service_tier="fast"`。launch 记录追加到 records/launches.jsonl（字段 `service_tier_requested=default`、`resumes_native_session`）。

| 原 agent / pane | 原模型 | 新 agent / pane | 新 launch | 续接的原生会话 |
| --- | --- | --- | --- | --- |
| s13-t076-2 / wF:p38 | gpt-6-astra xhigh Fast | s13-t076-2r / wF:p39 | launch-f74f0d2636684448a884b551e0ba1ee2 | 01a12bbb-d44f-74e2-a218-b44fb0fa283b |
| s13-t077 / wF:p36 | gpt-6-astra xhigh Fast | s13-t077r / wF:p3A | launch-a54ac5170aaa492fbf7aee1c4505a443 | 01a12b31-fd0c-7c92-9977-f14e7fae4a81 |
| s13-t078 / wF:p37 | gpt-6-astra xhigh Fast | s13-t078r / wF:p3B | launch-4f7c176de49042c28ae6617133ccc80c | 01a12b32-017d-7de0-8b81-77b382a05f7e |

注意：T-076-2 的未提交改动仍在主 checkout 工作区，关闭 pane 不影响文件。续接后 T-076-2 窗格页脚显示 GPT-6.1-Sol xhigh，周额度提示"only 2% left"。

launcher 变更（scripts/launch-worker）：Fast 改为可选 `--service-tier fast`，默认不传；新增 `--resume` 续接原生会话。产品 `workbench/src/panes.ts` 仍硬编码 Fast，需各写入者在自己分支去掉（T-076-2 主 checkout、T-077 分支）。
