# P1 材料 08b：逐屏批准按键，先交 launch 审批

2026-10-14，依据主控 #106～107 与 [决定 04](p1-materials-08b/controller-decision-04-update-106.md)。**静态准备 PASS，真实引导、信任、主回合和 hooks 仍 INCOMPLETE／待审批。** 本轮未启动 CLI／API／PTY，没有向真实界面发送按键，不写 CLI 内部状态，不碰用户 ~/.claude。

## 08 的读回与最小改动

08 真实启动停在主题选择，[原文](p1-materials-08/launch/screen.bin) 保留；执行主控没有按 Digit1 或 Enter。[cleanup](p1-materials-08/cleanup/result.json) 已核对 CLI PID 22672 退出，PASS、无残留。不能把该主题屏当作信任屏，也不能把 Dark 所处位置当成数字快捷键。

产品改动单独提交 `2f6d31ea2506c5ea508e37327bde28f8dbce47ee`：旧 pane_trust／trustKey 已由 pane_screen_key／screenKey 替代，不留并行接口。用途限隔离假服务的 onboarding-theme／workspace-trust；真实调用者由 operator 凭据认证，UI 用途、屏 ID、所选项和批准引用不充当身份。

同一屏 ID 或相同原字节快照不能第二次按键，即使换 ID 也拒绝。workspace-trust 另限整个 launch 一次。每次检查实际 CLI、启动期状态和原文仍未变化，先登记意图再写 PTY，记录时间、目录、用途、所选项、原文与按键；不记为用户亲手输入，不自动连按、补键或 continue。权限、认证、遥测或数据共享选择均停下交主控，不能套用主题用途。

## 主题键的依据与实际未知

[依据记录](key-evidence-08b.json) 区分事实与未知。实际 2.1.296 屏幕没有主题数字编号：首项 Auto，第二项是光标与勾选所在的 Dark mode；代码预览中的数字不是菜单编号。未找到该版本主题数字快捷键的官方合同，**不配置 Digit1／Digit2 作为主题键**。

[官方 Select 操作](https://code.claude.com/docs/en/keybindings#select-actions) 定义 Up／Down 导航和 Enter 接受选项。08b 将它们映射为 ArrowUp=`ESC[A`、ArrowDown=`ESC[B`、Enter=`CR`；是否适用于这个首次 ThemePicker，仍须批准后在真实屏幕读回，不把文档当作已运行证明。

针对已看到的 Dark 光标，建议：单独批准 ArrowUp 导航到 Auto → 读取变化后的新快照并另批 ArrowDown 明确移到 Dark → 再读回已选 Dark 后，**单独批准 Enter 确认该明确所选项**。这不是启动时 Enter 选默认，也不是数字键后自动补 Enter。后端要求 Enter 前一条已登记主题导航是从 Auto 的 ArrowDown，且本次批准所选项为 Dark；直接默认 Enter 被拒。

每个不同的选择状态使用新的 screen_id 与实际原字节、独立批准文件。动作后不自动推断界面已变化或引导完成；如果真实界面不响应、需要其他键、显示其他引导，停下读回，不重试。若主控不批准此显式确认方案，只执行 launch，按键阶段不执行。目录信任的 Digit1 只在新原文明确显示对应选项并另批后使用。

## 新实例和完整材料

实例根 `/private/tmp/t078-2-p1-08b-ubqe_xs5`；task t078-p1-08b，launch `2fa7ba09-b9d4-4919-872b-ede76921763d`，session `fcc94015-6ecc-45e3-b6c4-74a1eca36dcb`，thread `d036af51-03e7-49ee-bc2e-2276bc1de6e1`。repo 仅预置 value.txt，Git 元数据在 launch 初始化；HOME、CLAUDE_CONFIG_DIR 和全部运行目录均隔离在该根内。

准确 argv／shell argv／env／角色／hooks／预检见 [approval.json](p1-materials-08b/approval.json)，控制端和 API argv/env 见 [control-plane](p1-materials-08b/control-plane.json)。其余同 08：固定 CLI 2.1.296、Haiku 5.5／low、manual、Bash/Read、空 MCP、公开 Bearer、theme=dark、无 IS_DEMO、禁标题侧请求、debug-file、原始 hook stdin/stdout/stderr/退出/耗时、timeout 3 秒。

源码绑定上述产品提交与 [source snapshot](p1-materials-08b/sources.tar.gz)，启动前逐文件字节核对；变基改变源码时必须重新生成并审批绑定，不复用此静态 PASS。初始 API URL 为 loopback 端口 0，实际端口在运行时分配、记录并校验，再启动 CLI。仍只一条主 Messages 请求、一条 nonce、0 个真实模型回合；Esc、二次送达、紧急停止保留在 09。

## 独立审批阶段

本次只请求 **launch**：预检、启动、读屏并停下。首次引导出现时保存原文，不发任何按键。

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-launch-08b
```

后续每个屏幕先单独读取，`SCREEN_ID` 是主控给该实际快照的唯一名称：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-screen-08b SCREEN_ID
```

保存于 screen-SCREEN_ID/screen.bin 与 screen.json（时间、目录、launch/session、screen_id）。主控从 [screen-key-approval-template](p1-materials-08b/screen-key-approval-template.json) 另存 approvals/SCREEN_ID.json，填写真实所选项、用途、明确按键、原文路径、approved_by=executor、approval_ref 和实际 basis。模板不是批准；不得复制旧屏原文或旧实例确认。

然后逐次另批下面的单键命令。KEY 仅 ArrowUp／ArrowDown／Enter／Digit1；PURPOSE 仅 onboarding-theme／workspace-trust，组合由后台严格限定：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-key-08b SCREEN_ID KEY PURPOSE
```

实际输出 key-SCREEN_ID/ 保存批准、按前原文、按后原文、进程确认及后台事件。返回 INCOMPLETE，等待人再次读回；不会自动执行下一屏或 Enter。同屏／重复信任／原文变化或来源不符即停，无兜底重试。

实际进入提示符后，主控另填本实例 readiness.json 并审批 `p1-continue-08b`；它才允许一次登记的 bracketed paste＋独立 CR，要求主请求、busy、UserPromptSubmit／Stop、ACK、idle 和真实 hook exit 0 原件。之后另批 `p1-cleanup-08b`，核对本 CLI 退出才归档／删根。任何超限文件停下报告，不自动压缩豁免或外置。

**真登录阶段：在用户 HOME 出现任何引导屏（不只信任），一律保存原文、停下交主控、不按键。** 假服务逐屏接口只允许 isolated fake API 记录，不能用于真登录。此条也已写入 [PLAN-2](PLAN-2.md)；真登录尚未启动，未读或复制凭据。

## 静态证据

[红态](screen-key-red-08b/results.json) 为新入口缺失，拒绝规则不可达，不冒充业务红态。[绿态](screen-key-green-08b/results.json) 证明域夹具中的显式导航／确认、同屏去重、默认 Enter／数字主题键拒绝与信任一次限制；[反例](screen-replay-mutant-08b/counterexample.json) 去掉原字节去重后，换 ID 实际写了第二次 ArrowUp。均未操作真实菜单或 PTY。

[准备检查](p1-preparation-check-08b.json) 覆盖无内部状态、仅 value.txt、准确参数、48 个冻结文件、语法、尺寸与项目 status，PASS。真实按键、hooks 与回合仍未完成；旧 08 的通过项不外推到新候选。

重放用新编号／输出，不能覆盖现有证据：

```sh
node workbench/tests/test_t078_screen_key.ts /绝对路径/新的域检查目录
python3 -B workbench/tests/regenerate_t078_p1.py --label p1-materials-<新编号>b --extra-source evidence/2026-10-11-batch13/T-078/p1-check-materials-08b.py
python3 -B evidence/2026-10-11-batch13/T-078/p1-check-materials-08b.py --output /绝对路径/新的静态报告.json
```

材料将独立提交，工作树保持干净供主控变基；整票 INCOMPLETE、open，待主控关闭，不 push。
