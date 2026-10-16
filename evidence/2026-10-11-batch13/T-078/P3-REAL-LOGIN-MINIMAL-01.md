# P3 真登录最小复核材料（计划与入口前置，未启动）

2026-10-16，主控 #335。用户认证路线已定：2026-10-12“假服务为主，真登录复核2～3回合”，见 [PLAN-2](PLAN-2.md)、[决定04](controller-decision-04.md)首节。**不重复请求认证路线；当前launch BLOCKED，2～3真实回合均未运行。** 不把下述proposal叫作已有可执行的产品profile。

## 现有入口的实际阻塞

`workbench/src/claudeLaunch.ts:39`只允许http://127.0.0.1，:50固定隔离HOME/CLAUDE_CONFIG_DIR，:51强制假Bearer，:65记authentication=isolated fake API only。`Panes.startController`沿此构造，不提供正常登录profile。`screenKey`也刻意只给fake profile，不能用它按用户HOME里的引导。把manifest.env.HOME改成用户HOME不生效；直接在zsh里另起Claude会绕过真实launch/preset/凭据/hook登记，不作为解决方案。

最小前置是另安排“正常登录profile”实现切片，保留同一个controller_start/实际caller/Stop/relay路径：明确normal-login枚举，不把“缺api_url”当fallback；隔离路径和普通登录两种已批准契约分别核对，普通分支只允许本次构思主控接收者。每会话hooks仍在/tmp，用户设置不写；不能复用假会话PID/capability。此为需要的产品行为，**不在本次仅F6源包/材料准备里顺手实现**。已另报主控；后续启动仍经具体P3/P4批准，09B代签不能自动覆盖它。

## 最小两回合及额度

一个全新夹具broker/repo/task、一名真实登录ideation接收者；另一名executor仍是交互Claude＋loopback假API。真实Codex0，确定性worker目标可不启动（本复核只验证唤醒，不做stop/ack）。两个CLI串行启动，fake executor先完成其逐屏审批；真实HOME的任何首启/主题/信任/登录/账户/权限/遥测提示都只保存原文、停止，不自动按键。

| 阶段 | 真实输入/来源 | 真实模型预算与判定 |
|---|---|---|
| R1（P3启动后另批） | 经原窗口/派发路径登记短基线：`只回复 REAL_BASELINE_<本次nonce>，不要使用工具。` | 默认第1次实际供应商Messages调用；≤60秒，目标短答≤80 tokens；核对实际Haiku 5.5、UPS/Stop及idle |
| F-SEND | fake executor实际收到批准提示，假API给Bash `node workbench/bin/inbox send --to ideation --kind report --body-file <本次报告>`；真实CLI工具排队，真实Stop转交 | 真实模型0；fake executor建议1工具根/2 POST＋1执行反馈确认根/1 POST，单工具许可另签，实际调用者executor |
| R2（P4单独批准） | 上述真实report的唯一inbox wake，完整文本带另一个nonce；不由operator冒充发report、不再人工dispatch同一唤醒 | 第2次实际供应商Messages调用，≤60秒；回复含本次nonce，真实hook/登记/PTY只送一次，原收件箱/真实调用者可关联 |
| R3（可选，非失败重试） | 只有R1/R2通过且剩余额度可核对时，另列一个明确复核目的再审 | 全卡最多第3次实际模型调用；本材料没有预批第3次输入 |

预算按**实际供应商调用**而非CR或assistant段落：工具续轮、失败、自动续轮/重试也占用3次上限。真角色不主动用工具；出现PermissionRequest/tool_use、额外POST、count不可核对即停止，不把它算免费。真登录没有假API可直接数POST；执行前必须先证明固定CLI能提供包含失败/重试的可靠调用计数（只针对本次session），不能只数transcript里的成功assistant message。计数前置尚未验证；如果拿不到，P3保持NO_GO，不改成“根数近似调用数”，也不临时加代理读取认证。

R2须在report投递前预批准并arm，避免真实唤醒先于人工审批；arm不发输入。必须先核对R1实际消耗与余额才让fake sender提交报告。整个真角色最多2个拟议根，第三根不在本默认包；CLI/provider错误不触发脚本重发。不要为限工具而增加未批准的permissions/登录配置。

## 拟议argv/env与真实HOME写入边界

参数proposal（不是目前可运行的manifest）：固定 `/Users/luckye/.local/share/claude/versions/2.1.296`、新session-id、`--model claude-haiku-5-5 --effort low --settings <本次仅hooks JSON> --append-system-prompt <本次角色卡完整文本>`。用已验证的append-system-prompt，不沿用PLAN-2早稿中已被本版本拒绝的append-system-prompt-file。**不传permission-mode/permissions/认证覆盖，不运行/login，不使用IS_DEMO，不自动更新。** MCP/工具和已有用户配置如何限制须在正常profile前置审查中明确，不能静默改变用户全局配置。

env白名单：`HOME=/Users/luckye`，本次隔离TMPDIR/ZDOTDIR/A2A_USER_DATA及后台签发的A2A_PROJECT/TASK/SESSION/ROLE/PRESET/LAUNCH/STATE/NATIVE_SESSION/SPEC_REV、本次requests/hooks路径；固定PATH/终端locale。清除继承的A2A worker身份、CLAUDE_CONFIG_DIR、ANTHROPIC_BASE_URL/API_KEY/AUTH_TOKEN及其他假服务变量；**不读、不复制、不枚举任何认证**，CLI自己使用用户已有正常登录。角色不拿operator凭据。

三个hooks为UserPromptSubmit/Stop/PermissionRequest，每条精确使用本次持久launch的 `node <repo>/workbench/src/gates/cli.ts --state <本次state> signal --launch <本次launch>`，stdin原样，timeout3秒。最终hooks JSON只含这三项，没有apiKeyHelper、认证或permissions；必须在启动审批时展开实际路径/ID后逐字核对，不能把模板占位符带进live命令。

**允许在真实HOME发生的写入仅为CLI自写的本次会话历史**：本次session的`~/.claude/projects/<由本次cwd得到的目录>/<session>.jsonl`及本次会话历史索引（若CLI需要索引，须先明确它的确切文件和写入方式再批准）。a2a脚本不在HOME写文件；hook原件、debug若能关闭或重定向则放本次/tmp目录；不写`~/.claude/settings*.json`、`~/.claude.json`、permissions、登录/认证存储、其他会话或用户既有历史，不删除任何用户历史。

这里列的是**许可白名单，不是已实测的CLI全部实际写集**。当前没有本版本正常登录的精确写集证据，不能承诺它不会自动写缓存/账户/全局索引。前置必须先确认CLI对本次历史之外写入的控制或观察方法；若无法满足“仅会话历史”，停下报主控，不用事后发现再回滚用户文件，也不扩大白名单。不能用拷贝认证到隔离HOME代替已选正常登录方案。路径中的项目目录名由CLI实际manifest/transcript确定，不靠猜测或遍历用户认证目录；只读本次精确session历史，脱敏后留证。

## 命令与停止点

可执行的本轮动作只有文件审稿/路径检查；**当前无可合法真启动的controller manifest**，所以不交一条绕开产品的直接Claude命令。后续实现好normal-login profile、冻结实际绑定和取得P3签字后，唯一启动命令形状是：

```text
node /Users/luckye/Documents/Code/a2a-wt-t078/workbench/src/gates/cli.ts --state ACTUAL_P3_STATE controller_start --task ACTUAL_P3_TASK --manifest ACTUAL_APPROVED_NORMAL_LOGIN_MANIFEST
```

该行是**不可执行模板**：ACTUAL_*尚无runtime绑定，不是空/null或伪造attempt；先由真实注册/审批填齐。后续R1/R2仍用相同pane_dispatch/release、真实收件箱自动wake和独立阶段驱动，不能使用headless/-p或绕过hook。具体完整命令必须由normal-profile切片交出实值材料后另冻；本次不能诚实地宣告“真登录命令READY”。

停止条件：任何用户HOME引导/信任/登录/权限提示；模型/CLI版本不符；要求改settings/认证/非本次历史；工具/额外调用/未知计数；>60秒；nonce/Stop不匹配；已有后台/用户会话身份混入；记录或脱敏失败。均保存INCOMPLETE、不按键、不重试、不换模型。清理只用原launch的正常停止与本次broker/API，用户HOME历史与任何认证不删；外置只留本次受限记录。下一步由主控安排normal-profile、实际写集与计数前置，已有认证路线不重问用户；任何超出“仅本次会话历史”的要求另经用户决定。
