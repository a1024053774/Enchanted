# T-078 09A-3 阻塞交接

2026-10-14，主控 #128 的新 worker；本轮目标收缩以用户当前会话答复为准：**“保持边界，先交阻塞报告及独立材料”**。

**产品与 09A-3 launch 材料：BLOCKED。** 没有修改产品，也没有取得新候选的真实入口红态／绿态；不能标 MATERIALS READY。整票仍 open、INCOMPLETE，旧 08e 或 09A-2 证据不替本候选背书。

## 根因与最小接线

| 文件 | 当前事实 | 必需改动／所有权 |
| --- | --- | --- |
| `workbench/src/gates/cli.ts:206` | 成功 signal 输出固定为 `{}`；失败输出 exit 1。daemon 拒收不足以阻断 Claude 的 UserPromptSubmit。 | 只将 UserPromptSubmit 的阻断决定传给真实 hook 输出／退出码；Stop 不变。T-080 独占，先由主控协调；本 worker 不写。 |
| `workbench/app/main.ts:75` | release IPC 不接收声明参数，只发 window_release。 | 转发明确空框声明、中断引用和输入代次；需扩大本轮文件边界或另派。 |
| `workbench/app/preload.ts:8` | releaseQueue 无参数。 | 保持同一窗口输入入口，转发 renderer 持有的声明；需扩大本轮文件边界或另派。 |

`gates/core.ts` 无须修改。不能以后台猜测、文本标记、替代 CLI 或另一个写入入口绕过。按主控 #128 的“必须改时先停下告诉我”停下后，用户已明确维持边界；本轮不再推进依赖该扩展的工作。

阻塞已追加到 [issue 20261014T122545Z](../../../.project-map/inbox/20261014T122545Z-worker:t078-09a3-new-issue-001.md)，没有关闭。主控可让 T-080 完成 CLI 接线并另派 main/preload，或在协调所有权后重新授权 T-078；之后须先取真实入口红态，再实施，不复用旧实例。

## 已交的独立材料

- [失败方式清单](FAILURE-MODES-09A3.md)：空框声明、中断引用、输入／组合代次、并发窗口、控制字节来源、拼接阻断及手打提交例外。实现仍 pending。
- [旧 slot 清理脚本与执行说明](SLOT-CLEANUP-AFTER-REBOOT-09A2.md)：只处理 `t078-09-d2d9c666-5621-4467-bbe4-d99450bd5503`，重启与当前使用情况核对后，完整归档读回，再删除精确目录。交主控运行；worker 未运行。
- [本地归档证据](slot-archive-static-09a3/result.json)：2/2 PASS；正例保留字节／链接，已知坏跟随链接变异实际触发成员集违约并被拒。真实外盘清理仍 INCOMPLETE。
- [静态交付检查](static-delivery-check-09a3.json)：Python 语法与 UTF-8 回读 PASS；diff 检查无错误。

09A-2 `/private/tmp` 根已丢失；之前外置 fixture 和仓库小份保留，其余未归档原件记证据缺口，不补造。原 root+slot 处置脚本不再满足前置，不能照旧执行。

本轮 vendor CLI／API／Electron／真实模型启动为 0；外置写入／删除／进程信号为 0。现有 worker 环境带旧 T-078-1/a1 标识，不能当新会话的当前 ownership 证明；未拿它 submit、验收或集成。新代码版本只包含材料、测试 helper、报告和追加式 issue，未 push。
