# T-078-2 P1 刷新材料（主控 #84）

2026-10-13。**INCOMPLETE，等待审批，未启动 CLI、API 或 socket。** Worker 已续接为 s13-t078s，按主控记录请求 gpt-6.1-sol/xhigh、service_tier=default；不申请 Fast。旧 p1-materials-01、P1-APPROVAL.md 及其原始静态结果保留，只能作为过期记录，不能执行旧启动脚本。

## 新实例和启动配置

材料目录 `p1-materials-02/`；根 `/private/tmp/t078-2-p1-02-dcmlidc0`。launch 为 `f135697a-cf77-4cc0-9ba2-8c8e759f6b0c`，native session 为 `85bad1c6-63a3-41dc-af66-d47c9cab2100`；thread、角色卡、完整 argv/env/hooks 在 [approval.json](p1-materials-02/approval.json)，输入模板在 [input.json](p1-materials-02/input.json)。旧实例根确实不存在，旧身份没有复用。

固定 CLI、两项 preflight、交互参数、隔离 HOME/CLAUDE_CONFIG_DIR、公开假 key、单提交预算和初始 readiness 人工确认均沿用 P1 范围。`--settings` 为仅含 hooks 的 JSON，无 permissions／认证覆盖，不用 --bare；真实登录仍未进入。审批分别覆盖固定 Claude 2.1.296 的 --version、--help 和该份交互 argv。模板没有可用于实际启动的端口。

## 启动时分配端口

1. 模板 api_url 为 `http://127.0.0.1:0`；API 实际执行 `HTTPServer(('127.0.0.1', 0), ...)`，由操作系统分配空闲端口。此时没有 Claude 进程。
2. API 将 host、实际 port、api_url、自己的 PID、launch/session 完整写入临时文件后原子发布 `api-ready.json`，不覆写已有收据。
3. runner 对照已记录的 API 子进程 PID 与本次 launch/session 核对收据，只允许模板的 api_url 改成这个 loopback endpoint。错误 PID、身份、host、port 或 URL 均停止。
4. 在隔离根追加 `runtime-input.json`，通过纯构造器生成 `p1-materials-02/launch/runtime-manifest.json`。它包含真正的完整 argv/env/hooks；argv 和 settings 必须与审批模板一致，环境只有 ANTHROPIC_BASE_URL 可以改为刚分配的地址。
5. 实际 manifest 保存且核对完毕后，才依次执行 CLI --version、--help 与交互启动；后台 controller_start 显式拒绝端口 0，并且不写启动记录、不调用 PTY。

启动模板不会被改写。continue 再核对 runtime-input、API 收据与实际 launch manifest，防止后续指向别的服务。所有端口分配、网络与进程步骤只在主控运行的沙箱外阶段发生；本轮纯检查没有绑定端口。源码包及 control-plane.json 包含准确的 API/driver argv、管理端环境和允许的动态字段。

## 新阶段名

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-launch-02
```

这个阶段只启动并观察，返回 INCOMPLETE／等待初始 readiness；不发送探针输入，不自动答 onboarding、信任或权限。输出在 p1-materials-02/launch/；实时 PTY 仍在该隔离根 state/traces/<launch>/pty.raw。若旧根消失、输入或源码变化，先失败，不能自己重新生成身份然后启动。

主控确认实际 CLI 可接新输入后，写该根 `initial-ready.json`：launch/session 必须匹配，confirmed_by=executor、readiness=confirmed，basis 填实际确认依据。出现登录或未批准启动／权限对话则停止，不用提示词或 Enter 答复。然后在同一 CLI 上执行：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-continue-02
```

准确输入见 nonce.txt。最多 1 次根输入和 1 次 Messages 请求，另允许 count_tokens；假 SSE 不证明模型行为。API 屏障 60 秒、观察期限各 30 秒、preflight 各 15 秒。任何非预期结果停止，原件保留、无重试；真模型回合预算仍为 0。

成功或中止后，核对并停止自己的后台／PTY/API，确认退出后删除本次 operator 凭据、归档 fixture，再删除仅本次根；无法核对或协议失败时保留现场：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-cleanup-02
```

## 本轮证据与复现

`p1-port-red-02` 在旧产品入口观察到端口 0 先写 launch、后尝试 PTY；抛错替身阻止了实际 PTY/CLI。加检查后 `p1-port-green-02` 证明 0 次 PTY 调用、0 条 launch；这是产品入口纯隔离红绿，不是网络验证。`p1-endpoint-static-02` 用两个外部给定端口及六项身份/地址反例验证绑定，另检查忽略 ready 收据的已知坏行为；不外推为实际 API 启动。

重放均须新输出目录：

```sh
node workbench/tests/test_t078_p1_port_guard.ts <新目录>
python3 -B workbench/tests/test_t078_p1_endpoint.py --output <新目录>
node workbench/tests/test_t078_claude_signals.ts <新目录>
node workbench/tests/test_t078_controller_plan.ts <新目录>
node workbench/tests/test_t078_pane_runtime.ts <新目录>
```

复现生成流程用 `python3 -B workbench/tests/regenerate_t078_p1.py --label p1-materials-03`；必须换 label，不能覆写材料 02 或旧结果，新实例也须重新审批并换阶段名。材料 02 在本轮静态准备步骤中生成；该脚本保存同一生成流程。源码快照、差异、静态检查和实例更新记录都在新材料目录。未重跑 8/9/18、未开新审查、未合流；本卡其余 P2～P4 仍待 P1 真实协议证据。
