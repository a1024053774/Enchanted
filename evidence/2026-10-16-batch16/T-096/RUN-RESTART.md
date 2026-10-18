# T-096：执行主控真实重启验证

状态：**INCOMPLETE**。`-01` 两场的残留已由主控收尾并归档，收尾结果 PASS；`red-b-02`、`tracer-b-02` 仍在第一次后台故障注入阶段失败，没有到达重启读回。下一步先只读核对并归档 `-02`，再用 `-03` 新标签重跑。

候选先冻结成提交；运行使用新 label、外置盘输出目录和构建槽，不覆盖旧运行。执行主控确认没有另一场隔离 Electron 验证同时运行；脚本只操作自己的 PID。原 `cleanup_failed_01.py` 已执行完成，不再作为当前步骤重跑；记录为 `cleanup-failed-01.run.json` 和两份 `*-cleanup-failed-01.archive.json`。

本次固定归档命令（无新 daemon／CLI／Electron，无信号、停止命令或源目录写入）：

```sh
python3 evidence/2026-10-16-batch16/T-096/archive_failed_02.py --label archive-failed-02 --approval-ref '执行主控 T-096 #8：只读核对并归档 red-b-02、tracer-b-02'
```

它只接受 `/private/tmp/t078-2-t096-dkri52ul` 和 `/private/tmp/t078-2-t096-j4p4ocqz`，并把原摘要／ownership.jsonl 与主控给定的 14 个 PID 核对。所有 PID 须不存在，端点须缺失或为原 daemon 的死端点；Unix socket 探测只接受 ECONNREFUSED，其他状态均停止。复制前后再次核对；存活 PID、活动／未知端点、后续 epoch 或已有归档均拒绝，不接管、不覆盖。

源目录所有内容保留不变。死 `state/control.sock` 不能作为普通文件复制，私有 `operator-1.json` 不得进入证据，因此只排除这两个明确路径，在 preflight／清单记录其元数据和理由；凭据内容不读取。其余文件复制到原外置盘 run 的 `fixture/`，逐项比较路径、文件数、字节数与 symlink 原始目标文本；源目录对应部分也须在复制后保持不变。清单的 comparison_scope 明确不含排除项，不冒称连同私密凭据及 socket 的整树完全相同。

runner 的进程探针统一为单次已记录读回：rc 1 且 stdout／stderr 均为空时返回“已退出”；非空诊断、其他退出码、错误格式仍报错。身份检查与发信号之间若发生 ProcessLookupError，同样记为已退出，不重试信号；权限错误仍抛出。非阻塞 stdout、计划内退出、逐阶段收尾及未知启动的 handoff 沿用已验证路径。所有新发现的写入者在故障注入前追加落盘身份。

每场预算及收尾规则写在 `run_restart.py` 开头。真实 Claude 版本配置为 2.1.302；不传模型提示词、不输入终端按键、不登录。三格为两个真实 Claude 主控，加一个受控 C receiver 替代 Codex 的 worker。杀掉本场 Electron、daemon、shell 与 CLI 后，第二次 Electron 不传 launch；窗格必须从保存集回来。worker 不启动第二个进程，其门禁 attempt 必须与重启前读回相等。

脚本通过 `controller_start` 创建启动记录；缺 argv 和错误版本在停止后的隔离 `launch_records` 中注入，不修改门禁拥有的 tasks/attempts；缺 session 保存原件后使目标不可用。恢复仍经过生产 daemon 入口，失败窗格须在真实 Electron 中只读显示“未恢复”，不能出现 `pane_restored` 事件。

零回合会话夹具：首轮 CLI 不提交请求。停止后脚本给每个原 session ID 放入一对明确标注为合成的历史 user/assistant 记录；它不是模型输出。第二轮须用完整原参数加原 session 选择器续接，macOS sysctl 读出的实际 argv 必须逐字段相等；Electron 终端须显示预置历史的 nonce。只出现 PID 或后台成功事件都不能通过。真实 CLI 可能停在初始化／信任屏；遇到这种情况保存原始输出并报 INCOMPLETE，不自动确认，不把屏幕当成已获批准。

以下 `CLAUDE` 请替换为主控已核对的实际 2.1.302 可执行文件绝对路径；不要用会随更新漂移的别名。`--approval-ref` 填本次主控运行授权位置。

先跑 main 红态和候选单格 Tracer bullet；单格成立后再跑三格和故障。示例：

```sh
python3 evidence/2026-10-16-batch16/T-096/run_restart.py --source /Users/luckye/Documents/Code/a2a --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/red-b-03 --label red-b-03 --approval-ref T-096-main-red --claude CLAUDE --claude-version 2.1.302 --panes 1 --expect-red
python3 evidence/2026-10-16-batch16/T-096/run_restart.py --source /Users/luckye/Documents/Code/a2a-wt-t096 --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/tracer-b-03 --label tracer-b-03 --approval-ref T-096-controller-tracer --claude CLAUDE --claude-version 2.1.302 --panes 1 --check-close
python3 evidence/2026-10-16-batch16/T-096/run_restart.py --source /Users/luckye/Documents/Code/a2a-wt-t096 --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/three-b-01 --label three-b-01 --approval-ref T-096-controller-three --claude CLAUDE --claude-version 2.1.302 --panes 3 --check-close
```

三个故障各用独立场景；最后一场同时验证一个主控失败、另一个主控继续恢复，worker 仍未恢复、attempt 不变：

```sh
python3 evidence/2026-10-16-batch16/T-096/run_restart.py --source /Users/luckye/Documents/Code/a2a-wt-t096 --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/no-argv-b-01 --label no-argv-b-01 --approval-ref T-096-no-argv --claude CLAUDE --claude-version 2.1.302 --panes 1 --fault missing-argv
python3 evidence/2026-10-16-batch16/T-096/run_restart.py --source /Users/luckye/Documents/Code/a2a-wt-t096 --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/version-b-01 --label version-b-01 --approval-ref T-096-version --claude CLAUDE --claude-version 2.1.302 --panes 1 --fault version-mismatch
python3 evidence/2026-10-16-batch16/T-096/run_restart.py --source /Users/luckye/Documents/Code/a2a-wt-t096 --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/no-session-b-01 --label no-session-b-01 --approval-ref T-096-no-session --claude CLAUDE --claude-version 2.1.302 --panes 1 --fault missing-session
python3 evidence/2026-10-16-batch16/T-096/run_restart.py --source /Users/luckye/Documents/Code/a2a-wt-t096 --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/isolation-b-01 --label isolation-b-01 --approval-ref T-096-isolation --claude CLAUDE --claude-version 2.1.302 --panes 3 --fault missing-argv
```

输出与收尾：原始命令、argv、三份 snapshot、门禁 task 前后读回、API 请求和 Electron 事件保存在外置盘。仓库只写 `<label>.run.json` 摘要和 `<label>.archive.json` 清单。退出和身份无法核对时不归档，保留现场，按摘要中的 PID/路径由执行主控处理。正常结束时核对全部登记写入者退出，先删除本场临时 operator 凭据（不归档凭据内容），再复制夹具并比较文件数、字节数；其余原件保留。
