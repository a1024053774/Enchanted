# T-077 换执行器与速度配置

2026-10-12，主控 #77：worker 从 s13-t077 换为 s13-t077r，续接同一原生会话；执行器改为 gpt-6.1-sol / xhigh / 普通速度，不传 Fast。授权原文及额外预算见本目录 `20261012T015257Z-ideation-answer-001.md`。

生产 Panes 去掉 `service_tier="fast"`，启动记录的 service_tier_requested 改为 null，表示没有传该配置，不声明供应商实际 tier。README 与直接断言该字段的窗格测试同步。

`no-fast-red-01.json` 保存旧候选因完整 argv 仍含 Fast 而发生的断言失败；`no-fast-green-01.json` 为同一检查的 4 项通过。两次都替换了版本响应和 PTY，没有启动外部进程、复制 auth 或调用真实模型。预览计划独立保存在 `real-plan-02-preview.json`，最终审批计划将在产品提交后生成，不改旧证据。

重现绿态检查（输出文件不得已存在）：

```sh
node evidence/2026-10-11-batch13/T-077/check-real-launch-offline-02.ts evidence/2026-10-11-batch13/T-077/real-plan-02-preview.json /tmp/t077-no-fast-check.json
```

已有真实回合 4 个；用户另批 2～4 个。本次新实例计划 4 个、上限 4，独立 ledger 记录新增用量，累计上限 8。两次启动各 2 个回合，分别审批。旧失败和旧 ledger 不更改。主控 #74 的 16 组回归已经读回全部 PASS；速度配置变更只做上述最小受影响检查。
