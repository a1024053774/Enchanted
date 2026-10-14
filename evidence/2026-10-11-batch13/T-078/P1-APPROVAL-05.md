# P1 材料 05：仅预置主题与 onboarding 开关

2026-10-13，依据主控 #91 和 [决定 04 更新原文](controller-decision-04-update-91.md) 末节。**材料静态检查 PASS；真实运行 INCOMPLETE／待启动审批。** 本次没有启动 Claude、API、PTY 或模型；旧材料与失败原件保留，blocking issue `20261013T154915Z-worker:s13-t078s-issue-001` 未自行关闭。

## 审批范围与唯一配置差异

请求批准 **p1-launch-05**：固定 Claude Code 2.1.296 连接隔离假 API，停在初始屏幕观察点。输入预算 0，真实模型预算 0，不运行 continue。相对材料 03，除新实例身份与引用路径外，argv、角色文本、model/effort、权限、工具、MCP 和三个 hooks 不变。仅新增：

- 白名单环境 `IS_DEMO=1`。[官方环境变量](https://code.claude.com/docs/en/env-vars) 说明其可跳过 onboarding，并隐藏邮件地址／组织信息；在固定 CLI 上的实际效果待探针验证。
- 隔离 `claude/settings.json` 内容仅为 `{"theme":"dark"}`。[官方 theme 参考](https://code.claude.com/docs/en/settings-reference#theme) 允许在 settings.json 设置该主题；副本是 [isolated-settings.json](p1-materials-05/isolated-settings.json)，runner 在启动 API 前核对字节与内容。

不预置 `.claude.json` 的 onboarding、假 key 批准或 repo trust 内部字段。[官方认证说明](https://code.claude.com/docs/en/authentication#authentication-precedence) 描述了交互 API key 批准；[官方设置说明](https://code.claude.com/docs/en/settings#find-or-create-your-settings-files) 将应用状态与项目信任放在 CLI 自维护文件中。未找到此次可用的公开预置合同，后两项保持未知。本探针只观察实际剩余提示，不宣称引导已经完成。

## 完整参数与实例绑定

实例根 `/private/tmp/t078-2-p1-05-sgtocfk7`；task `t078-p1-05`，launch `776a1e76-12d3-46bd-801d-2f6b29a4eb2a`，session `5cba7310-f985-4003-b94e-04345c41518a`，thread `3f5fbdcb-a69f-4d49-a15b-ba7cbb4c6a9d`。HOME、CLAUDE_CONFIG_DIR、state、repo、tmp、shell、requests、控制端 HOME 均在该实例根内。

准确 argv、shell argv、完整白名单 env、hooks、角色卡原文及 `--version`／`--help` 两项预检见 [approval.json](p1-materials-05/approval.json)；输入见 [input.json](p1-materials-05/input.json)，控制端／API argv 和 env、配置路径、预算与端口规则见 [control-plane.json](p1-materials-05/control-plane.json)。父进程的凭据及 A2A 身份变量不继承，不读或复制用户认证。后台自行添加本 launch 的私有 capability，不公开入证据。

Claude 可执行文件保持 `/Users/luckye/.local/share/claude/versions/2.1.296`。参数保持 `--session-id <本 session> --model claude-haiku-5-5 --effort low --permission-mode manual --settings <仅 hooks JSON> --append-system-prompt <角色卡原文> --strict-mcp-config --mcp-config {"mcpServers":{}} --tools Bash,Read --disable-slash-commands`。不使用 `--bare`，不换版本、认证路线、工具或权限。`--settings` 仍只含 UserPromptSubmit／Stop／PermissionRequest，指向本 launch 的 `cli.ts signal`。

API 启动时绑定 `127.0.0.1:0`，由系统分配端口。先记录 api-ready.json 的端口、PID、launch/session，校验后写 runtime-input.json 与 launch/runtime-manifest.json，再启动 CLI。只允许替换模板的 api_url 与 ANTHROPIC_BASE_URL；产品入口拒绝未分配的端口 0。公开假 key 为 `a2a-fixture-key-not-a-secret`，假服务不代理真实 API。

HEAD 仍为 `38a7eeed9db48ca114b5d9ac747028d712e60468`；P1 改动未提交，HEAD 单独不能代表候选。准确源码由 [sources.tar.gz](p1-materials-05/sources.tar.gz) 与 [source-files.json](p1-materials-05/source-files.json) 绑定；启动前逐文件核对字节，不能用旧通过结论替新候选背书。

## 停止条件、原文和 cleanup

launch 不注入任务、Enter 或默认选择，返回 INCOMPLETE 后由执行主控观察。**出现任何 API key 批准或目录信任提示，保存当时屏幕原文并停止推进，不按键、不选默认。** 未知、版本不符、身份无法核对、API 协议或预算异常也停止，不重试。

原始终端持续写入 `<实例根>/state/traces/<launch>/pty.raw`；launch/result.json 的 pane_output 保留原始字节 base64。若 launch 返回时屏幕尚未完整出现，执行主控只读该 trace 或经本实例 operator 凭据读取 pane_output，并保存当时完整原文；不按关键词或正则判断提示含义。

`p1-continue-05` 与 `p1-cleanup-05` 均须读回后另行批准，launch 不自动调用。continue 另要求 initial-ready.json 对本 launch/session 显式确认 readiness；最多一条 nonce 和一条脚本化 SSE，不证明真实模型。材料中的 Messages 请求上限 1 仅为后续单独批准的 continue 准备，当前 launch 无输入。

cleanup 按主控认可的修复，关联 launch/process-manifest.json 中实际 CLI PID、启动时间、命令及 shell PID。先停止自建后台，再核对 CLI 退出，最多观察 15 秒。明确无该进程才归档和删本实例；仍存活、身份变化、记录缺失或无法核对均为 BLOCKED，保留现场。不额外 kill CLI，不发信号给未知进程；自己的假 API 经 PID／命令核对后才收 SIGTERM。实际退出核对修复仍待本次运行复验。

## 静态证据与执行

[红态](p1-bootstrap-red-05/results.json) 在材料 04 上确认 IS_DEMO 缺失和主题文件不存在两项合同失败；未预置内部状态检查通过。[同一检查的绿态](p1-bootstrap-green-05/results.json) 在材料 05 上三项 PASS。静态校验、参数差异和项目 status 见 [p1-preparation-check-05.json](p1-preparation-check-05.json)。这些只证明材料构造，不证明 CLI 引导、hooks、主控协议或真实模型行为。

静态检查与生成重放（新标签、新输出目录，不能覆盖旧结果）：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/workbench/tests/regenerate_t078_p1.py --label p1-materials-<新编号>
node /Users/luckye/Documents/Code/a2a-wt-t078/workbench/tests/test_t078_p1_bootstrap.ts /绝对路径/p1-materials-05 /绝对路径/新的检查目录
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/p1-check-materials-05.py --output /绝对路径/新的静态报告.json
```

本次唯一请求执行的阶段，由执行主控审批并在沙箱外运行：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-launch-05
```

后续真实登录 2～3 回合、完整假 API 主控链路、同任务三窗格和合流均未执行。假服务证明与真模型证明分开报告，整票仍 INCOMPLETE。
