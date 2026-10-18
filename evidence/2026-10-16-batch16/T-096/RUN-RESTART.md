# T-096：执行主控真实重启验证

状态：**INCOMPLETE**。`red-b-01`、`tracer-b-01` 均因脚本缺陷失败，尚未得到重启红态／绿态；先收尾原场景，再用 `-02` 新标签重跑。候选需先冻结成提交；脚本拒绝未提交的 src/app/tests 改动。每条命令使用新 label、外置盘输出目录和构建槽，不覆盖旧运行。执行主控先确认没有另一场隔离 Electron 验证同时运行；脚本只操作自己的 PID。


主控 #90 留下的两场先运行定向收尾（没有新 CLI、Electron 或模型回合，没有信号或强杀）：

```sh
python3 evidence/2026-10-16-batch16/T-096/cleanup_failed_01.py --label cleanup-b-01 --approval-ref '执行主控 T-096 #5：只收尾 red-b-01、tracer-b-01'
```

脚本只接受这两场固定夹具：`/private/tmp/t078-2-t096-bn5td39u` 的 67586／67659／67660，及 `/private/tmp/t078-2-t096-20qgx07u` 的 67769／67833／67839。两场均核对完才发送第一个 `daemon_stop`。它使用各自私有 operator 凭据访问已有 control.sock；停止前再次核对 PID、精确启动时间、完整命令和归属，任何不符就报 INCOMPLETE 并交回现场。

旧脚本没有落盘这六个进程最初的精确 lstart，因此收尾先用原启动／首屏记录限定出生时间，再与本次 preflight 的精确 lstart 逐字段复核。这个证据限制会保存在外置盘 preflight 中，不会补称为原先已记录。原 Electron 身份从它的 owner 文件及逐 PID 的原始 ps 输出回读；意外存活或身份不符同样停止。确认登记写入者全退出才移除临时 operator 凭据、复制到原外置盘 run 的 `fixture/` 并核对文件数／字节数，原夹具其余内容保留。旧 `.run.json` 不重写；新清单为 `<旧 label>-cleanup-b-01.archive.json`。

runner 修复：非阻塞 stdout 的 None／BlockingIOError 只表示暂时无数据，计划内 SIGKILL 的非零退出不再作异常；输出／布局诊断不能跳过 daemon_stop。身份或启动结果未知则不自动接管，摘要的 `handoff` 指向夹具、ownership.jsonl 和已有启动收据。停止回执不是退出证明；逐个 PID 与端点确认后才归档。所有新发现的写入者在故障注入前追加落盘身份。

每场预算及收尾规则写在 `run_restart.py` 开头。真实 Claude 版本配置为 2.1.302；不传模型提示词、不输入终端按键、不登录。三格为两个真实 Claude 主控，加一个受控 C receiver 替代 Codex 的 worker。杀掉本场 Electron、daemon、shell 与 CLI 后，第二次 Electron 不传 launch；窗格必须从保存集回来。worker 不启动第二个进程，其门禁 attempt 必须与重启前读回相等。

脚本通过 `controller_start` 创建启动记录；缺 argv 和错误版本在停止后的隔离 `launch_records` 中注入，不修改门禁拥有的 tasks/attempts；缺 session 保存原件后使目标不可用。恢复仍经过生产 daemon 入口，失败窗格须在真实 Electron 中只读显示“未恢复”，不能出现 `pane_restored` 事件。

零回合会话夹具：首轮 CLI 不提交请求。停止后脚本给每个原 session ID 放入一对明确标注为合成的历史 user/assistant 记录；它不是模型输出。第二轮须用完整原参数加原 session 选择器续接，macOS sysctl 读出的实际 argv 必须逐字段相等；Electron 终端须显示预置历史的 nonce。只出现 PID 或后台成功事件都不能通过。真实 CLI 可能停在初始化／信任屏；遇到这种情况保存原始输出并报 INCOMPLETE，不自动确认，不把屏幕当成已获批准。

以下 `CLAUDE` 请替换为主控已核对的实际 2.1.302 可执行文件绝对路径；不要用会随更新漂移的别名。`--approval-ref` 填本次主控运行授权位置。

先跑 main 红态和候选单格 Tracer bullet；单格成立后再跑三格和故障。示例：

```sh
python3 evidence/2026-10-16-batch16/T-096/run_restart.py --source /Users/luckye/Documents/Code/a2a --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/red-b-02 --label red-b-02 --approval-ref T-096-main-red --claude CLAUDE --claude-version 2.1.302 --panes 1 --expect-red
python3 evidence/2026-10-16-batch16/T-096/run_restart.py --source /Users/luckye/Documents/Code/a2a-wt-t096 --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/tracer-b-02 --label tracer-b-02 --approval-ref T-096-controller-tracer --claude CLAUDE --claude-version 2.1.302 --panes 1 --check-close
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
