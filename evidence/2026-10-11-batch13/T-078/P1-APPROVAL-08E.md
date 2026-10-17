# P1 材料 08e：显式选择信任，只请求 launch 审批

依据主控 #113 与 [决定 04](p1-materials-08e/controller-decision-04-update-113.md)。**域和静态检查 PASS；实际信任选择、主回合及 hooks 仍 INCOMPLETE／待审批。** 本轮没有启动 Claude／API／PTY／模型，没有发送真实界面按键。

## 08d 读回与根因

08d 的主题三键和固定 Security notes Enter 均由主控实跑通过。下一份 [实际原文](p1-materials-08d/screen-after-notice-01/screen.bin) 共 6,568 字节，显示目录信任；光标／默认为 `No, exit`，下一项为 `Yes, I trust this folder`，底部说明 Enter 确认、Esc 取消，没有数字编号。旧 Digit1 没有此屏依据；主控未发送，已 [cleanup PASS](p1-materials-08d/cleanup/result.json)，无残留。原件与批准保留。

新域探针使用该实际默认屏，重放其前面的实际主题／notice 事件；Yes 光标的重绘是明确标注的合成域输入，不能冒充 CLI 实测。[首次红态](trust-selection-red-08e/results.json) 和 [加入实际前置事件的红态](trust-selection-red-02-08e/results.json) 均确认：起点拒绝 ArrowDown，却接受 Digit1、实际写出字节 `1`。直接 Enter 等下游规则在起点不可达，不冒称其业务红态。

## 单独提交的修复

修复提交 **`ab997f4d2ea8f4719e6989409c1bebb5835099c1`**，[diff](trust-selection-fix-08e.diff) 供主控审。workspace-trust 只接受 ArrowDown／Enter，二者目标项都必须是 `Yes, I trust this folder`。Enter 的前一条已登记意图必须是当前 launch／窗格的 workspace-trust ArrowDown 到该项；新确认原文还须完整延续该导航快照的字节前缀，且有新读回字节。当前原文仍须等于本次批准快照；不解析文字含义、不猜光标、不用数字键兜底。

同屏 ID／相同原字节仍只能操作一次；整个 launch 只允许一次信任确认，确认后连新的信任导航也拒绝。两步各自记录原文、时间、目录、目标项、按键与批准引用，来源由 operator 凭据取 executor，不算用户亲手输入。Digit1 已从产品按键映射和 runner choices 删除，没有并行路径；主题、固定 notice 和真登录的限制不变。

[信任域绿态](trust-selection-green-08e/results.json) 10/10；原屏幕／主题／notice 域检查分别 4/4、4/4、12/12。默认 Enter、Digit1、两次确认、错误目标、其他用途插入、原文前缀变化、快照变化、同屏换 ID 和真登录记录均被拒。[导航变异体](trust-navigation-mutant-08e/counterexample.json) 撤掉前置导航核对，默认 No 屏实际写出 CR；[次数变异体](trust-once-mutant-08e/counterexample.json) 实际完成两次 ArrowDown＋CR；[前缀变异体](trust-prefix-mutant-08e/counterexample.json) 实际在不延续原文的快照上写出 CR。各自只令对应检查失败，属于域业务反例，未操作真实菜单。

## 新实例与完整启动绑定

实例根 `/private/tmp/t078-2-p1-08e-8k1yyjw5`；task `t078-p1-08e`，launch `30724960-8ff2-4b20-bd0d-9a25b2ce192f`，session `f4b06f40-93fc-41b6-8a57-c568818f97dc`，thread `aaa4dad9-d53b-420d-90bc-88c777fc6e51`。repo 仅预置 value.txt。HOME、CLAUDE_CONFIG_DIR、TMPDIR、ZDOTDIR、manager-home、state、requests、hooks 全隔离在本根内；不预置 CLI 内部状态，不碰用户 ~/.claude，不读取／复制凭据。

准确 CLI argv／shell argv／env／角色／hooks／预检见 [approval.json](p1-materials-08e/approval.json)，控制端及 API argv/env 见 [control-plane.json](p1-materials-08e/control-plane.json)。固定 CLI 2.1.296、Haiku 5.5／low、manual、公开 Bearer、theme=dark、无 IS_DEMO、禁标题侧请求、debug-file、hooks timeout 3 秒与原始 stdin／stdout／stderr／退出／耗时不变，不用 --bare。

代码绑定上述修复提交及 [52 文件源码快照](p1-materials-08e/sources.tar.gz)。启动前逐字节核对；变基或源码变化须重新生成、重新审批。API 在 launch 才绑定 loopback 端口 0，分配端口写 runtime manifest；只有 api_url／ANTHROPIC_BASE_URL 可随实际端口改变，核对后才启动 CLI，私有 capability 不入 manifest。

launch 输入／模型预算 0；另批 continue 后最多一次 nonce、一个假 API 主 Messages 请求，真实供应商模型预算 0。仍先证明一回合；Esc 放行、二次送达、紧急停止保留材料 09，完整链路验收未删。

## 本次只请求启动

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-launch-08e
```

只预检、初始化自己的夹具 Git repo、启动自己的 API／后台／CLI，记录进程身份及持续 trace 路径后停下。launch 返回 INCOMPLETE，仅证明进程启动，不截即时首屏、不推定就绪，不发菜单键或 nonce。

显示界面后，主控另批只读屏幕，SCREEN_ID 为本次快照的新名称：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-screen-08e SCREEN_ID
```

逐屏读回原文、时间、目录、launch/session，从 [批准模板](p1-materials-08e/screen-key-approval-template.json) 另存 approvals/SCREEN_ID.json；填 executor 批准引用／basis、用途、明确按键、目标项和原文路径。模板不是批准，不复制旧实例确认。

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-key-08e SCREEN_ID KEY PURPOSE
```

KEY 仅 ArrowUp／ArrowDown／Enter。主题仍逐屏另批 Up→Auto、Down→Dark、Enter→Dark。固定 Security notes 仍用 onboarding-notice／Enter／Continue，须与 [固定文字](p1-materials-08e/security-notice-text.txt) 逐字一致且原字节另获批准；[比较规则](NOTICE-COMPARISON-08D.md) 保持有效。

目录信任步骤明确分开：

1. 读回本实例实际信任屏，确认目录和 `No, exit`／Yes 两项；单独批准 `ArrowDown / workspace-trust / selected_label="Yes, I trust this folder"`。
2. 另读回变化后的新快照，主控确认实际光标在 Yes、还是同一信任对话框；另存新 screen_id 和批准文件，再单独批准 `Enter / workspace-trust / selected_label` 同上。

两步之间不自动补 Enter。默认 Enter、Digit1、错误目标、其他用途插入、快照或目录／身份不符、重复确认、需要别的键或无响应，均停下保存原件，不重试。旧 [08d 后续引导说明](ONBOARDING-AHEAD-08D.md) 的信任 Digit1 建议已被本次实测取代，不能执行；其“完整顺序未知、新认证／权限／遥测／共享／MCP 屏停下”仍有效。现在已实测 Security notes 之后出现信任框，不据此推断确认信任之后再无引导。

到实际主提示符后，由主控另填本实例 readiness.json、另批 `p1-continue-08e`，要求主请求、busy、UserPromptSubmit／Stop、ACK、idle 和真实 hook exit 0 原件；最后另批 `p1-cleanup-08e`，确认 manifest 中 CLI 退出才报 PASS 并归档／删本根。单文件超 5 MiB 停下报告。

**真登录阶段：用户 HOME 出现任何引导屏，一律保存原文、停下交主控、不按键。** 此按键入口仅用于隔离假服务。

## 静态检查和重放

[静态报告](p1-preparation-check-08e.json) 核对新实例／ID、仅 value.txt、准确参数、隔离目录、无内部状态／readiness／批准、源码字节、语法、startup-only、无 Digit1 runner choices、信任模板和固定 notice、尺寸及 project-map status。实际 launch 未执行；整票保持 INCOMPLETE、open、待主控关闭。

```sh
node workbench/tests/test_t078_trust_selection.ts /绝对路径/新域输出 evidence/2026-10-11-batch13/T-078/p1-materials-08d
python3 -B workbench/tests/regenerate_t078_p1.py --label p1-materials-<新编号>e --extra-source evidence/2026-10-11-batch13/T-078/p1-check-materials-08e.py
python3 -B evidence/2026-10-11-batch13/T-078/p1-check-materials-08e.py --output /绝对路径/新静态报告.json
```

不覆盖旧证据。变异体精确替换和命令在对应 command.json，仅在新建临时源码副本运行；检查器绑定 08e，新材料须另生成相应检查器并重新审批。提交材料后工作树保持干净，不 push。
