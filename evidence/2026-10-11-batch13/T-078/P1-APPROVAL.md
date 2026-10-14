# T-078-2 P1 首次启动审批材料

**INCOMPLETE，待 P1 审批。** P0 已批准。本轮仅实现、生成材料并运行纯状态／静态检查：Claude CLI、API、socket、PTY、Electron、ps／信号运行均为 0，真实模型回合为 0。合流仍等 T-076-2。

## 完整材料

[approval.json](p1-materials-01/approval.json) 展开交互 argv、shell argv、环境白名单、hooks JSON、角色卡、UUID 和两项 preflight argv。[input.json](p1-materials-01/input.json) 保存启动输入；sources.tar.gz 包含精确新源码，candidate.diff 保存已跟踪文件差异。代码起点为 38a7eeed，本候选尚未提交，不能用起点代替新源码版本。control-plane.json 列出后台／API 环境及 argv。

隔离根为 `/private/tmp/t078-2-p1-0ek36x_v`，所有 state、repo、home、claude、tmp、shell、requests、manager-home 均在其下。launch 为 `b9ed5fb8-d97c-4487-8a68-dee96905b5e4`，native session 为 `5aba1c39-df7c-4aef-a746-eb044cd5c0f6`；thread 见 manifest。没有读取或复制用户认证。后台启动时生成临时 capability，不入证据；角色绑定于 launch，不能用参数选择。

这次审批须分别覆盖三项真实 Claude 进程调用：固定二进制 `/Users/luckye/.local/share/claude/versions/2.1.296` 的 `--version`、`--help`，以及 approval.json 的交互启动。版本必须为 `2.1.296 (Claude Code)`，所需选项必须存在。交互 argv 含 session-id、`claude-haiku-5-5`、`--effort low`、`--permission-mode manual`、实际 hooks、角色卡、空 strict MCP、Bash/Read、禁 slash commands；没有 --bare。

供 P1 明确审批的细化：`--settings` 用完整 JSON 参数，仅 hooks、无 permissions／认证覆盖；不另写设置文件。假 API 固定 `http://127.0.0.1:19178`，以便启动前展开准确环境；不同于 PLAN-2 的动态端口。端口冲突即停，不选备用、不替换服务。只绑定 loopback，不代理外部请求；假 key 为公开字符串 `a2a-fixture-key-not-a-secret`。服务验证该 key 但不保存任何认证头。

CLI 使用隔离 HOME／CLAUDE_CONFIG_DIR 和纯白名单，不继承用户 OAuth/API key、代理、父 worker 身份或 Git hooks。管理端与 API 使用隔离 manager-home、TMPDIR、operator 凭据路径和夹具 Git 环境，具体固定值见 control-plane.json；不 source 身份文件、不写 Git 配置。API argv 精确为 `/usr/bin/python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/workbench/tests/t078_fake_messages.py /private/tmp/t078-2-p1-0ek36x_v`。

## P1 生命周期与明确停点

首次启动阶段：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-launch-01
```

核对输入和源码快照，执行两项 CLI preflight，启动 API／隔离后台／一个构思主控 CLI，然后以 **INCOMPLETE／等待初始 readiness 确认** 返回。阶段不发送输入，不自动答 onboarding、信任或权限提示。输出在 p1-materials-01/launch/；实时原始终端为隔离根 `state/traces/<launch>/pty.raw`，API／后台日志也在该根。

主控检查实际隔离终端，确认确实可接新输入后，才在根目录写 `initial-ready.json`：launch/session 匹配上述 UUID，confirmed_by 为 executor、readiness 为 confirmed、basis 记录实际确认依据。若有登录、未批准的 onboarding／信任／权限要求，停止并报告，不写 ready，不把探针文字或 Enter 当作答复。缺少明确确认时 continue 拒绝。

在同一已批准 CLI 中放行唯一输入，**不再启动 Claude**：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-continue-01
```

通过生产 pane_release／pane_dispatch 登记后写 bracketed paste 和独立 CR。准确输入见 nonce.txt；真实 CLI 发 UserPromptSubmit，假 API 持有响应。检查 backend busy、实际请求与 hook 后，放开一次 text SSE；真实 Stop 才结束唯一提交。核对一次 pane_idle、原始 PTY nonce 回复，保存 hook 原始 stdin、请求体与 SSE。不虚构原生 turn id。turn_limit=1 阻止第二次提交；多回合匹配仍待真实 payload 证据，不算本轮已完成。

预算：1 次根输入，最多 1 次 Messages，另允许 count_tokens；真实模型调用 0。API 屏障 60 秒，观察期限各 30 秒，preflight 各 15 秒。异常退出、payload 不匹配、额外 Messages／未知 endpoint／错误认证／权限等待即停，原件保留、无重试。服务响应中的 Haiku 字段是夹具数据，不证明真实模型运行。

最后清理本次生命周期：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-cleanup-01
```

后台收尾并停止自己的 PTY；API 核对保存的 PID／命令后才停止。不能核对就不发信号。后台确认退出后删除本次 operator 凭据、归档 fixture，再删除仅本次根。失败或未确认退出时保留目录。不碰用户 HOME、正式后台、Herdr 或外部 listener。所有 API／CLI／socket／ps／信号均只在这三个审批后的沙箱外阶段运行。

## 已有证据与剩余范围

- p1-state-red-01：缺主控运行入口，Claude hook 误走 Codex 日志扫描；身份检查只是下游不可达，不算身份规则业务红态。
- p1-state-green-01：3 项纯状态检查通过；真实 CLI 的 hook 形状仍待 P1。
- p1-bad-session-01：单处去掉 native-session 检查的坏实现，只让对应拒绝断言失败；这是纯状态反例，不是 CLI 认证证据。
- p1-static-regression-01 2/2，p1-worker-state-regression-01 11/11；未重跑 8/9/18，未启动 reviewer。
- 本轮未实现 controller inbox、多回合、主控窗口输入或双主控；留待 P2～P4，不提前启动真登录。假服务与真模型证明分开报告。

重放纯检查：`node workbench/tests/test_t078_claude_signals.ts <新目录>`；骨架／worker 状态分别用 test_t078_controller_plan.ts、test_t078_pane_runtime.ts。纯构造材料命令为 `node workbench/tests/prepare_t078_p1.ts /private/tmp/t078-2-p1-0ek36x_v`；必须先保留旧 approval 原件，获批后不得改材料。单文件 >5 MiB 时仍按规则外置归档。
