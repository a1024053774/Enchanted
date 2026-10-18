# T-096：执行主控真实重启验证

2026-10-18 审查后补充：旧候选 `11b32303b` 的独立审查为 NO_GO，缺陷是明确关闭最后一格后重开会重新选择 worker。修复后的 `d61876fe2` 已由主控完成 `empty-reopen-b-01`：**PASS（31 项实跑，cleanup true，模型／POST 0）**；两主控初始化由主控逐屏批准。该标签及输出目录不得重用。新候选待独立审查 02／门禁验收；下文七场 PASS 只描述旧候选的已跑范围，逐场适用性与四个产品文件的差异见 RESULTS 最新段。

新边界入口（仅执行主控运行，先冻结代码；标签须全新）：

```sh
sh evidence/2026-10-16-batch16/T-096/RUN-EMPTY-LAYOUT.sh /已核对的绝对路径/claude-2.1.302 本次运行授权位置 empty-layout-b-01
```

启动及收尾沿用下文逐屏批准流程；不复用旧批准。脚本跑三格恢复并保留两个主控历史／实际 argv 和 worker 未恢复的核对，然后点击三个“关闭窗格”，正常退出第二个 Electron，确认退出才启动第三个（不传 `--launch`），后台保持运行。必须同时读到第三个真实窗口的空状态、空 pane key／DOM、后端 saved=true 且 panes=[]，以及无新增打开／凭据／恢复事件、完整 task 不变。新增原件为 `empty-layout-before-reopen.json`、`empty-reopened-view.json`、`empty-layout-after-reopen.json` 和 window-3；任何退出不明均保留现场，不再发退出请求。预算：两主控各启动及续接一次、一个受控 worker receiver、两个后台 epoch、三个串行 Electron，模型／POST 0；每个主控六键及一次就绪放行仍需逐屏批准，不截屏。运行完成须检查 `<新标签>.run.json` 的业务检查、fake_posts=0、cleanup_complete=true 和对应归档清单，不能只看退出码。

`REVIEW-OUTSIDE-01.sh` 是 reviewer 对固定旧 SHA 的合同复现脚本，原文保留，预期仍是 NO_GO／退出 1；它不启动真实 Electron，不用于给新候选判绿。

状态：**PASS（本票实跑）**。主控 #107／#15 确认 red-b-05、tracer-b-05、three-b-01、no-argv-b-02、version-b-02、no-session-b-01、isolation-b-01 全部通过，失败现场也已清理归档。候选冻结待独立审查，详见 `REVIEW-REQUEST-T096-01.md`；以下命令仅保留为复现说明，不重跑已有标签／输出目录。任何经主控安排的新场景仍须逐屏批准、模型预算 0，同一时刻最多一个 Electron。

候选先冻结成提交；新 label／外置盘输出／构建槽不覆盖旧运行。`--expect red|restore` 现在必填，漏传会在资源启动之前退出。red 模式保留死端点去测试真实重启，不预先删除端点掩盖缺陷；仅识别原件中明确的、发生在新凭据和进程创建之前的拒绝。超时、其他报错或新 epoch 身份不明仍为 INCOMPLETE。

两场 `-02`、red-b-03 和 red-b-04 的固定归档均已完成，不重跑已有归档。清单明确排除死 socket 与私密 operator 凭据，其余文件核对数量／字节／路径和 symlink 原始目标，原件保留。

restore 模式先完成真正的原生引导：runner 输出一条 `WAITING_FOR_STARTUP_APPROVAL` 和 context 路径，在声明期限内等执行主控逐屏批准。原 `workbench/README.md` 要求“启动、每屏明确按键、continue、cleanup 分别审批”；本流程没有预先批准 Enter，也不写 hasCompletedOnboarding 或 trust 内部标志。按键只走现有 `pane_screen_key`，一次批准一个原始屏幕。

每场预算及收尾规则写在 `run_restart.py` 开头。真实 Claude 版本配置为 2.1.302；不传模型提示词、不登录。restore 首轮每个主控至多六个逐屏批准的初始化键，以及一次空队列的就绪放行；red 不发键。三格为两个真实 Claude 主控，加一个受控 C receiver 替代 Codex 的 worker。杀掉本场 Electron、daemon、shell 与 CLI 后，第二次 Electron 不传 launch；窗格必须从保存集回来。worker 不启动第二个进程，其门禁 attempt 必须与重启前读回相等。

脚本通过 `controller_start` 创建启动记录；缺 argv 和错误版本在停止后的隔离 `launch_records` 中注入，不修改门禁拥有的 tasks/attempts；缺 session 保存原件后使目标不可用。恢复仍经过生产 daemon 入口，失败窗格须在真实 Electron 中只读显示“未恢复”，不能出现 `pane_restored` 事件。

零回合会话夹具：首轮 CLI 不提交请求。停止后脚本给每个原 session ID 放入一对明确标注为合成的历史 user/assistant 记录；它不是模型输出。第二轮须用完整原参数加原 session 选择器续接，macOS sysctl 读出的实际 argv 必须逐字段相等；Electron 终端须显示预置历史的 nonce。只出现 PID 或后台成功事件都不能通过。真实 CLI 可能停在初始化／信任屏；遇到这种情况保存原始输出并报 INCOMPLETE，不自动确认，不把屏幕当成已获批准。

以下 `CLAUDE` 请替换为主控已核对的实际 2.1.302 可执行文件绝对路径；不要用会随更新漂移的别名。`--approval-ref` 填本次主控运行授权位置。

先跑 main 红态和候选单格 Tracer bullet；单格成立后再跑三格和故障。示例：

```sh
python3 evidence/2026-10-16-batch16/T-096/run_restart.py --source /Users/luckye/Documents/Code/a2a --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/red-b-05 --label red-b-05 --approval-ref T-096-main-red --claude CLAUDE --claude-version 2.1.302 --panes 1 --expect red
python3 evidence/2026-10-16-batch16/T-096/run_restart.py --source /Users/luckye/Documents/Code/a2a-wt-t096 --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/tracer-b-05 --label tracer-b-05 --approval-ref T-096-controller-tracer --claude CLAUDE --claude-version 2.1.302 --panes 1 --expect restore --startup-wait-seconds 600 --check-close
python3 evidence/2026-10-16-batch16/T-096/run_restart.py --source /Users/luckye/Documents/Code/a2a-wt-t096 --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/three-b-01 --label three-b-01 --approval-ref T-096-controller-three --claude CLAUDE --claude-version 2.1.302 --panes 3 --expect restore --startup-wait-seconds 600 --check-close
```

单格 tracer 命令会先停在引导等待。让该命令保持运行，在另一个主控终端读取打印出的 context（例如外置盘 `tracer-b-05/ideation.startup.json`），执行：

```sh
python3 evidence/2026-10-16-batch16/T-096/startup_controls.py capture --context /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/tracer-b-05/ideation.startup.json --name theme-auto-01
```

capture 输出 `.screen.json`、仅供查看的 `.txt`、原始 `.raw` 和批准模板。执行主控读取实际屏幕，将模板另存为本次批准文件；逐字填入 approved_by=`executor`、本次 approval_ref、具体 basis，以及本屏的 key／purpose／selected_label。模板默认均为空，不产生批准。只有核对过当前原始屏幕后才能执行：

```sh
python3 evidence/2026-10-16-batch16/T-096/startup_controls.py key --screen SCREEN_JSON --approval-file 本次已填写的批准文件.json
```

每按一键重新 capture，使用新 name／新批准文件。现有门禁允许的初始化顺序如下；本表是操作清单，不能替代当前屏幕批准：

| 次序 | purpose | key | selected_label |
| --- | --- | --- | --- |
| 1 | onboarding-theme | ArrowUp | Auto (match terminal) |
| 2 | onboarding-theme | ArrowDown | Dark mode |
| 3 | onboarding-theme | Enter | Dark mode |
| 4 | onboarding-notice | Enter | Press Enter to continue… |
| 5 | workspace-trust | ArrowDown | Yes, I trust this folder |
| 6 | workspace-trust | Enter | Yes, I trust this folder |

遇到不同文字、拒绝、登录或其他未批准屏幕，保存原始字节，停止按键，不换 purpose 或标志来绕过。runner 到期会收尾并报 INCOMPLETE。

trust-Enter 后重新 capture（例如 name=`prompt-ready-01`），实际看到原生输入提示符且没有待处理引导后，填写另一份就绪批准：保留该模板中的 launch／session／directory／screen_id／screen_file，填写 approved_by=`executor`、本次 approval_ref 和具体 basis，并新增 action=`startup-ready`。key／purpose／selected_label 保持空。这一步沿用现有 `pane_release`，要求队列、active、writing 和用户草稿均为空，原始屏幕仍与批准相同；不写入终端键或模型提示词。执行：

```sh
python3 evidence/2026-10-16-batch16/T-096/startup_controls.py ready --screen 就绪屏幕.screen.json --approval-file 本次就绪批准.json
```

runner 必须同时读到 trust-Enter 写入事件和其后的 initial_release 才继续故障注入。这只是测试前置条件，最终仍要求实际进程 argv 逐字段相同、Electron 终端出现同一历史 nonce、fake POST 0。三格时 ideation 完成后依次等待 executor 的 context；每个 profile 各自批准，不能复用另一场批准。

三个故障各用独立场景；最后一场同时验证一个主控失败、另一个主控继续恢复，worker 仍未恢复、attempt 不变：

```sh
python3 evidence/2026-10-16-batch16/T-096/run_restart.py --source /Users/luckye/Documents/Code/a2a-wt-t096 --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/no-argv-b-01 --label no-argv-b-01 --approval-ref T-096-no-argv --claude CLAUDE --claude-version 2.1.302 --panes 1 --expect restore --startup-wait-seconds 600 --fault missing-argv
python3 evidence/2026-10-16-batch16/T-096/run_restart.py --source /Users/luckye/Documents/Code/a2a-wt-t096 --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/version-b-02 --label version-b-02 --approval-ref T-096-version --claude CLAUDE --claude-version 2.1.302 --panes 1 --expect restore --startup-wait-seconds 600 --fault version-mismatch
python3 evidence/2026-10-16-batch16/T-096/run_restart.py --source /Users/luckye/Documents/Code/a2a-wt-t096 --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/no-session-b-01 --label no-session-b-01 --approval-ref T-096-no-session --claude CLAUDE --claude-version 2.1.302 --panes 1 --expect restore --startup-wait-seconds 600 --fault missing-session
python3 evidence/2026-10-16-batch16/T-096/run_restart.py --source /Users/luckye/Documents/Code/a2a-wt-t096 --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/isolation-b-01 --label isolation-b-01 --approval-ref T-096-isolation --claude CLAUDE --claude-version 2.1.302 --panes 3 --expect restore --startup-wait-seconds 600 --fault missing-argv
```

输出与收尾：原始命令、argv、三份 snapshot、门禁 task 前后读回、API 请求和 Electron 事件保存在外置盘。仓库只写 `<label>.run.json` 摘要和 `<label>.archive.json` 清单。退出和身份无法核对时不归档，保留现场，按摘要中的 PID/路径由执行主控处理。正常结束时核对全部登记写入者退出，先删除本场临时 operator 凭据（不归档凭据内容），再复制夹具并比较文件数、字节数；其余原件保留。
