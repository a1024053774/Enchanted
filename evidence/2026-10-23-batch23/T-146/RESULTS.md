# T-146-1 / a1

状态：INCOMPLETE。产品行为尚未修改，不是可验收的缺陷修复交付。

已读取任务卡、公共约定、ticket、项目地图、术语和 intent，以及 Reflect、侧栏、流程、角色申请与后台入口的相关代码。项目地图初检 Problems 0、Stale living docs 0。

## 已完成

- 新增 `workbench/tests/test_t146_session_state_e2e.py`。经真实后台与角色申请主控派两个真实 Claude Code worker（`claude-haiku-5-5`、本地脚本化 Messages 接口）：一个提交后空闲，另一个执行 Bash 工具等待测试释放；记录回收 worker、关闭主控终端前后的 Reflect、侧栏、流程 DOM 与后台快照。断言来自任务卡，缺失会话记录为 MISSING，不替换成 ended。尚未到达 Electron 阶段。
- 测试提供独立的新 `--summary`、`--revision`、`--mutant reflect-lifecycle`；变异在修复后恢复 `ebbae7bd0` 的 Reflect 实现。尚无绿态或变异失败证据。
- `scope-issue.md` 已经 `scripts/inbox send` 上报，编号 `20261023T100141Z-worker:b23-t146-issue-001`。

## 运行证据

命令：

```sh
python3 workbench/tests/test_t146_session_state_e2e.py --revision ebbae7bd0 --summary evidence/2026-10-23-batch23/T-146/red-attempt-01.json
```

结果：INCOMPLETE，退出 130。真实 CLI 已启动，Write、git add 和 git commit 成功；Bash 等待工具和 submit 工具均失败，错误为 `Exit code 71 / sandbox-exec: sandbox_apply: Operation not permitted`。发现环境失败后中断等待；finally 停止 fixture 后台并保存摘要。此结果不是业务缺陷红态。原始 fixture 保留在 `/private/tmp/t146-92adu2eo`；未将数据库或 trace 加入 Git，后续归档由执行主控处理。

`RUN-OUTSIDE-01.sh` 为沙箱外复跑准备，输出目录包含时间与 PID，保留既有证据；也列入两项要求的回归。未申请越权、未绕过 CLI 沙箱。

提交诊断候选后执行既有流程基线：`node workbench/tests/test_t111_flow.mjs /private/tmp/t146-t111-baseline-c49e7749a.json .`，退出 0，摘要 `{"status":"PASS","task":"T-111","model_calls":0}`。该结果只证明未改产品时的既有流程契约成立，也实证当前 oracle 排除 ended；不替代 T-146 修复后的回归。fixture 清理后 `control.sock`、`daemon.pid` 均不存在。收尾 project-map status 仍为 Problems 0、Stale living docs 0。

## 等待裁定

1. 状态同源最小修复需要改 `daemon.ts:409` 的 Reflect 调用入口，此文件不在允许清单。`renderer.tsx` 与 `main.ts` 未动。
2. 流程实现和受保护的 T-111 oracle 要求过滤 ended，侧栏不列已结束的角色申请主控；任务卡要求三处显示 ended。需要主控裁定展示规则与 oracle。
3. 代码显示关闭终端已会使角色申请 ended，尚未复现所述关闭后仍运行中。确定的代码差异是 Reflect 的生命周期与侧栏的完整状态不同；需真实 DOM 证据确定具体触发条件。
4. CLI 自然退出场景尚未写入测试，需在边界裁定与真实红态后补齐；不能用门禁回收替代此项证据。

修复、真实 Electron 红态/绿态、变异、T-137 与修复后的 T-111 回归、独立行为验收均未完成。当前测试是诊断候选，不以其未执行的断言宣称覆盖成立。无 submit 或验收通过结论。

独立只读诊断审查：针对冻结候选 `c49e7749a88356f55e4368aca7e85de10d0d660b`，审查员返回 `STATUS: INCOMPLETE`、FINDINGS 无，确认报告如实记录未修复、未取得 Electron 红绿态、未验证变异与 CLI 自然退出。该审查发生在上述 T-111 基线证据补记之前，不是产品验收通过。
