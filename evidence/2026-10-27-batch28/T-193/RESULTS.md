# T-193 结果：主控可在多个已打开项目里建任务和派发

日期：2026-10-27。状态：PASS。

## 改动

- 主控身份绑终端，命令按 `project` 或完整任务 id `<项目>+<任务>` 找项目，限工作台里已打开的项目；未打开的项目拒绝并说明。每个任务仍只绑定一个仓库（`daemon.ts`、`terminalCli.ts`、契约 `a2aGates.ts`）。
- 额外目录改为派发时逐次指定（`extra_directories`），写入 attempt、启动记录与 argv；未指定就不给，项目设置里的目录不再自动给 worker。monitor 不获得额外目录。
- 获批目录是派发那一刻的真实路径，之后不再重新解释（`gates/core.ts` 的 `extraDirectories(..., approved)`）：run 在 `run_bound` 时、worker 启动前落盘；run 恢复与合并冲突后的自动替换只核对并沿用原列表，路径改指、消失或变成文件就拒绝（`extra_directory_changed`）。
- 启动前的最后核对放在全部异步准备之后、紧接 `store.launch`（`panes.ts`），reviewer 沿用 worker 的列表，审查门禁核对二者一致。
- 说明：README、角色卡（worker、reviewer、monitor）、SKILL.md、`a2a help`、项目设置页文字、产品页 `docs/index.html` 一句。README 按第 4 轮 D1 改为“run 恢复和合并冲突后的自动替换沿用原 attempt 获批的目录；普通改卡后的新派发仍须重新指定”。

## 证据

测试：`workbench/tests/test_t193_multi_project_e2e.py`。真实后台、socket、终端身份与交互 Claude Code CLI，模型为本地脚本服务。

| 文件 | 版本 | 结果 |
| --- | --- | --- |
| `red-base.json`、`dev1-red-base.json` | 修前基线 | 失败于 `controller_reaches_other_opened_project`：跨项目建卡被拒 |
| `dev1-green-01.json` | 第一版 | 失败于仓库硬保护断言；保留 |
| `dev1-green-02.json`、`green.json` | 第一版、第 1 轮候选 | 6 项 PASS |
| `dev1-mutant-*.json`、`mutant-home-project-only.json`、`mutant-project-extra-dirs*.json` | 变异 | 各在业务断言失败（跨项目、未指定就不给） |
| `green-02-relinked.json` | 修复中 | 失败于 `relinked_directory_never_granted`；保留 |
| `green-03-relinked.json`、`green-04-claim-approved.json`、`green-05-launch-check.json` | 第 2、3 轮修复后 | 7 项 PASS |
| `mutant-follow-relinked*.json` | 变异：跟随换过的链接 | 失败于 `relinked_directory_never_granted` |
| `regression-t123_*`、`regression-t140_*`、`regression-t141_*` | 回归 | 22、22、24 项 PASS |
| `review2-fix-probes/`、`review3-fix-probes/` | 审查探针修后复跑 | 观察字段与说明见各自 `summary.json` |

复跑（`workbench/` 下）：

```sh
python3 tests/test_t193_multi_project_e2e.py --summary <新路径>
python3 tests/test_t193_multi_project_e2e.py --mutant follow-relinked --summary <新路径>
```

## 独立审查（Codex gpt-6.1-sol high，只读）

- 第 1 轮 `review-1.md`：NO_GO。reviewer 启动时重新解析目录；run 保存原始别名，重启后换目录。
- 第 2 轮（首次启动被供应商内容过滤中止，未出报告；重开后为 `review-2.md`）：NO_GO。恢复与冲突替换的预检和重新解析分离；首次派发的获批目录落盘过晚；一处变异定位失效。
- 第 3 轮 `review-3.md`：NO_GO。内部复用仍重新解析；Claude worker 启动构造的异步间隔里放过已改变的路径。
- 第 4 轮 `review-4.md`：PASS。两条均按根因关闭，复跑时序反例与正常对照；D1（README 措辞）已按建议修改。

## 未覆盖

- 未做 Electron 实机界面检查；agy、opencode worker 的额外目录本轮没有真实复跑。
- 第 4 轮建议把三个时序反例纳入常规回归；本 ticket 未加，探针保留在审查目录的报告里。
- 校验到 PTY 启动之间不是文件系统原子操作；不承诺对抗外部进程在最后一次核对之后换链接。
