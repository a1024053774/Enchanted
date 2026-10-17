# P1 材料 06：隔离假服务改用 Bearer 认证

2026-10-13，依据主控 #94 与 [决定 04 更新原文](controller-decision-04-update-94.md)。**认证构造／语法检查 PASS；完整准备 INCOMPLETE（旧归档待外置），新认证的真实 CLI 验证待审批。** 本轮没有启动 CLI、API、PTY、ps、信号或模型。真登录复核仍用用户平常的登录，认证与预算不变。

## 官方依据与选择

| 方式 | 文档合同与本次取舍 |
| --- | --- |
| `apiKeyHelper` | [官方参考](https://code.claude.com/docs/en/settings-reference#apikeyhelper) 支持命令输出凭据，发送到 X-Api-Key 与 Authorization 两个头；来自 project/local 设置的命令在交互模式受目录信任约束。本实例的隔离用户设置可配置公开假 key helper，但增加命令执行与输出合同，固定版本的实际效果仍需探针。本次不实现或尝试 |
| `ANTHROPIC_AUTH_TOKEN` | [官方网关连接说明](https://code.claude.com/docs/en/llm-gateway-connect#conflicts-with-an-existing-login) 明确该变量立即接管认证，而交互 API_KEY 要先批准；同页给出 [BASE_URL 与 token 配合](https://code.claude.com/docs/en/llm-gateway-connect#set-the-base-url-and-credential) 的 CLI 配置。本次选择它，无 helper 命令、无内部状态预置 |

[环境变量参考](https://code.claude.com/docs/en/env-vars) 定义 AUTH_TOKEN 为 Bearer 头、BASE_URL 为 API 地址覆盖；[认证优先级](https://code.claude.com/docs/en/authentication#authentication-precedence) 将该 token 排在 API_KEY 与 helper 前。由此选择文档化的免 API_KEY 批准路径；**固定 Claude Code 2.1.296 是否实际发出请求，仍待 launch／continue，不能由文档或纯检查替代。** 依据索引见 [p1-auth-choice-06.json](p1-auth-choice-06.json)。

本次只在已有假服务 profile 把 `ANTHROPIC_API_KEY` 移除，改为 `ANTHROPIC_AUTH_TOKEN=a2a-fixture-key-not-a-secret`。它是公开夹具字符串，不是真登录或 OAuth token。假 API 只接受 `Authorization: Bearer` 的该值，拒绝缺 token、错 token 或同时带 X-Api-Key；没有兼容或兜底认证路径，不记录原始 headers，不代理外部 API。

## 原失败与本次证明边界

continue-05b 已登记并提交 nonce，但 CLI 报未登录，假 API 没收到请求，期限到即停。原 [result](p1-materials-05/continue-05b/result.json)、traceback、PTY 和归档保留；结合官方 API_KEY 批准合同解释此失败，没有读取内部批准状态或按键通过提示。[cleanup-05b](p1-materials-05/cleanup-05b/result.json) 核对记录 CLI PID 50901 已退出才 PASS，主控报告无残留。原实例已清理，不能复用，因此本次必须用新实例。

本次静态合同先红后绿：profile 原来缺 Bearer 且保留 API_KEY；原假 API 拒绝正确 Bearer，却会实际记录仅 API key／错 Bearer 配旧 key／混合认证的请求。候选接受唯一正确 Bearer，拒绝其余三项。

- [profile 红态](p1-auth-profile-red-06/results.json)／[绿态](p1-auth-profile-green-06/results.json)：调用真实纯启动构造器，2 项；没有启动 vendor CLI。
- [handler 红态](p1-auth-handler-red-06/results.json)／[绿态](p1-auth-handler-green-06/results.json)：真实 POST 方法、内存字节流、4 项，拒绝项无请求记录；没有 HTTP socket 或真实 CLI。
- [bootstrap](p1-bootstrap-final-06/results.json)：新实例的 theme／IS_DEMO／未预置内部状态，3 项。

这是新认证合同的静态红绿，不把旧 X-Api-Key 夹具在原合同下的行为称为产品缺陷；也不把 handler 内存流通过称为真实 HTTP、CLI 认证、hooks 或主控链路通过。

## 完整启动材料与新停点

实例根 `/private/tmp/t078-2-p1-06-54dai8pv`；task `t078-p1-06`，launch `b2b531c2-9e30-4b4d-a076-c9ef84164479`，session `ad43fce1-0d01-47db-8492-31a7c932245c`，thread `5477e304-44c0-4ade-9d14-4789f9084cb4`。HOME、CLAUDE_CONFIG_DIR、repo、state、tmp、shell、requests、控制端 HOME 全在新根内，不继承父进程真实凭据或 A2A 身份。

准确 argv、shell argv、白名单 env、角色文本、三个 hooks 及 --version／--help 预检见 [approval.json](p1-materials-06/approval.json)。控制端／API 的准确 argv/env、继续阶段 argv、端口和预算见 [control-plane.json](p1-materials-06/control-plane.json)。隔离 [settings](p1-materials-06/isolated-settings.json) 仍仅 `theme: dark`；`--settings` 仍只含三个 hooks，不含 helper、权限或认证覆盖。后台生成本 launch 的私有 capability，不公开入证据，不读或复制用户认证。

除新实例身份、引用路径与 nonce 外，相对材料 05 的 CLI argv、model Haiku 5.5、effort low、manual 权限、工具 Bash/Read、空 MCP 和角色卡均不变，环境唯一认证差异是 API_KEY → AUTH_TOKEN。保留 IS_DEMO=1；不用 --bare，不换 CLI 2.1.296，不登录，不写未文档化内部状态。差异与当前静态检查见 [p1-preparation-check-final-06.json](p1-preparation-check-final-06.json)。

API 仍在启动时绑定 127.0.0.1:0，保存实际端口、PID 和身份，再生成 runtime manifest 才启动 CLI；不预占固定端口。候选由 [source-files](p1-materials-06/source-files.json) 与 [source snapshot](p1-materials-06/sources.tar.gz) 绑定，HEAD `38a7eeed9db48ca114b5d9ac747028d712e60468` 不单独代表未提交的 P1 源码。

本次只请求 **p1-launch-06**，输入预算 0、真实模型预算 0，停在初始屏幕观察点。该阶段先按本卡规则归档 cleanup-05b 的 8,028,610 字节 fixture.tar.gz 到 `/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/p1-materials-05/cleanup-05b/fixture.tar.gz`，逐字节读回后才移除仓库原件，留下 summary 与 manifest。随后运行完整静态检查，写材料 06 的 prelaunch-check.json；任一步未通过都不会启动 API 或 CLI。当前 [静态报告](p1-preparation-check-06.json) 的失败仅为此超限原件；原报告保留，修改启动前归档后的未运行草稿也保留在 p1-materials-06-before-archive，不复用其实例身份。

任何 key、helper 执行、目录信任或权限提示都停并保存原文，不按键或选默认；版本／身份／协议异常不重试。原文在 `<根>/state/traces/<launch>/pty.raw`，launch result 保留原始字节 base64。

continue／cleanup 要读回后单独审批，不自动调用。continue 的 [readiness-template.json](p1-materials-06/readiness-template.json) 是 **unconfirmed**，不是批准：主控观察本次新实例后，将其另存为材料目录 readiness.json，填入本 launch/session 的 `confirmed_by: executor`、`readiness: confirmed` 与实际观察／批准依据，再审批 `p1-continue-06`。旧 05 的确认不能复用。最多发送原 nonce 一次、接收一条脚本化 Messages SSE；仍是 0 个真实模型回合。

cleanup 保留已真实复验的退出检查：关联本次 process-manifest 的实际 CLI PID／启动时间／命令，确认退出前不 PASS 或删根；最多观察 15 秒，仍活着或身份未知则 BLOCKED。仅核对并停止自己的 API，不额外 kill CLI；失败现场不覆盖。

## 命令

请求执行主控审批并在沙箱外运行：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-launch-06
```

静态产物重放用新标签／新输出，不覆盖已有证据：

```sh
python3 -B workbench/tests/regenerate_t078_p1.py --label p1-materials-<新编号> --extra-source evidence/2026-10-11-batch13/T-078/p1-check-materials-06.py
node workbench/tests/test_t078_p1_auth.ts /绝对路径/新的profile检查目录
python3 -B workbench/tests/test_t078_p1_bearer.py --output /绝对路径/新的handler检查目录
node workbench/tests/test_t078_p1_bootstrap.ts /绝对路径/p1-materials-06 /绝对路径/新的bootstrap检查目录
python3 -B evidence/2026-10-11-batch13/T-078/p1-check-materials-06.py --output /绝对路径/新的静态报告.json
```

本次未运行新 CLI 或 fake API。假服务链路、真登录复核、三窗格与最终合流仍待后续分开取得证据，整票仍 INCOMPLETE。
