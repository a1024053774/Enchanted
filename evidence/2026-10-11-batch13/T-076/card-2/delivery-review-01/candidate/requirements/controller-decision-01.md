# T-076-2 执行主控决定 01：计划审阅

时间：2026-10-11；审阅对象：`PLAN.md`（开工 HEAD a7f4cc30）、`ISSUE-spec-channel.md`。

## 结论：计划批准，进入"新测试与红态交接"阶段

| 编号 | 决定 | 附加条件 |
| --- | --- | --- |
| P1 | 批准 `red_commands[].test_paths` 显式声明；批准从注册时工作分支提交读取 `.a2a/quality.json` 并冻结 | 只在夹具仓库提供该文件，本卡不改主仓库根配置；不保留两套红态定义 |
| P2 | 批准 reviewer 的 B 通道扩展：reviewer 最终消息只输出完整 JSON，由匹配的 Stop hook 落文件后走既有 RequestRelay | 不恢复 socket 方案 A；不剥 fence、不局部提取；非法即保存原文、上报、停止，不追加纠格式回合。worker 继续只走原文件 B 通道 |
| P3 | 批准 `run` 在审查通过后等执行主控显式 `integrate/abandon --score-file`，不预填分 | 期限显式给出，绑定原 attempt |
| P4 | 批准 W01–W06 与 F01–F04，范围以 PLAN 第 7 节的文件+方法为准 | Recovery 9 项不改业务断言；冻结候选反例（`test_coop_e2e.py:476–511`、`test_run_e2e.py:254–264`）不得改；实际需要超出白名单时停下另交 |
| P5 | 批准第 9 节 8 槽预算（正常目标 6，槽 7/8 须另行分配）；批准第 4.1 节的 reviewer 权限形状（只读、无 Git 写规则、独立 home 只复制 auth.json） | hook 仍按实例批准：每次真实启动前交准确 argv、隔离目录与 hook 命令，执行主控逐次批准后才运行 |

## spec 通道差异

确认：worker 沿 T-075 rev 4 的 B 通道，不按 spec 第 5 节字面回到方案 A。spec 文字差异由执行主控转交构思主控处理（issue `20261011T161950Z-worker:s13-t076-2-issue-001` 已 forward）；本卡不改 spec。

## 下一步与停止点

1. 写新测试与 `assertion-hunks.md`，起点上取得业务红态；新入口无基线时按 PLAN 第 7.1 节用已知坏变异体补证，不把 usage 错误算红态。
2. 准备 `outside-sandbox.sh` 的阶段 1–3（版本/外置盘检查、起点红态、受控反例），回复 `T-076 OUTSIDE-SANDBOX READY` 并停下，由执行主控运行。
3. P-review 真实探针（槽 1）不在本阶段启动；红态交回后再单独交其 argv 与 hook。

T-077 合流说明：`exec/t077` 尚未合入 main；本卡只写主 checkout 自己范围。若 T-077 先合入，重读 `gates/core.ts` 等冲突位置再继续，不覆盖、不回退。
