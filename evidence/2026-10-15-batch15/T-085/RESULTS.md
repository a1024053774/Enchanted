# T-085-1 恢复套件重启配置结果

状态：**PASS**

工作树起点为 `6ba3bde4174d8e0fc6db65a70a1216fd05c2cdac`。本任务没有修改 `workbench/src/`，没有调用真实模型，没有提交或 push。最终代码只改动 `workbench/tests/test_daemon_recovery_e2e.py`；运行脚本和结果均保存在本目录。

## 最终运行

外部执行命令为：

```sh
cd /Users/luckye/Documents/Code/a2a-wt-t085
bash evidence/2026-10-15-batch15/T-085/OUTSIDE-COMMANDS.sh
```

完整终端输出：[outside-run-03.log](outside-run-03.log)。脚本为三段选择未占用序号的输出目录，并在结束时打印各段退出码。

### 红态

红态在未修改的起点副本中运行：

```sh
git archive 6ba3bde4174d8e0fc6db65a70a1216fd05c2cdac | tar -x -C /tmp/t085-red-src.Qqc8kq
ln -s /Users/luckye/Documents/Code/a2a-wt-t085/workbench/node_modules /tmp/t085-red-src.Qqc8kq/workbench/node_modules
python3 -B /tmp/t085-red-src.Qqc8kq/workbench/tests/test_daemon_recovery_e2e.py \
  --output /Users/luckye/Documents/Code/a2a-wt-t085/evidence/2026-10-15-batch15/T-085/red-05
```

结果：退出码 `1`；`run.json` 为 `INCOMPLETE`，5 个用例中 4 个通过、1 个失败、0 个 errors。失败只有 `test_daemon_verify_interruption_and_operation_lock`，位置是起点测试的 `following` verify 退出码断言。`red-05/run.json` 的 CLI 命令记录中，第二次 `verify` 的原始回执为：

```json
{"ok":false,"error":"review_launch_config_required","user_input_observer":{"state":"healthy"}}
```

这确认了任务卡要求的缺审查启动配置红态。

### 绿态

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t085/workbench/tests/test_daemon_recovery_e2e.py \
  --output /Users/luckye/Documents/Code/a2a-wt-t085/evidence/2026-10-15-batch15/T-085/green-03
```

结果：退出码 `0`；`green-03/run.json` 为 `PASS`，`tests_run=5`、`failures=0`、`errors=0`。`outside-run-03.log` 记录五个用例全部 `ok`。

### 变异

变异由 `OUTSIDE-COMMANDS.sh` 在一次性副本中完成。副本源码和运行命令为：

```sh
git archive 6ba3bde4174d8e0fc6db65a70a1216fd05c2cdac | tar -x -C /tmp/t085-mutant-src.N1tQmu
cp /Users/luckye/Documents/Code/a2a-wt-t085/workbench/tests/test_daemon_recovery_e2e.py \
  /tmp/t085-mutant-src.N1tQmu/workbench/tests/test_daemon_recovery_e2e.py
python3 -B /tmp/t085-mutant-src.N1tQmu/workbench/tests/test_daemon_recovery_e2e.py \
  --output /Users/luckye/Documents/Code/a2a-wt-t085/evidence/2026-10-15-batch15/T-085/mutant-03
```

变异只对目标中断用例把重启宿主的配置目录换成空的 `empty-review-control`；其余四个用例仍使用原配置。结果：退出码 `1`；`mutant-03/run.json` 中只有目标用例失败，另外 4 个通过、0 个 errors。失败点是配置来源比对断言：`empty-review-control/config.json` 不等于中断前的 `quality-control/config.json`。因此该变异被完成条件检测到。

局限是：这个变异在配置比对断言处停止，没有继续进入产品审查创建路径，所以不会再次产生产品错误码 `review_launch_config_required`；它证明的是重启配置等同性断言能拒绝空配置。产品错误码的独立红态由 `red-05` 提供。

## 三轮运行经过与根因

第一轮记录在 [outside-run-01.log](outside-run-01.log)，红态 `red-03` 已复现目标缺配置失败。绿态和变异当时都被新增的 `ready_record['root']` 字符串断言挡住：夹具路径一侧显示 `/tmp/...`，`Path.resolve()` 另一侧显示 `/private/tmp/...`。这不是 daemon 行为差异，而是 macOS `/tmp` 符号链接的证据比较缺陷；修复为两边都 `resolve()` 后，四个集成案不再被误拒。

第二轮记录在 [outside-run-02.log](outside-run-02.log)，红态 `red-04` 仍只有目标案失败。绿态的配置比对已通过，重启后第二次 verify 已创建审查，但测试在 `after['task']['state'] == 'verified'` 处看到 `reviewing`。根因是 `start('verify')` 直接启动真实 CLI 子进程，绕过了 `DaemonCards.cli()` 中原有的 `QualityDriver.complete_review()` 调用；受控 reviewer 没有通过 `pane_release`、`signal` 和结果回收把审查结论送回门禁。修复是在该 verify 子进程成功退出后，经同一受控 CLI 驱动 `self.quality.complete_review(self.task)`，没有放宽 verify 或伪造产品结果。

第三轮记录在 [outside-run-03.log](outside-run-03.log)：`red-05` 保持预期红态，`green-03` 5/5 通过，`mutant-03` 只让目标案因空配置比对失败，另外 4 案通过。

## 重启配置证据

绿态目标用例的 artifact 在 [green-03/artifacts.tar.gz](green-03/artifacts.tar.gz) 内，成员为：

```text
a4r-m3idw2d_/c-a_n4af8c/restart-launch-config.json
```

该 JSON 给出：

- `before.ready`：`/tmp/a4r-m3idw2d_/c-a_n4af8c/daemon-ready.json`；
- `after.ready`：`/tmp/a4r-m3idw2d_/c-a_n4af8c/daemon-restart-ready.json`；
- `before.source` 与 `after.source`：同一规范化路径 `/private/tmp/a4r-m3idw2d_/c-a_n4af8c/quality-control/config.json`；
- `equal: true`；两份配置都含 8 个受控 reviewer 配置；重启 argv 的最后一个参数也是该 `quality-control` 目录。

同一 artifact 的 `verify-complete.json` 显示最终 `task.state=verified`、`verification.state=passed`、`review.state=passed`。受控 reviewer 的结果投递记录在同一临时夹具的 `quality-control/driver.jsonl` 中；宿主使用受控 PTY，`real_codex_turns=0`。

## 保留的失败现场

`outside-run-01.log`、`outside-run-02.log` 及其 `red-03`、`red-04`、`green-01`、`green-02`、`mutant-01`、`mutant-02` 输出目录均保留，没有覆盖或删除。`red-02` 仍保留沙箱直接调用 `/bin/ps` 的权限失败现场；`red-01` 是误预创建输出目录后留下的空目录。

## 地图状态

在报告完成前运行：

```sh
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
```

结果：`Problems (0)`、`Stale living docs (0)`，退出码 `0`。T-085 仍由执行主控按门禁流程处理，本 worker 未提交。

T-085 READY
