# T-096：执行主控真实重启验证

状态：**INCOMPLETE，脚本待运行**。候选需先冻结成提交；脚本拒绝未提交的 src/app/tests 改动。每条命令使用新 label、外置盘输出目录和构建槽，不覆盖旧运行。执行主控先确认没有另一场隔离 Electron 验证同时运行；脚本只操作自己的 PID。

每场预算及收尾规则写在 `run_restart.py` 开头。真实 Claude 版本配置为 2.1.302；不传模型提示词、不输入终端按键、不登录。三格为两个真实 Claude 主控，加一个受控 C receiver 替代 Codex 的 worker。杀掉本场 Electron、daemon、shell 与 CLI 后，第二次 Electron 不传 launch；窗格必须从保存集回来。worker 不启动第二个进程，其门禁 attempt 必须与重启前读回相等。

脚本通过 `controller_start` 创建启动记录；缺 argv 和错误版本在停止后的隔离 `launch_records` 中注入，不修改门禁拥有的 tasks/attempts；缺 session 保存原件后使目标不可用。恢复仍经过生产 daemon 入口，失败窗格须在真实 Electron 中只读显示“未恢复”，不能出现 `pane_restored` 事件。

零回合会话夹具：首轮 CLI 不提交请求。停止后脚本给每个原 session ID 放入一对明确标注为合成的历史 user/assistant 记录；它不是模型输出。第二轮须用完整原参数加原 session 选择器续接，macOS sysctl 读出的实际 argv 必须逐字段相等；Electron 终端须显示预置历史的 nonce。只出现 PID 或后台成功事件都不能通过。真实 CLI 可能停在初始化／信任屏；遇到这种情况保存原始输出并报 INCOMPLETE，不自动确认，不把屏幕当成已获批准。

以下 `CLAUDE` 请替换为主控已核对的实际 2.1.302 可执行文件绝对路径；不要用会随更新漂移的别名。`--approval-ref` 填本次主控运行授权位置。

先跑 main 红态和候选单格 Tracer bullet；单格成立后再跑三格和故障。示例：

```sh
python3 evidence/2026-10-16-batch16/T-096/run_restart.py --source /Users/luckye/Documents/Code/a2a --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/red-b-01 --label red-b-01 --approval-ref T-096-main-red --claude CLAUDE --claude-version 2.1.302 --panes 1 --expect-red
python3 evidence/2026-10-16-batch16/T-096/run_restart.py --source /Users/luckye/Documents/Code/a2a-wt-t096 --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/tracer-b-01 --label tracer-b-01 --approval-ref T-096-controller-tracer --claude CLAUDE --claude-version 2.1.302 --panes 1 --check-close
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
