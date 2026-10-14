# P1 材料 08d：固定 Security notes，只请求 launch 审批

依据主控 #111～112 与 [决定 04](p1-materials-08d/controller-decision-04-update-112.md)。**域与静态检查 PASS；实际 notice 确认、主回合与 hooks 仍 INCOMPLETE／待审批。** 本轮没有启动 Claude、假 API、PTY 或模型，没有发送真实菜单键。

## 08c 读回与本次变更

主控实跑 08c 证明 ArrowUp→Auto、ArrowDown→Dark、Enter 确认 Dark 三步均写入 PTY，主题屏结束；随后停在 4,685 字节的 [Security notes 原文](p1-materials-08c/screen-after-theme-01/screen.bin)，没有按键。[cleanup](p1-materials-08c/cleanup/result.json) PASS，无残留。原件及批准文件保留。

构思主控同意只在隔离实例确认这一固定提示。新用途 onboarding-notice 只允许 Enter；[比较规则](NOTICE-COMPARISON-08D.md) 明确分段、去控制序列、逐字相等、拒绝反例、原字节批准和一次限制。文字不同即停，不使用关键词或语义判断，不确认其他提示；真登录用户 HOME 的任何引导屏仍停下交主控、不按键。

产品单独提交 **`f14d63df7f6f5131ea143ab37a5878ec7ecb28e8`**，[diff](notice-fix-08d.diff) 供主控审。[红态](notice-red-08d/results.json) 是旧门禁拒绝整个新用途，没写额外 CR；下游规则不可达，不冒称各业务规则红态。[最终域检查](notice-green-final-08d/results.json) 12/12，[单规则文字变异体](notice-text-mutant-08d/counterexample.json) 撤掉比较后实际写出四个不应写的 CR，四项失败、其余通过。原主题／屏幕检查各 4/4，未放宽其他用途。全部是合成 PTY／进程身份的域证据，真实 notice 未确认。

## 新实例、启动绑定和预算

实例根 `/private/tmp/t078-2-p1-08d-ohyh5win`；task `t078-p1-08d`，launch `17e750b4-13e5-4d49-b0b6-923e019df82e`，session `0fcd6b6a-3a47-4b8d-a99f-cff643cdf75f`，thread `f361ac76-3658-4fcb-8459-eb3e3c37d435`。repo 只预置 value.txt；HOME、CLAUDE_CONFIG_DIR、TMPDIR、ZDOTDIR、manager-home、state、requests 和 hooks 全部隔离在该根内。

准确 CLI argv／shell argv／env／角色文本／hooks／预检见 [approval.json](p1-materials-08d/approval.json)，控制端和 API argv/env 见 [control-plane.json](p1-materials-08d/control-plane.json)。固定 CLI 2.1.296、Haiku 5.5／low、manual、公开 Bearer、theme=dark、无 IS_DEMO、禁标题侧请求、debug-file、hooks timeout 3 秒及原始 stdin／stdout／stderr／退出／耗时不变。不用 --bare，不预置内部状态，不碰用户 ~/.claude，不读取或复制凭据。

代码绑定上述提交与 [51 个文件的源码快照](p1-materials-08d/sources.tar.gz)。启动前逐字节核对；变基或源码变化必须重新生成并审批。API 只在 launch 绑定 loopback 端口 0，分配端口后写 runtime manifest，再核对只有 api_url／ANTHROPIC_BASE_URL 改变才启动 CLI。私有 capability 不入 manifest。

launch 输入 0、模型 0；后续 continue 仍须单独批准，最多一次 nonce、一个假 API 主 Messages 请求，真实供应商模型预算 0。仍先证明一回合；Esc 放行、二次送达、紧急停止留材料 09，完整验收未删。

## 本次请求：只启动，不按键

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-launch-08d
```

launch 只预检、初始化自己的夹具 Git repo、启动自己的 API／后台／CLI、记录实际进程身份与持续 trace 路径；返回 INCOMPLETE，不截即时首屏、不宣称就绪、不发送任何菜单键或 nonce。

显示界面后另批只读屏幕命令，SCREEN_ID 是该快照的新名称：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-screen-08d SCREEN_ID
```

保存原字节、时间、目录、launch/session。主控逐屏读回，从 [模板](p1-materials-08d/screen-key-approval-template.json) 另存 approvals/SCREEN_ID.json，填 approved_by=executor、approval_ref、basis、用途、明确按键、目标项和原文路径；模板不是批准，不复制旧实例确认。

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-key-08d SCREEN_ID KEY PURPOSE
```

各步独立审批：主题 ArrowUp 目标 Auto → 读回 → ArrowDown 目标 Dark → 读回 → Enter 确认 Dark。随后若确为本次固定 Security notes，读回新原文后另批 `KEY=Enter / PURPOSE=onboarding-notice / selected_label=Continue`，后端同时核对 [基准文字](p1-materials-08d/security-notice-text.txt) 与主控批准的原字节。同一 notice 在 launch 限一次，换 ID／重绘不能再次确认；不自动补 Enter或进入下一步。

可能的后续引导及官方依据见 [比对说明](ONBOARDING-AHEAD-08D.md)。未信任目录预计会显示信任框，但固定版本的逐屏顺序未知；目录信任须读回实际选项、另批 workspace-trust／Digit1，一次。认证、权限、遥测、共享、MCP 或其他新提示均停下，不套用 notice。任何原文变化、文字不同、重复操作、错误来源、需要其他键或无响应，保留原件、不重试。

到实际主提示符后，主控另填本实例 readiness.json、另批 `p1-continue-08d`，核对主请求、busy、UserPromptSubmit／Stop、ACK、idle 和真实 hook exit 0 原件。最后另批 `p1-cleanup-08d`，确认 manifest 的 CLI 已退出才报 PASS 并归档／删本根。单文件超 5 MiB 停下报告。

**真登录阶段：在用户 HOME 出现任何引导屏，一律保存原文、停下交主控、不按键。** 此入口只适用隔离假服务记录，不用于真登录。

## 静态与重放

[静态检查](p1-preparation-check-08d.json) 核对新实例／ID、仅 value.txt、参数、隔离目录、无内部状态／readiness／批准、源码字节、语法、startup-only、模板和固定文字与 08c 原件一致、尺寸与 project-map status。实际 launch 未执行；整票保持 INCOMPLETE、open、待主控关闭。材料提交后工作树保持干净，不 push。

```sh
node workbench/tests/test_t078_notice_key.ts /绝对路径/新域目录 evidence/2026-10-11-batch13/T-078/p1-materials-08c
python3 -B workbench/tests/regenerate_t078_p1.py --label p1-materials-<新编号>d --extra-source evidence/2026-10-11-batch13/T-078/p1-check-materials-08d.py
python3 -B evidence/2026-10-11-batch13/T-078/p1-check-materials-08d.py --output /绝对路径/新静态报告.json
```

不得覆盖已有证据。检查器绑定本次 08d；新材料也须有对应检查器及重新审批。
