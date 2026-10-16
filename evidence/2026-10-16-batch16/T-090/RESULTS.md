# T-090-1 修复与宿主验收交接

状态：INCOMPLETE。最小产品修复与静态检查完成；修复后的宿主绿态、整组回归及独立审查尚未运行，不宣称产品 PASS。task `T-090`、attempt `a1`、worker `s16-t090`，身份与完整启动 argv 见 `worker-launch.json`。启动参数请求 `gpt-6.1-sol`、xhigh、default tier；实际供应商 tier 未核对。

## 已核对证据

- 红态采集 PASS：`red-01.json`、`red-01.archive.json`，起点 `f08a280bdf6142443efd52d4897d2305fd68987f`。指定原方法 1 test、1 error、0 failure、0 skip；审查报告已接受，结束核对以 `review_worker_workspace_changed` 失败。worker 在开始和结束时 HEAD 相同且不等于 C。详情见 `RED-READBACK-01.md`。
- 起点反例 PASS：`boundary-baseline-01.json`、`boundary-baseline-01.archive.json`。HEAD 改动、变脏和切换到预先存在的同提交分支三条场景均被拒；共享 refs 未变，task paused、review unknown，产生问题记录并保留现场，没有 `review_reclaimed`。三条均无宿主或清理错误。
- 修复前项目状态 PASS：主控补齐稀疏检出的 `.grilling` 后，`project_map.py status --root .` 为 0 problems、0 stale living docs。先前非零输出原样保留，未改地图。产品修改后，status 按 covers 规则标记 `workbench/README.md` stale，见 `project-map-candidate.txt`；该文件与地图均不在写入边界，由主控核对 Verified。

## 产品改动

只修改 `workbench/src/gates/core.ts` 的审查开始与结束 worker 边界：开始时把实际 HEAD、分支、status 写入现有 `review_requested` 追加式事件；结束时按 task、attempt、review_id 读取本次快照并比较，要求初始及结束 status 均为空。缺失快照仍拒绝；保留原有 worker 路径、登记和分支归属检查。

审查候选仍绑定冻结 C；原有审查目录干净、共享 refs 未变、副本与启动参数核对、结束核对后才写 `review_reclaimed` 和集成前置均未改。没有修改 `acceptance/`、公共契约类型、冻结协议、启动策略、测试 driver 的回收逻辑；没有 reset worker、跳过回收或伪造事件。

测试增加三条通过真实 CLI/后台/relay/Git/SQLite 的外部变更反例。原整组 runner 仅增加原方法选择参数，仍核对完整原组成员数量、继承方法身份与原断言。

## 宿主绿态与整组命令

从本 worktree 执行，使用新 label，不覆盖已有红态或基线：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t090/evidence/2026-10-16-batch16/T-090/run-host.py --phase green --label green-regression-01
```

脚本按顺序运行：原冻结候选用例；原交付 8、恢复 9、编排 18；三条 worker 边界反例；T-082 七条正常及结束核对场景；四个启动变异（只读 argv、错误工作目录、联网、tmp 可写）；一个省掉 worker 结束检查的坏实现，分别运行三条新反例，必须命中 `T090-WORKER-HEAD`、`T090-WORKER-DIRTY`、`T090-WORKER-BRANCH` 的业务失败。最后一项证明新反例能拒绝已知坏实现，宿主或导入错误不算拒绝证据。

原始输出直接写 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-090/green-regression-01/`；仓库仅生成摘要及 `.archive.json`。临时运行夹具复制到外置盘并核对文件数、字节数后才清理原件；外置盘缺失即报错。借用既有依赖，不安装、不构建、不链接构建输出。真实模型回合为 0，PTY/原生进程观测是受控输入，不据此声称真实 Codex 沙箱边界已复验。

红态可在保留的起点源码快照复现（输出目录必须另取新名）：

```sh
python3 -B /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-090/red-01/source/workbench/tests/run_s3_rebased_regression.py --suite coop --case test_submit_requires_clean_head_and_cannot_replace_frozen_candidate --revision f08a280bdf6142443efd52d4897d2305fd68987f --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-090/red-replay-01
```

重放旧 runner 的临时夹具仍需按 T-088 归档，不能因重放失败覆盖原件。

## 当前检查及限制

PASS：`node --check workbench/src/gates/core.ts`；三个 Python 文件 AST 解析；`git diff --check`；UTF-8 回读；修改边界核对。未跑构建（本任务不需要构建，也没有安装依赖）。

INCOMPLETE：修复后真实入口绿态、整组回归、三个新反例的坏实现检出、主控独立审查、门禁验收与集成，以及 living doc Verified 核对。worker 已只读对照 README 的审查段（115–119、194–197 行）：正文要求审查期间 worker 未变，与本修复一致，未发现需要改写的语义；仍由主控完成地图核对。候选完整提交号在 worker 最终交接中报告；本报告不替代显式交付、验收或集成。
