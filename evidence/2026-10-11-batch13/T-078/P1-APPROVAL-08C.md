# P1 材料 08c：修复主题确认，只请求 launch 审批

依据主控 #109 与 [决定 04](p1-materials-08c/controller-decision-04-update-109.md)。**域检查及静态准备 PASS；真实主回合、hooks 与完成仍 INCOMPLETE。** 本轮未启动 Claude、假 API 或 PTY，未发送真实界面按键。08c 使用新实例和新 ID；08b 的失败、屏幕、批准与 cleanup 原件全部保留。

## 根因、红态与修复

[只读诊断](theme-diagnosis-08c.json) 将批准文件与后台已登记事件逐项核对，屏幕原字节也一致。theme-01 的 ArrowUp 目标是 Auto，theme-02 的 ArrowDown 目标是 Dark；theme-03 的 Enter 确认 Dark。`selected_label` 的语义是**本次按键的目标项**。旧门禁误把前一条 ArrowDown 的标签当作按键前的光标，要求 Auto；旧域测试也沿用了这个错误语义。

[新红态](theme-confirmation-red-08c/results.json) 直接读取 08b 的三个批准文件及三份实际屏幕字节，在域夹具重放同一序列。旧代码拒绝正确序列，写入只有 Up／Down；反过来，旧测试的颠倒标签却允许 CR。这两个失败都原样保留，默认 Enter 在起点上已被拒，不能把它说成新增红态。

修复单独提交 **`95b69e04aac6f20d3a18e1e42a5c2494e35f46c3`**，[diff](theme-confirmation-fix-08c.diff) 供主控审。Enter 要求连续登记的 ArrowUp 目标 Auto、ArrowDown 目标 Dark，本次批准目标 Dark；未解析屏幕含义，不放松默认 Enter，不改凭据或身份路径。[域复现绿态](theme-confirmation-green-08c/results.json) 4/4，[原屏幕门禁检查](screen-key-green-08c/results.json) 4/4：正确序列可确认，默认 Enter、颠倒标签、缺少 Auto 导航均拒绝；同屏去重及一次信任仍有效。域夹具使用合成 PTY／进程身份，**不能证明真实菜单确认已成功**。

绿态在上述提交前的相同源码上取得；[提交读回](theme-fix-commit-readback-08c.json) 核对已保存 patch 与独立修复提交一致，保留真实 worker 会话尾注，没有恢复或伪造身份环境。

08b 的 launch/screen.bin 只有 13 字节，原因是捕获 CLI 进程身份后立即截取，尚未等到首屏。08c 采用主控允许的较小改法：**launch 只记录进程启动**，返回进程 manifest 与持续 PTY trace 路径，不生成首屏、不宣称就绪。首屏另由 screen 阶段保存原文，主控读回后才可审批单键。

## 新实例、参数与预算

实例 `/private/tmp/t078-2-p1-08c-1uy5wegk`，repo 仅 value.txt；task `t078-p1-08c`，launch `3b6b2608-8ad2-4d42-bd97-55b2792bb346`，session `a5ef1f20-73fa-40f5-b824-c40bc4da4e6a`，thread `e73b5bcb-cd9f-4088-9fd5-1cefc741171f`，与 [input.json](p1-materials-08c/input.json) 一致。

完整 CLI argv／shell argv／环境白名单／hooks／角色文本／预检见 [approval.json](p1-materials-08c/approval.json)；控制端与 API argv/env 见 [control-plane.json](p1-materials-08c/control-plane.json)。固定 CLI **2.1.296**、Haiku 5.5／low、manual，公开 `ANTHROPIC_AUTH_TOKEN`、`CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1`、无 IS_DEMO，theme=dark，hooks timeout 3 秒，debug 与 hook 原始 stdin／stdout／stderr／退出／耗时留证。其余启动参数不变，不用 --bare，不预置内部引导或批准状态，不读／复制凭据，不碰用户 ~/.claude。

HOME、CLAUDE_CONFIG_DIR、TMPDIR、ZDOTDIR、manager-home、state 与 requests 均位于该实例根内。假 API 只绑定 loopback 端口 0，启动时分配并写入 runtime manifest；只有 api_url 与 ANTHROPIC_BASE_URL 可随实际端口改变，再核对批准 argv/env 才启动 CLI。后台 capability 私有，不入 manifest。

代码绑定修复提交及 [源码快照](p1-materials-08c/sources.tar.gz)，49 个文件逐字节核对；变基或源码变化必须重新生成、重新审批。材料生成不会启动服务。launch 输入预算 0；后续另批 continue 才允许一次 nonce、一个假 API 主 Messages 请求，真实供应商模型回合预算 0。08c 只证明一回合；Esc 放行、二次送达和紧急停止仍留材料 09，完整链路验收未删。

## 本次只请求启动

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-launch-08c
```

该阶段只预检、初始化自己的夹具 Git repo、启动自己的 API／后台／CLI、记录进程身份后停下。返回 INCOMPLETE 表示未证明首屏或回合，不发任何菜单键或 nonce。

显示首屏后，另批只读命令，SCREEN_ID 为该实际快照的新名称：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-screen-08c SCREEN_ID
```

它保存 screen-SCREEN_ID/screen.bin 与 screen.json（原字节、时间、目录、launch/session）。主控逐屏读回，从 [批准模板](p1-materials-08c/screen-key-approval-template.json) 另存 approvals/SCREEN_ID.json，填写用途、明确按键、**目标项 selected_label**、原文路径及 executor 的批准引用／basis。模板不算批准；不得复制旧实例批准，不得使用不同 ID 重复同一原字节。

主题若仍从 Dark 开始，只能逐屏另批 ArrowUp 目标 Auto → ArrowDown 目标 Dark → Enter 确认 Dark；每一步都读回新原文，不能自动补 Enter。目录信任只在实际原文显示明确选项且另批时用 Digit1，整个 launch 限一次。所有按键经过凭据认证、原文相等及启动期门禁，先记录意图再写 PTY，不记为用户亲手输入：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-key-08c SCREEN_ID KEY PURPOSE
```

KEY 仅 ArrowUp／ArrowDown／Enter／Digit1；PURPOSE 仅 onboarding-theme／workspace-trust，组合由后台限制。同屏重复、原文变化、错误身份、权限／认证／遥测／数据共享选择、需要其他按键或无响应，均停下保留原件，不补键、不重试。

实际到主提示符后，由主控另填本实例 readiness.json，再单独批 `p1-continue-08c`；要求主 Messages 请求、busy、UserPromptSubmit／Stop、ACK、idle 与真实 hook exit 0 原件。最后单独批 `p1-cleanup-08c`，确认 manifest 的 CLI 退出才报 PASS 并归档／删本根。单文件超 5 MiB 停下报告。

**真登录阶段在用户 HOME 出现任何引导屏，一律保存原文、停下交主控、不按键。** 不沿用隔离假服务的按键机制；[PLAN-2](PLAN-2.md) 已保留此约束。真登录尚未开始。

## 静态检查与重放

[静态报告](p1-preparation-check-08c.json) 核对新实例、仅 value.txt、准确参数及隔离目录、没有内部状态／readiness／批准、源码字节、Python／Node／shell 语法、launch 不截首屏、目标项模板、尺寸与 project-map status。静态 PASS 不替代真实 CLI／hooks／回合证明；T-078 保持 open、INCOMPLETE，待主控关闭。

重放必须使用新输出路径，不覆盖已有结果：

```sh
node workbench/tests/test_t078_theme_confirmation.ts /绝对路径/新域输出 evidence/2026-10-11-batch13/T-078/p1-materials-08b
node workbench/tests/test_t078_screen_key.ts /绝对路径/新门禁输出
python3 -B workbench/tests/regenerate_t078_p1.py --label p1-materials-<新编号>c --extra-source evidence/2026-10-11-batch13/T-078/p1-check-materials-08c.py
python3 -B evidence/2026-10-11-batch13/T-078/p1-check-materials-08c.py --output /绝对路径/新静态报告.json
```

最后一条检查器绑定本次 08c；生成新的编号时也须生成对应检查器。本次交 launch 审批后停止，工作树整理提交供主控变基，不 push。
