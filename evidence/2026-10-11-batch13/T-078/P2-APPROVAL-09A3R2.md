# 09A-3R2：逐项预批的模拟用户清空与声明

2026-10-14，主控 #150／#151。**材料准备 PASS；真实场景与整票验收 INCOMPLETE。** 只申请 clean launch，不启动、不依赖用户在场；CLI、假 API、后台、Electron、构建及真实模型启动均为 0。两套串行：clean 完成并确认退出后，再独立批准 block。删除保留不执行，到清理阶段由主控另定。

源提交 `643d59bfadbf07466ee28d57f471b8ef3d10646f`，九项尾注；[冻结记录](source-freeze-09a3r2.json)。本次只改测试／材料工具，src/app/hooks 与 core.ts／taskCards.ts 不改；旧 09a3r 材料保留，但因冻结驱动改变不再用于 launch。原产品回归见 [regression-02](rebased-outside-regression-02-09a3/result.json)，绑定原提交；新驱动局部 runner 14/14、窗口分支 13/13、原收据 12/12 PASS，红态及坏变异见 [实现报告](IMPLEMENTATION-09A3R2.md)。不把合成窗口事实称作真实 CLI／窗口绿态。

主控 #150 明确把无法执行的人工步骤改为 executor 预批的 test-simulated-user。生产输入记录仍走实际窗口通路，结果和 driver 日志明确标注自动化来源、executor 批准与逐动作引用；不冒称真实用户亲手操作。后台不删字，不裁剪／容忍拼接／自动重送，Stop 不变。

## 两套新身份

| 项目 | clean 正例 | block 反例 |
| --- | --- | --- |
| 材料 | [p1-materials-09a3r2](p1-materials-09a3r2/approval.json) | [p1-materials-09a3r2-block](p1-materials-09a3r2-block/approval.json) |
| 根 | `/private/tmp/t078-2-p1-09a3r2-hgqtpjz_` | `/private/tmp/t078-2-p1-09a3r2-block-093154n0` |
| task | `t078-p1-09a3r2` | `t078-p1-09a3r2-block` |
| launch | `06c1b757-4a9e-4054-906e-5b68efd74f5b` | `c55cbe18-b823-42a6-a707-51fe992f077b` |
| session | `36276ce3-224f-4dfb-bfeb-fa5cd7968d1c` | `ba9bc02d-7a4e-49f1-8109-85de8625449f` |
| thread | `be7457e3-5f46-4f76-9fc7-2a2173f1fefc` | `c27c24d3-481c-477e-9ebe-427fe3d319fc` |
| 主 Messages 预期 | 两次；第二请求末条 user 文本精确为登记标记＋nonce2 | 一次；实际拼接 UPS2 被 hook 阻断，无 API2 |
| Ctrl+C 预算 | 一次，且只在已取消／退休并看到恢复草稿后 | 0，保留草稿 |

独立 HOME／CLAUDE_CONFIG_DIR／TMPDIR／ZDOTDIR／Electron user-data、task／launch／session／thread 与四个 nonce；不复用旧实例或批准。每套提交／主 Messages 上限 2，真实模型上限 0。block 的上限 2 不是验收允许 API2；它必须在实际阻断 hook 完成后的 2 秒观察期内仍只有 API1。

完整 CLI/shell argv、env、hooks、版本预检在各自 `approval.json`；控制端 env、假服务 argv、端口解析在 `control-plane.json`；阶段 argv、预算在 `scenario-driver.json`。固定 CLI 2.1.296，Haiku 5.5／low／manual；公开假 token，不复制用户凭据，空 MCP、禁标题、dark theme、debug-file、hook timeout 3 秒。只绑定 `127.0.0.1:0` 假服务，运行时仅解析实际端口并修改 api_url／ANTHROPIC_BASE_URL。无真实供应商模型请求，不写全局配置，不换版本或启动参数。

## 当前只申请 clean launch

材料提交后，以下启动仍需主控单独批准：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-09a3.sh 09a3r2 clean launch
```

范围是冻结材料里的 `--version`／`--help` 预检、隔离 repo 初始化、假 API、后台及交互 CLI，并经启动参数安装列出的 hooks。输入／按键预算 0，不启动 Electron，不声明首屏或 readiness。worker 和材料提交脚本均不执行 launch。

## 逐屏引导、信任和 readiness 另批

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-09a3.sh 09a3r2 clean screen SCREEN_ID
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-09a3.sh 09a3r2 clean key SCREEN_ID KEY PURPOSE
```

每屏使用新 SCREEN_ID，先保存并阅读原字节，再填 `approvals/SCREEN_ID.json`，一次一键。仍绑定当前 launch/session、隔离 repo、原 screen 文件、用途、导航后选项、批准人／引用／依据。theme 若出现，ArrowUp→Auto 读回、ArrowDown→Dark 读回，再另批 Enter；Security notes 逐字匹配冻结 notice 后另批 Enter；workspace-trust 先 ArrowDown→Yes、读回选项，再另批 Enter。已经满足的项不多发键，没有默认 Enter、Digit1 或自动补键。新权限／认证／共享／遥测或不认识的屏幕即停。

实际主提示符出现后另填 `readiness.json`，confirmed_by=executor、readiness=confirmed，保存 basis。当前所有模板未批准。block 独立走同一流程，不继承 clean 的 trust／readiness。

## actions-approval 必须逐项预批

把各包 `actions-approval-template.json` 填为 `actions-approval.json`。保留绑定的 launch/session/scenario、source=`test-simulated-user`、key_basis；顶层填写 approved_by=executor、approval_ref、basis；**actions 每一项也分别填写 approved_by=executor、approval_ref、basis**。只填总批准、改 key／truth、错身份／场景／来源、漏一步，都在窗口动作前拒绝。

| clean actions（顺序固定） | block actions（顺序固定） |
| --- | --- |
| Escape | Escape |
| clear-restored-draft，key=Control+C | retain-restored-draft，无清空键 |
| declare-empty-release，truth=empty | declare-empty-release，truth=intentionally-false |

这是预批自动化，不是等待人工窗口操作。Esc 与清空／声明的请求日志、收据和 source 均留存。

## clean continue：一次清空、实际观察后声明

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-09a3.sh 09a3r2 clean continue
```

本阶段才构建专属 slot、打开隔离 Electron、初次放行并注入 nonce1。先核对 CR1／UPS1／API1／busy、nonce2 仅登记排队、窗口绑定和可输入；经同窗口发一次 Esc，并取得 action→准入→intent→written→退休收据、API1 peer 取消、active=null、busy/interrupted、queue held。

驱动随后观察最后一个可辨识的 `❯` 编辑区：两条横线包围、第一 nonce 确实恢复，保存 restored-draft 截图／窗口快照。只有此状态和同窗口中断引用匹配，才经 xterm 键盘通路发一次 Control+C。按键依据为 [官方 Interactive mode](https://code.claude.com/docs/en/interactive-mode)：无操作运行时第一下清空输入，第二下可能退出；详见[日期化依据](KEY-BASIS-09A3R2.md)。此选择有文档依据，本包尚未在新实例实测。

清空必须取得 UTF-8 0x03 的 control action／准入／intent／written；不能记 message，attempted 不是送达。驱动等新 PTY offset 和窗口编辑区确实为空，保存 cleared-draft PNG／JSON、编辑区行号／内容和相同 highwater 的 PTY 原字节前缀。不是清 textarea、读后台 user_draft 或检查整个 transcript 里有没有 nonce。只有最新输入代次恰好增加一次且 Esc 引用保持一致，才点击真实“输入框已空，放行”按钮；再核对“用户声明输入框已空”的记录、引用及代次与释放事件一致。

正例最终要求新 prompt_id、第二 paste＋独立 CR、exact API2、唯一 Stop2、idle、P2_ACK 和截图成立，三份实际 hook exit 0。后台不删字，清空仅走模拟用户输入通路。输入或组合事件后的旧声明仍由生产入口拒绝；手打且未登记为注入的提交不套用错配阻断。

停止条件：恢复草稿不可见、错窗／仍 active／只读、一次 Ctrl+C 未清空／CLI 退出、未知输入区／残字／占位提示、快照未到新 offset、缺控制收据、被记 message、额外输入或代次改变，都停 INCOMPLETE。不发送第二次 Ctrl+C，不换 Ctrl+U／Ctrl+S／双 Esc，不自动重投。

## block 独立批准：不清空，模拟不真实声明

clean 运行结束且退出已确认后，再单独批准：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-09a3.sh 09a3r2 block launch
```

block 的 screen／key／readiness／actions／continue 都独立批准；命令把 clean 改成 block。Esc 送达、取消／退休／held 与恢复草稿观察仍要求齐备。驱动不发任何清空键，只保留草稿，再按预批 truth=intentionally-false 点击声明。这证明用户声明不等于机器读到了空框，并验证真正的提交前保护。

实际 UPS2 必须含两个 nonce，diagnostic 绑定 dispatch2/submission；hook 原始 stdout 为 JSON decision=block、exit 0；API 总数仍 1，无 API 错误、无第二 turn_start／Stop，仅两次提交写入。阻断 hook 完成后再观察 2 秒无 API2；保存拼接 prompt、原 hook、库事件、PTY 和截图。缺证、未知、API2、自动重送或超时都停 INCOMPLETE。这是有界观察，不称一般可靠性。

## 清理保留，当前不批准删除

本包不运行 cleanup 或 slot 删除，不在 launch／continue 中隐含它们。窗口驱动完成／失败时关闭自己的 Electron；后台、CLI、API 和隔离根的后续清理到主控阶段再定，仍核对实际身份／退出并保存原件。slot-cleanup 包装入口目前直接拒绝，不调用“清单后删除”脚本。`scenario-driver.json` 中 slot_cleanup_argv 只记录既有工具位置，本包不批准执行。两套 slot 当前都未创建；不碰旧 slot、共享构建输出或用户窗口。

普通状态期限 30 秒、构建 90 秒、block 无 API2 观察 2 秒；不再等待 180 秒人工处理。观测可轮询，按键和声明各只尝试一次，不自动重试。外置盘缺失即停，不回退。单文件超 5 MiB 时保留原件，交主控外置归档／逐字节读回，不删失败或覆盖旧结果。

## 静态证据及材料提交

[生成记录](preparation-generation-09a3r2/result.json)、[准备核对](preparation-check-09a3r2.json) PASS：两包各 79 文件逐字节冻结；新身份／nonce、未启动状态、隔离设置、固定 argv/hooks、逐项未批准模板、自动化来源、清空预算、语法、TSX 内存转换与 project-map status 均通过。[最终交付核对](materials-delivery-check-09a3r2.json) 10 项 PASS，另实走包装拒绝分支，确认 slot 删除入口与旧 generation 均 exit 2、没有执行启动或删除工具。只读复核使用新输出文件：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/check-materials-09a3.py --generation 09a3r2 --output /绝对路径/新准备检查.json
```

主控按原 worker 启动身份提交，钩子自动追加尾注，脚本只提交不 launch：

```sh
sh /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/commit-materials-09a3r2.sh
```

真实 clean/block、新候选独立 reviewer、09B/09C、实际系统 IME 和真登录仍 INCOMPLETE，整票 open；不关闭、不验收／集成、不 push。静态准备 PASS 不替代实际边界证据。
