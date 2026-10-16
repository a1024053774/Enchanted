# T-082 独立审查 01 返工

状态：**INCOMPLETE**。起点 HEAD 为 `f09f0dcc8`，产品源文件与独审的 `7f2bd4061` 相同；已修改工作树，尚未提交或经新独立审查。真实回合保持 2/4，本轮只用受控 PTY。

主控 #55 读回：OUTSIDE-11 的 01～14 全 PASS；第 15 段只读变异实际触发了门禁 `review_launch_boundary`，失败 id 是更早的 `TRACER-REVIEW-START`，原 runner 错等 `TRACER-REVIEW-COPY-ARGV`，因此整串 INCOMPLETE。default tier 两个负例均在原 id 失败，default-tier-green PASS。诊断与实际 argv 见 `launch-policy-diagnosis-01/readback.json`。已修正两个 T-076 runner 的只读变异预期，并严格核对原始拒收码/实际 argv；审计未改。

仅重跑该段：`bash evidence/2026-10-15-batch15/T-082/OUTSIDE-COMMANDS-12.sh`，结果待主控运行；不重跑已通过的 01～14。

## 修前证据

先只读打开外置盘 `review-01-outside/r82-review01-UnlqXU.tar.gz`，保存第 14、15 段的原始回执选段和归属到 `rework-01-red-readback/`，随后才改产品。`source.json` 保存修改前 `git diff 7f2bd4061 HEAD -- workbench/src` exit 0。

- `integration_before_end_check.json`：真实 signal socket 延迟客户端关闭，报告入库后、结束核对前，integrate `ok:true`；main 实际从 G 前移到 M，审查目录外部改动仍在，事后状态 accepted。原断言 `REVIEW-END-BEFORE-INTEGRATE` 为 contract_failure，cleanup 无失败、host_exit=0。
- `requirements_workspace_changed.json`：请求 workspace 改为 wrong-copy，入库 workspace 与要求的副本不同，task verified/review passed。原断言 `REVIEW-REQUIREMENTS-WORKSPACE` 为 contract_failure，cleanup 无失败、host_exit=0。

这些是独审已经执行的真实入口失败，不是本次重新执行的记录。OUTSIDE-11 会在原产品副本再次重放两案；不把后续重放改称时间上更早的运行。

## 逐项修复与检查

| 独审发现 | 工作树改动 | 新检查 |
| --- | --- | --- |
| P1：报告入库即可提前集成 | `requireReviewed` 复用既有 `review_reclaimed` 完成事件，按 task/attempt/review 绑定。调用者在任务操作锁内核对；回收也持同一锁，只有结束边界检查和两个清理步骤完成后才写事件。daemon 回收路径不另开 API，不事后回滚 | 延迟真实 socket 关闭的脏目录案、干净目录案均必须拒绝提前集成并保持 main；干净案回收后同一候选必须能集成 |
| P2：请求副本元数据未绑定 | core 在 `reviewEvidence` 检查形状之后、保存 result 之前比较 workspace 与本次 candidate_workspace；parser 继续只负责结构，报告内容不作判断 | 改写 workspace 后必须 paused/unknown，且没有 review_result 入库 |
| P2：结束负例不足 | 三个场景直接进入现有 `test_t082_review_boundary_e2e.py` 的真实 CLI/daemon 用例 | 共享 refs 改变必须作废/上报/保留副本；去掉结束完成前置、去掉 workspace 比较、去掉 refs 比较三个单点错误实现各须在对应断言失败 |
| P2：default tier 负例换了观测点 | runner 不再拿缺少其他新契约的旧快照作此负例；分别从当前 D3 候选仅移除 worker/reviewer 的 default override | 保持 `TRACER-WORKER-DEFAULT-ARGV`、`TRACER-REVIEWER-DEFAULT-ARGV`；reviewer 案先通过 D3 启动边界和身份检查 |
| P3：相同分支仅作变异锚点 | 三个生产值改为常量，相关 runner 改常量的实际值；条件变化仅存在于临时变异源码 | 四种启动拒收、T-076 launch-policy 和正例回归 |

`run_cases` 增加测试进程的 `A2A_TEST_ARTIFACT_PARENT` 目录设置；新批次显式选外置盘。它不传给产品门禁。产品自行创建的 `/private/tmp/a2a-requests-*` 根据停止前已保存的 launch 归属及 host_exit=0 收据清理，不重开已停止的 WAL 数据库。

## 主控运行命令

```sh
bash evidence/2026-10-15-batch15/T-082/OUTSIDE-COMMANDS-11.sh
```

新输出为 `outside-command-11-01/` 起递增。各步独立保存结果并继续，不用第一处失败掩盖后续结果。计划含两项原版红态、候选结束/元数据用例、三个单点错误实现、启动拒收、T-076 指定三性质及严格协议、T-077 四案、修复后的 launch-policy 串。

正常停止后归档并删除本次外置夹具；缺少停止收据或有超时则保留现场，返回非 0。脚本末尾打印输出路径与退出码。该批业务绿态和三个单点错误实现检出已由主控 #55 确认（01～14）；剩余 launch-policy runner 的预期修正等待 OUTSIDE-12，随后再交主控冻结。

a7f4cc30 锚点和质量 runner 的审计逻辑未改；旧拒收记录继续保留。真实权限边界的既有原生工具回执仍保留，本轮没有重放真实 Codex。
