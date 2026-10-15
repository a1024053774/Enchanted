# T-078 09B run-04 handoff

状态：`INCOMPLETE`（材料与脚本就绪，阶段 A 未运行，launch `NO_GO`）。

主控 #195 的真实失败现场 `09b-stage-a-03/result.json` 保留：阶段 A 创建 root、两个 detached 假 API 与 daemon，`card_save` 因 `paths.deny: ["oracle/**"]` 返回 `invalid_task_card`，未 dispatch、claim、target 或 Claude CLI。`cleanup-09b-stage-a-03.py` 只绑定该 root `/private/tmp/t078-2-09b-run-576xn98k`、API 62217/62218 与 daemon 62220；先运行 `--dry-run` 做 scene/ready PID、argv/root、lstart 双读和 PID 复用核对，不发信号、不停 daemon、不归档、不删根；正式运行 daemon 经认证 `daemon_stop`，每个 API 最多一次 SIGTERM，归档后逐成员比对普通文件字节、目录类型、符号链接目标，全部通过才删 root。脚本未执行。

先后运行（同一原启动身份）：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/cleanup-09b-stage-a-03.py --approval-ref "主控 #196" --dry-run
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/cleanup-09b-stage-a-03.py --approval-ref "主控 #196"
```

dry-run 输出 `09b-stage-a-03-cleanup-dry-run/`，正式输出 `09b-stage-a-03-cleanup/`；两目录都已列入 `09b-run-04-allowlist.json`，正式 cleanup PASS 后再运行提交脚本。

#197/#198 已将正式 cleanup 的 62217 SIGTERM 超时保留为 BLOCKED，并确认 62218 未发信号。恢复脚本与输出目录：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/cleanup-09b-stage-a-03-recovery.py --approval-ref "主控 #198" --dry-run
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/cleanup-09b-stage-a-03-recovery.py --approval-ref "主控 #198"
```

恢复只在双读 argv/root/lstart 通过后分别对 62217、62218 发一次 SIGKILL；daemon 已退出，不重复 stop。主控已实跑 dry-run 与正式恢复：两个 SIGKILL、归档 71 成员／25,523 字节逐个读回 PASS，root 已删。假 API 的 SIGTERM 停止测试已保存红态 `09b-fake-api-stop-red-07` 与修复后绿态 `09b-fake-api-stop-green-08`；工作树 38 项 allowlist 归属预检 PASS。

修复在 runner：卡片现在使用 `paths.deny: []`，`oracle_paths` 由真实 `taskCards.validateTaskCard` 保护；`validate_card_preflight` 在创建 root、编译 receiver、fake API、daemon、target 之前调用。`09b-card-preflight-runner-06/results.json` 为 runner helper 的红（`oracle/**` 被拒）与绿（空 deny 通过），两项均 `spawned=false`、`root_created=false`，没有进程或 root。

交主控运行：

```sh
sh /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/commit-09b-run-04.sh
```

该脚本首提交 runner/card 修复与 #195 证据，随后调用 `prepare-09b-executable.py --label 09b-executable-materials-04`，冻结新的 materials-04 和 source freeze，再提交 RESULTS。它只做静态生成与 Git 提交，不启动阶段 A、CLI、API、目标或模型；材料冻结后仍 `launch_status=NO_GO`。主控须重新签 approval，才能另行决定是否运行阶段 A。
