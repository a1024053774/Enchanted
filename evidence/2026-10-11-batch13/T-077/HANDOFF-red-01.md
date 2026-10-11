# T-077-1 首批红态交接（2026-10-11）

状态：**INCOMPLETE**。主控决定 01/02 已原文留档；白名单 W01～W16 获准。产品源码和既有验收断言尚未修改。仅新增真实 CLI 合同测试及沙箱外脚本，等待执行主控运行；本文件不声称已取得红态。

执行命令：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-sandbox.sh red-01
```

脚本限定本 worktree，要求 HEAD=`14b57d22a84bcaebfa91c5051b9909b53a570fac` 且 `workbench/src` 无修改，Node 26.5、外置盘已挂载、已有 node_modules。不会安装依赖。每个测试在短 `/tmp/s3-*` 下建隔离 repo/state，保存源码快照、实际命令、SQLite 读回和完整夹具归档。默认后台按产品命令 detached；受控线程后台使用既有适配器的 `start_new_session=True`。不操作 Herdr、正式工作台或主 checkout。

13 个 focused cases：

| 场景 | 起点预期的业务红态 |
| --- | --- |
| worker 命名 | 随机目录且 detached，不符合项目/任务/序号和分支规则；W16 |
| clean revoke | 目录未清理、无规定隐藏引用；W02 |
| clean revise | 同上，先用保存的 C 验证旧身份被拒；W10 |
| verification 命名 | 完成条件在旧随机目录中运行；独立记录 cwd 与 detached 状态；W14 |
| 完成的 verification 清理 | 结果已落库但目录仍在，M 无用途引用；W08 |
| 交集无理由认领 | 同仓重叠路径的第二个 claim 错误通过；W12/W13 的第一段 |
| dirty revoke | 原始内容与 HEAD 保留，但没有绑定原 attempt 的 system issue |
| 状态未知清理 | 夹具 Git status 退出 73；场景保留，但没有 system issue |
| dirty integration | 已有保护拒收且内容/index 保留，但没有 system issue |
| 一次 R8 | 工作分支由独立写者前进后，integrate 立即拒收，未自动重新验收；W01 |
| 已集成的 run 清理 | 受控线程已回收但干净目录仍在、无 attempt 引用；W03 |
| timeout 保留未 submit 提交 | 未 submit 的 C 未集成，结束目录仍在且无隐藏引用；W04 |
| oracle 失败后终结清理 | 真实 oracle 拒绝且线程已回收，但目录仍在、无隐藏引用；W06 |

前 10 项通过默认生产后台与手工 claim；后 3 项通过 T-075-5 的既有受控线程边界及生产门禁，不能称真实 Codex 运行。真实模型用量为 **0/4**，不创建 CODEX_HOME、不复制认证、不安装 hook。本批不检查真实冲突回写、新 attempt、R8 第 4 次停止或完整 8/9/18；那些检查在后续批次先取得各自红态，不能由本批代替。

输出在 `T-077/outside-red-01/`，必须为新目录。每个案例的 `result.json` 保留原始测试退出码（红态为 1）、失败数、错误数和具体合同断言；`commands.json.gz`、`unittest.txt`、SQLite 读回和 `fixtures.tar.gz` 保存现场。`run.json.status` 在 baseline 阶段始终为 INCOMPLETE；仅当全部 13 项有业务断言失败、无 errors/skips 时 `red_confirmed=true`，协调脚本才退出 0。这不等于产品 PASS。

若遇导入/socket/命令语法/后台清理错误，`red_confirmed` 不成立。非预期业务失败或无法判定时保持现场并交主控，不改业务预期。probe 自身错误可修，但原输出不覆盖，另用新编号交回。

当前离线检查：Python AST 可解析；13 个显式 case 均存在；`bash -n` 通过；Node 为 v26.5.0；尚未运行任何 case。执行前请保留完整 stdout/stderr。依任务卡，本 worker 此处不申请提权，等待主控运行结果。
