# 主控 #351：09C 首启与阶段材料

状态：**静态准备 PASS；所有角色与业务动作未运行，launch NO_GO，批准待主控签字**。[最终静态原件](static-check-02.json) 核对 40 份命令文件、79 条命令/比较步骤，以及真实 B1 校验函数的内存批准夹具；未执行 B1 runner。首份 [01](static-check.json) 保留；首轮生成器给无工具 C-I4 多生成的两份许可读屏命令已移除，交接流程未使用、未运行，02 增加无工具阶段不得有许可命令的检查。冻结 312 个源码文件字节一致。本包复用已启动的 Stage A，root `/private/tmp/t078-2-09c-run-slm9wocj`，源码 `7a6edbff87df85077b3a05d38f3cfd5654cde9c1`，冻结包 `09c-executable-materials-02`，四份回归收据不变。Stage A 本次实际为 READY_FOR_APPROVAL、模型 0；不是 09C 全场通过。

以下路径相对于本票证据目录。命令文件是逐条执行的操作清单，**不得整份批量运行**；每条检查结果合格后再推进。输出已存在、任一身份/原屏/命令不符、任一额外 POST 或错误均停，INCOMPLETE，不重试业务动作或不确定的 Enter。

## 先完成两个角色，再开始计时

1. 主控签 `09c-c1-b1-ideation-p1-01/stage-b-approval.json`；逐条运行该目录 `B1-COMMANDS.txt` 的 dry-run、real。真实结果必须 PASS/cli_spawned，随后运行 `BIND-LAUNCH.txt`。它从实际结果绑定 manifest，不复制或假造 manifest。
2. 按同目录 `ONBOARD-COMMANDS.txt` 逐屏、逐键执行。每键前先完整读取当前原屏，再签 `onboarding/s*-*.json`：主题 ArrowUp→Auto、ArrowDown→Dark、Enter；Security notes 逐字符合 B1 的 `screen_text` 后 Enter（B1 plan 的 purpose 是 `security-notice`，真实 key 参数必须为 `onboarding-notice`）；信任屏 ArrowDown 到 Yes，再 Enter。禁 Digit1、默认 Enter 和批量按键。初读不符，用该步骤的 `-02` 命令只读重查，并把批准及 `--screen-file` 同时指向新原件，仍不符就停。若 key 已 written 而发键后 reader 因重绘拒绝，不再按一次；只另读下一屏确认，保留原 INCOMPLETE。
3. s13 必须为完整原屏、空提示符、manual mode。主控签 `readiness-template.json`（confirmed_by=executor、readiness=confirmed、basis 与 approval_ref 填实际读回依据），再运行 `READINESS-CONFIRM-COMMAND.txt`。命令验证完整分页/EOF、0 请求/响应/HTTP 原件、无提交事件，然后只写 readiness，不 release。采用 s13 `-02` 时，同步命令中的 screen 路径。
4. **ideation 首启结束后**，才对 executor 按同样流程运行其 `B1-COMMANDS.txt`、`BIND-LAUNCH.txt`、逐屏六键及 readiness。两角色启动步骤串行。本场必须先上线 executor；不能像 09B 一样在 stop 产生后才花时间 onboarding。
5. 两个实际 B1 均绑定后，运行本目录 `BIND-COMMAND-REFERENCES.txt`，把新增独立命令中的 LAUNCH_LABEL/LAUNCH_MANIFEST 替换为实际 manifest。然后运行 `09c-materials-01/BIND-OWNER-COMMAND.txt`，只读核对九进程并写 owner/target_identity（包含 target 原 attempt/fence/thread/native session/PID/lstart）；不得沿用 A16 身份。
6. 在计时前运行 ideation 的 `phases/C-I3/BUILD-COMMAND.txt`，准备唯一 slot 的 Electron build。该步骤不启动 Electron。目录若存在即停，不能覆盖构建 slot。主控逐份签两角色 `phases/*/approval.json`，逐条运行本目录 `ARM-ALL-COMMANDS.txt` 的五条 arm；arm 不发业务输入。本场只三次工具许可，所有 Bash input 必须为 command，不能用 argv 字段。

## 业务阶段顺序与预算

| 阶段 | 原生根来源 | 本阶段 POST | 许可 | 停止点/核对 |
| --- | --- | ---: | ---: | --- |
| C-I1 | 批准的 test-simulated-user 经 pane_dispatch/release | 2 | 1 | 真实 send 排队回执 → Stop/relay → stop delivered、created_at 原值；建立真实时钟起点 |
| C-E1 | 原 stop 的实际 inbox wake | 1 | 0 | 单条 SSE 持续等待，无工具、无 ack；C-I3 证据完成后才结束 |
| C-I2 | C-I1 的实际 delivered 执行反馈 | 2 | 1 | 真实 stop_too_early，年龄 <120000ms，目标无字节变化 |
| C-I3 | C-I2 的实际拒绝反馈 | 2 | 1 | 完整原屏/模板/身份匹配且真实时钟过门槛后，一个 Enter；实际 ideation 只中断一次 |
| C-I4 | C-I3 的实际执行反馈 | 1 | 0 | 只确认，Stop/idle，无新工具/ack |

合计 ideation **4 roots / 7 POST**，executor **1 root / 1 POST**，总 **5 roots / 8 POST / 3 许可，供应商模型 0**。每个实际 POST（含 409/CLI 自身重试）均计数，不能只数成功响应。global dispatch.seq、request/stop/permission ID 从实际登记、HTTP、hook、Stop/relay 取，不硬编码阶段序号。

## C-I1：先初始放行，再送一次请求

主控签完前述批准并核对准备齐全后，依次运行 ideation `phases/C-I1/INITIALIZE-COMMAND.txt`、`START-COMMAND.txt`：initialize 仅放行两个 unknown/空队列窗格，不发送；start 才派发一次已批准的完整文本（`09c-materials-01/i1-prompt.txt`），同时记为自动化 test-simulated-user。正文中的停止要求不冒称真实用户亲手输入。预计 Bash 命令见本目录 `TOOL-COMMAND-PREVIEW.json`；真正 tool_use/request ID 由现场生成。

Claude 到许可屏后运行 `OBSERVE-PERMISSION-COMMAND.txt`，应 READY_FOR_PERMISSION；运行 `PERMISSION-SCREEN-CMP-COMMAND.txt` 只读完整原屏并逐字节 cmp；运行 `PREPARE-PERMISSION-COMMAND.txt` 生成未签 permission。主控核对完整 Bash 命令、原 target、实际事件及 `❯ 1. Yes` 后签；先 `PERMISSION-CHECK-COMMAND.txt`，再 `PERMISSION-ENTER-COMMAND.txt`，一个 awaited Enter。输出为新的 execute-02，slot 带阶段/output/launch，不覆盖。成功后 settlement 应 PASS，原 stop delivered、无 ack、目标 delta 空，clock-origin 原件写成真实 wall/monotonic 起点。立刻运行本目录 `CONTINUED-DEMAND-COMMAND.txt`，只记录原批准持续有效，不执行 stop。

## C-I2、C-I3 与真实时钟

C-I2 只能观察原 delivered 反馈，不能重新 dispatch/release；同样执行 observe → 完整 screen/cmp → 生成未签 permission → 核对签字 → check → 单 Enter。必须在真实 stop 年龄 <120 秒内得到 stop_too_early、目标 delta 空。C-I3 由该真实拒绝自动触发，仍不新派发；尽早 observe、完整 screen/cmp 到下一许可屏。

运行 C-I3 `CONDITIONAL-ENTER-COMMAND.txt` 后，保留进程和它自己的 Electron 窗口。它会写 `execute-02-review/screen.bin`、完整分页 capture 与实际 `template.json`，在此等待主控签字，不默认放行。主控并行按 `REVIEW-AND-PUBLISH-COMMANDS.txt`：先复制真实 template 为未签草稿；核对实际 command/argv、stop_id/created_at/request_id、target 全身份、dispatch/global seq/prompt/tool_use/permission_event、窗口/input_generation、完整原屏后，只填草稿两个签字字段，再发布。发布命令先完整写完/flush/fsync，再用独占硬链接原子发布 approved.json，避免 driver 读到半份 JSON；不允许覆盖或更改其他字段。

前置契约见本目录 `C-I3-PREAPPROVAL-CONTRACT.json`。执行前 source、package、角色/native session、原 stop/目标、持续要求、无 ack、未消费 intent 均须一致。driver 在等待中读取真实 wall 与 monotonic；**wall age >120000ms 且从观察起 monotonic ≥120100ms** 才可按，自动开始最迟 130000ms，全场最迟 150000ms。按键前重新从 offset0 分页读完整输出/确认 EOF，所有当前原屏字节须等于已签原屏，实际命令/stop/目标/原屏/模板逐项一致；不完整、增长、时钟跳变、身份或选择变化、旧 intent、超过截止等任一不符即 INCOMPLETE、零新键。一次独占持久化 intent 后，经现有认证 Electron 窗口通路 awaited CR，记 action，不增业务根；写入未知不得再按。不得快进、改 created_at、operator 代 stop 或直接给目标发信号。

成功后只读 settlement 必须有原 stop、actual ideation emergency、实际事件年龄 >120 秒、目标相对 baseline 恰一个 Esc、无 ack、原 attempt/领导进程仍在；随后才解除 executor 单条 SSE 的 hold。运行 C-I4 `COLLECT-COMMAND.txt`，再 executor C-E1 `COLLECT-COMMAND.txt`，应均 PASS/Stop/idle，仍在 150 秒内。原件逐 POST/hook 继续保留；完整 raw 归档、逐成员字节读回、独立重数后才可另批回收，停机后不读 SQLite。

本交接未执行 B1 dry-run/real、读屏、按键、readiness、bind/owner、build、arm、初始化、业务阶段、HTTP 或真实时钟测试。所有模板仍空签。当前只有 Stage A 是实跑证据；09C 实际 CLI/Electron 时序和整票终审仍 **INCOMPLETE**。
