# A-15 executor B1 与逐屏材料

材料 PASS；本轮只有文件生成和静态检查，没有运行 executor B1 dry-run/real、screen/key、observe、release 或业务命令。

先以 `1aded2e073d959457233a4ee06351f0b76fa8788` 提交主控 #327 产出的 readiness、I1 dispatch/permission/execute 与签字件，九项尾注齐。I1 原件为 READY_FOR_EXECUTOR：实际 dispatch `c9f2322a-0526-4430-a3d6-98b376b8b140`、全局 seq=2、实际 request `80ef9485-80df-43f3-9791-bab43261cb5b`，stop `c3ab1493-5c73-4af5-947f-a0f16f19d6c7`（ideation→executor），pending=true、feedback_count=0、target_byte_count=0、Messages=2；Enter 为 action/control 记账。stop.created_at 为 `2026-10-16T10:51:40.728Z`，后续不能重置。

本次执行既有 ROLE-MATERIAL-COMMANDS 第二条，只生成 `09b-a15-b1-executor-p1-01`。生成器先核对 I1 结果及真实 relay pending 行，再写 executor 的独立 HOME/config/tmp/shell/requests/hooks/user-data、角色文件和 plan；静态构造 helper 不启动角色/API/daemon。新 launch=`3e63bc20-ec07-4237-b7ec-a8381f5a57ec`、session=`85c321f3-35c7-4504-9513-73481644652a`、thread=`7c8812a5-847a-49fb-bafc-7d5a18c84962`，target binding 仍逐项取 A-15 Stage A readiness。

主控后续按以下顺序逐项执行，不能把命令文件整份批量运行：

1. 核对并签 executor P1 的 `stage-b-approval.json`（两个签字字段当前为空）。复用同一 executor API：保存的 Stage A readiness 为 PID 59388、端口 64829；input.api_url 保留 `http://127.0.0.1:0`，真实 B1 必须重新核对完整 argv/PID/lstart/ready。本次只检查保存文件，不声称进程存活身份已重新核对。
2. `B1-COMMANDS.txt` 第一条只 dry-run，预期 READY_FOR_ROLE/spawned=false；读回后再决定 real 第二条，只启动 executor 到启动停点。两个输出分别为 `09b-a15-b1-executor-01-dry-run`、`09b-a15-b1-executor-01`，均尚不存在。ideation 首启已经完成，I1 已结束；本次不并行启动角色。
3. real 成功后才运行文件步骤 `BIND-LAUNCH.txt`，从实际成功 B1 结果取得 manifest/launch label；如果主控改用 -02 等新 launch 输出，须先把此文件的 `--result` 指向实际结果。当前 ONBOARD-COMMANDS 保留 LAUNCH_LABEL，不能原样执行，也不能拿 ideation manifest 代替；bind-launch 后再逐条执行。
4. `ONBOARD-COMMANDS.txt` 提供每屏初读与 -02 备用重读、六键和六条观测；六份空签字草稿在 `onboarding/`。主题 ArrowUp→Auto、ArrowDown→Dark、Enter；Security notes 核对后实际 key purpose 为 onboarding-notice；trust ArrowDown 到 Yes 再 Enter。B1 冻结 screen plan 仍是 security-notice + 完整 screen_text，与 runner 一致。若初读不符，只用新 -02 重读，不发键；采用 -02 时批准中的 screen_file 与 key 命令一起绑定该原屏。
5. **每个键后、下一键及初始 release 之前**，运行紧随该键的 observe-startup-queued 命令，expected-keys 从 1 至 6，固定读取本次原 I1 execute-02。它经真实 inbox_list 刷新原条目，要求 state=queued、历史无 delivered、无 I2、pane unknown/active=null、同一队列、业务写出=0、executor POST=0、原 entry.created_at 不变；任一失败立即停，不签下一键。首启键写出不等于业务投递。
6. 六项观测全 PASS、s13 为 manual 空提示符后停下；本包不自动确认 executor readiness、不 arm I2、不 initial release。后续必须按 PLAN 第 6 步先预批原 I2，再 release 原排队 stop；只有真实 turn_submitted 才可 delivered。

角色预算仍为 ideation 4 roots/6 Messages、executor 6/11、合计 17，供应商模型 0。当前已实跑的 I1 占 ideation 1 root/2 Messages；本轮文件生成不消耗 executor 回合。P1 的其他 E 阶段草稿由同一生成器产生，仍未签，不授权运行。

静态检查区分当前输入与未来产物：runner、prepare、observe、readiness、I1 收据、角色配置和两份命令的输入路径存在；新输出均不存在；screen.bin、实际 executor manifest 和 launch-binding 只能在后续真实阶段产生，未造占位文件。后续真实 HTTP/CLI/onboarding/queued 观测仍 INCOMPLETE／未运行。
