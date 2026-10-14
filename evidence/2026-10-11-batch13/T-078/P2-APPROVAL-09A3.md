# 09A-3：空框声明正例与拼接阻断反例

**主控 #135 更新：本包绑定变基前代码，仅留档，不用于 launch。** T-077 已合入 main；本批材料提交后，先将 exec/t078 变基到最新 main，再用全新标签、根和身份重新生成与静态核对，另交新 launch 审批。以下命令是本包的日期记录，不是当前启动授权。

2026-10-14，主控 #130／#131／#133。**材料准备 PASS，实验与整票验收 INCOMPLETE。** 本轮只交 launch 审批材料，没有启动 CLI／API／Electron／构建，真实模型预算与实际消费均为 0；没有额外 Codex／子代理。两套夹具串行运行，正例退出与归档后才另批反例，不能同时启动。

原证据提交 `c80cecd6cd4cc7dfdf816022db02c0f600f253d5`；本候选代码提交 `c1c6b53a8419e35ad0dee5a79abf6adc4c37f08c`。主控已核对并停止遗留的本地 Node 测试 helper。修复、原失败及限定红绿证据见 [IMPLEMENTATION-09A3](IMPLEMENTATION-09A3.md)：最终入口 17/17 PASS，真实 vendor 与 PTY 边界尚待验证。新候选没有独立 reviewer 的通过结论；不借用旧审查。

## 两套独立实例

| 项目 | 正例 clean | 反例 block |
| --- | --- | --- |
| 材料 | [p1-materials-09a3](p1-materials-09a3/approval.json) | [p1-materials-09a3-block](p1-materials-09a3-block/approval.json) |
| 根 | `/private/tmp/t078-2-p1-09a3-s86zm2yy` | `/private/tmp/t078-2-p1-09a3-block-wk7vopkk` |
| task | `t078-p1-09a3` | `t078-p1-09a3-block` |
| launch | `d7229b5d-8b8b-4bd8-bedf-a1034843c448` | `f42d3adf-0791-4233-a3b6-5d0f5532a29a` |
| session | `fcae11a8-500b-4634-aa83-1d97f79fc42b` | `242eb811-5b17-4b37-bcb1-9cad9ad0f34e` |
| thread | `20c3c123-48cb-4080-8cf4-e08b68ab523c` | `b2f9a3a7-629e-4a03-adbd-9cf11e5dcfa1` |
| 主 Messages 独立预期 | 两次，第二正文只含登记的 nonce2 | 一次，拼接 UPS2 被阻断，不能发 API2 |

每套根提交与 Messages 请求上限均为 2，模型上限为 0。反例上限不是要求它发第二次请求；它必须在真实阻断 hook 完成后的 2 秒观察期内仍只有 API1。两套 nonce、根、task、launch、session、thread 都不同；不复用 09A-2 进程或证据。

完整 CLI/shell argv 与环境、hooks 在各自 approval.json；控制端/API 及动态端口在 control-plane.json；构建、continue 与 slot 清理 argv 在 scenario-driver.json。CLI 固定 2.1.296，Haiku 5.5/low/manual；隔离 HOME、CLAUDE_CONFIG_DIR、TMPDIR 与 Electron user-data；公开假认证 token；禁标题、theme=dark、空 MCP、debug-file、hooks timeout 3 秒。不复制凭据，不写用户全局配置，不换参数／CLI版本。静态端口 0 由本次假服务绑定 127.0.0.1:0 后解析；运行时只允许实际端点变化。

## 只提交正例 launch 审批

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-09a3.sh clean launch
```

该阶段包括 approval.json 列明的 `--version`、`--help` 预检、假 API、后台及交互 CLI 启动；输入／按键预算 0，不启动 Electron，不声称首屏或 readiness。以上都是待批步骤，本 worker 未执行。

逐屏读原字节，再填对应 approvals/SCREEN_ID.json，逐次批准一键：

```sh
bash evidence/2026-10-11-batch13/T-078/outside-09a3.sh clean screen SCREEN_ID
bash evidence/2026-10-11-batch13/T-078/outside-09a3.sh clean key SCREEN_ID KEY PURPOSE
```

模板绑定当前 launch/session、隔离 repo、原 screen 文件、按键、用途、导航后目标项、批准人、引用与依据。沿用 08e：theme ArrowUp→Auto、ArrowDown→Dark，读回后 Enter；Security notes 必须逐字匹配冻结 notice，再批准 Enter；workspace-trust ArrowDown→Yes，读回后批准 Enter，同屏一次。没有默认 Enter、Digit1 或自动补键。新权限、认证、共享、遥测或不同屏幕即停；只操作本次隔离应用窗口。

实际主提示符出现后，另填 readiness.json 与 actions-approval.json。模板尚未批准。正例动作列表是 Escape、manual-draft-handling、empty-declaration-release；反例是 Escape、retain-draft、false-empty-declaration-release。这不是丢弃草稿或后台清空授权。

## 另批 continue：主控亲自处理草稿及声明

```sh
bash evidence/2026-10-11-batch13/T-078/outside-09a3.sh clean continue
```

continue 才构建本实例 slot、打开 Electron、首次放行和注入 nonce1。驱动依次核对 CR1／UPS1／API1／busy、nonce2 仅登记排队，以及窗口 launch/thread/active/input-enabled。受控 Escape 只发一次，必须从同 window/request/sequence 的 action、准入、写入意图、实际写入和提交退休确认送达，再观察 API1 取消及 busy/interrupted/queue held。

到 `manual-draft-handling` 输出和 before-user-release 截图后，驱动最多等待 180 秒。主控在这一个隔离窗口自行保留、修改或清空恢复的 CLI 草稿，看到输入框确实空了，再点击“输入框已空，放行”。保存清空后的画面和实际操作依据。驱动不代发 Ctrl+C/U/S、Esc 等清空键，不自动点声明；不能把后台 user_draft 当编辑框观测。界面按键仍经同一 window 输入通路记录为实际 action/message；放行记录文字必须是“用户声明输入框已空”，绑定中断收据和当前代次。

正例要求：Esc 与声明之间存在单独记录的草稿处理；声明与释放事件关联一致；第二 paste+独立 CR／新 prompt_id／exact API2／唯一 Stop2／idle／ACK2 与截图成立，真实三份 hook exit 0。API 的 exact 正文 oracle 未放宽。新输入／组合事件后的旧声明不得放行；这些竞态由入口红绿证明，真实系统 IME仍未验证。

## 独立反例：保留恢复的草稿

正例完成并另批 cleanup、核对退出后，反例再独立批准：

```sh
bash evidence/2026-10-11-batch13/T-078/outside-09a3.sh block launch
```

反例仍单独走 screen/key/readiness/actions-approval/continue，不继承正例信任。到同样的 Esc 后 held 画面，主控确认并保存第一提示恢复在输入框的证据，保留它、不清空，然后在此夹具里点击声明按钮。这是一条特意不真实的空框声明，用来证明后台不能声称机器看到了空框、提交前阻断仍能保护登记注入。驱动不代点，也不自动裁剪、重送或恢复。

反例要求实际 UPS2 prompt 同时含两条 nonce，diagnostic 绑定 dispatch2/submission；真实 hook stdout 是 `decision: block`、exit 0；假 API 总数保持 1、无 API 错误、无第二 turn_start／Stop、只有两次提交写入。保留原始拼接输入、hook 原件、库事件、PTY 和截图。缺证、未知、实际出现 API2、自动重投或超时均 INCOMPLETE，保留现场。

## 清理与静态复核

每套分别批准 cleanup，确认当前 manifest 中记录的 CLI/API/后台退出，归档再删自己的隔离根；slot-cleanup 是后续独立批准，不能隐含在 launch 内。slot 为 `t078-09-<各自 launch>`，当前都不存在。缺外置盘即报错；不碰共享 checkout 输出目录、其他 slot 或旧 09A-2 slot。

```sh
bash evidence/2026-10-11-batch13/T-078/outside-09a3.sh clean cleanup
bash evidence/2026-10-11-batch13/T-078/outside-09a3.sh clean slot-cleanup
# 反例将 clean 替换为 block，并再次批准。
```

普通观测 30 秒、构建 90 秒、手动处理 180 秒；不自动重试。单文件超过 5 MiB 时保留原件，交主控外置归档和字节读回，不能把失败删除或改写为通过。

[静态复核](preparation-check-09a3.json) PASS：两套各 75 个冻结文件逐字节相同、独立身份、未批准模板、隔离设置、固定 argv/hooks、未启动状态、语法、TSX 内存转换和 project-map status（0 problems／0 stale）均通过。复跑只读检查：

```sh
python3 -B evidence/2026-10-11-batch13/T-078/check-materials-09a3.py --output /绝对路径/新准备检查.json
```

独立 reviewer、8/9/18 整体验收、09B/09C、真实 IME、真登录和变基后重证仍 INCOMPLETE；本包不替整票验收背书。T-078 保持 open，待主控关闭，不 push。
