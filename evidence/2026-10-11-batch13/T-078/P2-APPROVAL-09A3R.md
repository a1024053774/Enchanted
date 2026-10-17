# 09A-3R：变基后的空框声明正例与拼接阻断反例

2026-10-14，主控 #147／#148。**材料准备 PASS；真实场景与整票验收 INCOMPLETE。** 本包只提交正例 launch 审批，没有启动 CLI、API、后台、Electron 或构建。真实模型预算及实际消费均为 0，没有额外 Codex／子代理。两套夹具串行运行；正例完成并核对退出后，再独立批准反例。

源码绑定 `166509267fe11f02b1591f2089a77d7480a0c1e6`，是 `567d7748c40ca511f170997d7fe216063fb7c4f1` 之后保存回归证据的提交，已包含 T-077／T-076 变基结果。冻结记录见 [source-freeze-09a3r](source-freeze-09a3r.json)。本轮产品源码不变；随后材料提交只保存本包，不改变冻结源码。旧 09A-3 两套材料仍保留日期记录，不能用旧批准启动本包。

[regression-02](rebased-outside-regression-02-09a3/result.json) 与[只读读回](regression02-readback-09a3r.json)：worker-inbox 14/14、coop 8/8、recovery 9/9、run 18/18、CAS 1/1 PASS，四个权限变异体各只在目标契约失败，并有真实禁止结果。runtime 12／input-failures 11 的原 PASS 绑定 `0f754a6d`，没有重跑；原版本至新冻结提交的 src/app/hooks 无变化。原 worker-inbox 空回执失败保持 INCOMPLETE，夹具修复的最小红／绿见 [诊断](WORKER-INBOX-DIAGNOSIS-02.md)。这些证据不替代本包的真实 Claude CLI hook 行为或新候选独立 reviewer。

## 两套全新实例

| 项目 | 正例 clean | 反例 block |
| --- | --- | --- |
| 材料 | [p1-materials-09a3r](p1-materials-09a3r/approval.json) | [p1-materials-09a3r-block](p1-materials-09a3r-block/approval.json) |
| 根 | `/private/tmp/t078-2-p1-09a3r-1t5lartp` | `/private/tmp/t078-2-p1-09a3r-block-58xp7gc_` |
| task | `t078-p1-09a3r` | `t078-p1-09a3r-block` |
| launch | `da1c185b-c207-4736-8eb4-64d09809e2e6` | `94dd894e-4071-46e2-88d3-7f6b3872f69f` |
| session | `ce8a30e5-9e0a-4d54-b0fa-9b13aeb69593` | `6b09a7fc-7170-46b0-950e-208e7e5ad89b` |
| thread | `fe306788-07ec-4196-99e8-58a6fcbbcaf7` | `3829ca94-2109-4a4d-a201-b73c87f705e2` |
| 主 Messages 独立预期 | 两次，第二请求末条 user 文本精确为登记标记＋nonce2 | 一次，拼接 UPS2 被阻断，不能发 API2 |

每套提交与主 Messages 请求上限均为 2，模型上限为 0。反例预算 2 不表示允许它通过验收时发 API2：真实阻断 hook 完成后的 2 秒观察期内必须仍只有 API1。四个 nonce 与各自 HOME、根、task、launch、session、thread 均独立，未复用旧运行身份。

各包 `approval.json` 保存完整 CLI／shell argv、环境与 hooks；`control-plane.json` 保存控制端环境、假 API 和动态端口解析；`scenario-driver.json` 保存 launch／continue／slot-cleanup argv。CLI 固定 `/Users/luckye/.local/share/claude/versions/2.1.296`，Haiku 5.5／low／manual；隔离 HOME、CLAUDE_CONFIG_DIR、TMPDIR、ZDOTDIR 与 Electron user-data。只用公开假 token，未复制用户凭据；禁标题、theme=dark、空 MCP、debug-file、hooks timeout 3 秒。不更换参数或 CLI 版本，不写全局配置。假服务只绑定 `127.0.0.1:0`，运行时仅允许实际端口改变 `api_url` 与 `ANTHROPIC_BASE_URL`。

## 当前只申请正例 launch

材料提交完成后，正例 launch 仍需主控单独批准：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-09a3.sh 09a3r clean launch
```

该阶段范围是冻结材料中的 `--version`／`--help` 预检、假 API、隔离 repo 初始化、后台及交互 CLI 启动，并经启动参数安装已列出的 hooks。输入与按键预算 0，不打开 Electron，不声明首屏或 readiness。提交脚本不执行这个命令；本包生成也没有执行它。

## 逐屏引导与信任审批

每次先保存、阅读当前原字节，再把 `screen-key-approval-template.json` 填成对应 `approvals/SCREEN_ID.json`，一次只批准一个键：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-09a3.sh 09a3r clean screen SCREEN_ID
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-09a3.sh 09a3r clean key SCREEN_ID KEY PURPOSE
```

SCREEN_ID 每次使用新值。模板绑定当前 launch／session、隔离 repo、原 screen 文件、按键、用途、导航后选中目标、批准人、引用及依据。沿用 08e 逐屏流程：若出现 theme，ArrowUp→Auto、读回，再 ArrowDown→Dark、读回，再批准 Enter；Security notes 必须逐字匹配本包冻结 notice，才单独批准 Enter；workspace-trust 先批准 ArrowDown→Yes、读回选项，再单独批准 Enter。若当前屏幕已满足某项，不发送多余按键。没有默认 Enter、Digit1 或自动补键；新权限、认证、共享、遥测或不同屏幕即停，保留现场并报主控。

主提示符实际出现后，另填 `readiness.json`（confirmed_by=executor、readiness=confirmed、basis）及 `actions-approval.json`（approved_by=executor、approval_ref、basis）。它们只作用于当前实例，所有模板现在均未批准。正例动作列表为 Escape、manual-draft-handling、empty-declaration-release；反例为 Escape、retain-draft、false-empty-declaration-release。反例不继承正例信任或 readiness。

## 另批 continue：Esc、用户处理草稿、声明空框

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-09a3.sh 09a3r clean continue
```

continue 才构建本实例 slot、打开隔离 Electron、首次放行并注入 nonce1。驱动核对 CR1／UPS1／API1／busy、nonce2 仅登记排队，以及窗口 launch／thread／active／input-enabled；Escape 只发一次。同 window／request／sequence 的 action、准入、写入意图、实际写入及提交退休都成立后，才确认 Esc 送达，并核对 API1 取消、busy／interrupted 与队列 held。

出现 `manual-draft-handling` 输出与 before-user-release 截图后，主控有 180 秒在这一隔离窗口亲自处理恢复的草稿。看到输入框确实空了，保存空框画面及操作依据，再点击“输入框已空，放行”。驱动不代发清空键、不自动点声明；后台不删字，user_draft 不是对 CLI 编辑框的观测。控制字节记 control action，普通输入按实际通路记录；声明文字必须是“用户声明输入框已空”，引用该 Esc 的中断收据与当前输入代次。

正例要求：Esc 与声明之间有单独记录的草稿处理；声明与释放事件引用一致；第二 paste＋独立 CR、新 prompt_id、exact API2、唯一 Stop2、idle、P2_ACK 与截图成立，三份真实 hook 均 exit 0。假 API 对正文的 exact oracle 不放宽；不裁剪、不容忍拼接、不自动重送。输入或组合事件之后的旧声明必须拒绝，入口红绿已有覆盖；真实系统 IME 仍未验证。手打且未登记为注入的提交不套用错配拦截，Stop 保持原行为。

## 反例独立批准：保留恢复草稿并验证阻断

正例另批 cleanup、确认实际退出后，才提交反例 launch 审批：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-09a3.sh 09a3r block launch
```

反例独立走 screen／key／readiness／actions-approval／continue；将上面各命令的 clean 改为 block。到 Esc 后 held 画面，主控保存第一提示确实恢复在编辑框的证据，保留它，再在本反例里点击声明按钮。这是特意不真实的空框声明，用来检验用户声明的局限及提交前阻断。驱动不代点，不自动清空、裁剪、重送或恢复。

反例要求：真实 UPS2 prompt 同时包含两条 nonce；diagnostic 绑定 dispatch2／submission；hook 原始 stdout 是 JSON `decision: block`，exit 0；假 API 总数保持 1，无 API 错误，无第二 turn_start／Stop，仅两次提交写入。真实阻断 hook 完成后继续观察 2 秒无 API2，并保留拼接 prompt、hook 原件、库事件、PTY 与截图。这只证明本次有界观察，不称一般可靠性。缺证、未知、实际出现 API2、自动重投或超时均 INCOMPLETE，保留现场。

## 分别批准清理，不包含在 launch 中

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-09a3.sh 09a3r clean cleanup
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-09a3.sh 09a3r clean slot-cleanup
# 反例改成 block，仍需分别批准。
```

cleanup 核对本实例 manifest 的 CLI、API、后台退出，保存本根归档后才删除自己的根；不能以 cleanup 覆盖实验失败。slot-cleanup 是后续独立阶段，绑定 `t078-09-<各自 launch>`。现有 slot 脚本核对来源、Electron quit 与 PID 退出，保存文件名／大小清单后删精确 slot，**没有归档 slot 内容或逐字节读回**；旧包对此的文案不准确，已另报主控。它不是 launch 的授权内容；主控到清理阶段再决定是否先另行归档或修清理脚本。本轮不改该脚本、也不执行删除。当前两个 slot 均未创建。不碰共享 checkout 构建输出、其他 slot、旧 09A-2 slot 或用户应用；缺外置盘即停，不回退。

普通状态期限 30 秒、构建 90 秒、手动草稿处理 180 秒；无自动重试。单文件超 5 MiB 时保留原件，交主控外置归档并逐字节读回，不能删失败或改写为 PASS。

## 准备证据与提交

[生成记录](preparation-generation-09a3r/result.json) 与[静态核对](preparation-check-09a3r.json) PASS：两包各 76 个冻结文件与当前源码逐字节相同；独立身份、隔离设置、固定 argv／hooks、未批准模板、未启动状态、语法、TSX 内存转换与 project-map status 均通过。[最终交付核对](materials-delivery-check-09a3r.json) 9 项 PASS，另确认版本晚于 567d7748、身份／nonce 不复用旧包及文案与实际动作一致。再次只读检查须使用新输出文件：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/check-materials-09a3.py --generation 09a3r --output /绝对路径/新准备检查.json
```

主控以原 worker 启动身份运行材料提交脚本，钩子自动生成尾注；脚本只提交，不 launch：

```sh
sh /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/commit-materials-09a3r.sh
```

新候选独立 reviewer、真实 clean／block、09B／09C、真实 IME 和真登录仍 INCOMPLETE。整票保持 open，不关闭、不验收／集成、不 push。本包的静态 PASS 只代表准备就绪。
