# 材料 09A-2：窗口就绪与 Esc 送达核验

本次只请求新实例 launch 审批；CLI／假 API／Electron／构建均未启动，真实模型预算为 0。场景范围仍为 [PLAN-09](PLAN-09.md) 的 A1～A6，双主控与紧急停止 09B/09C 未完成，不删验收。T-077 合入后再变基、重新生成并完整重跑，本材料绑定变基前代码。

## 09A 失败的只读结论

原件及外置清单完整保留在 p1-materials-09 与 [archive manifest](external-archive-578c9fe0799847c19ce5020b5ec503d0.json)。[完整读回](readback-09a-complete.json) 从指定归档成员读取 SQLite 与 pty.raw：用户输入表为空，没有 Esc 写入意图、写入收据或 Claude 提交退休；UPS1 与 dispatch1 已建立，第二 dispatch 登记并排队。Esc 未被后台接收／写出。

两处根因：驱动在首个渲染快照前就发键，返回 sent:true；其后 31 个后台快照仍全部 input_enabled=false，其中 30 个已 busy 并正确绑定 dispatch1。main.ts 把 nullable 主控的 attempt=null 与 current_attempt 空值取出的 undefined 比较，永久禁用输入。API peer 于 05:28:12.423742Z 关闭，属于 cleanup 时段，不能归因于 05:27:23.792Z 的 Esc 尝试。窗口输出 20,591 字节等于归档 pty.raw（21,778 字节）的前缀；二者都是 PTY 输出，输入事实以数据库动作及写入收据为准。

产品修复独立提交 `7cd19b586fe757268384d99f243f5d0a583a5ad3`，[最终 diff](binding-fix-final-09a2.diff) 交主控审。运行中的 nullable controller 允许输入；worker 当前 attempt 条件保持，后台逐次凭据／task/spec/native leader 校验不改。前端同一快照渲染 launch/thread/active/input-enabled 属性，驱动读这些已渲染值，不拿一次独立后台查询冒充窗口接通。

发 Esc 前，runner 等窗口本 launch/thread、running、busy、active=dispatch1 且输入可用；驱动在发键边界再核对相同条件，未接通／错窗格／错 active／禁输入均不发键。只返回 attempted:true。之后必须观察同一 window_id/request_id/sequence 的用户 terminal-key action、window_request_admitted、terminal_input_write_intent（Esc 一字节）、terminal_input_written、该 dispatch 的 user-esc 退休，且事件顺序正确，才能继续核对 active=null 和 API peer 取消。sent:true、active 单独变空或 cleanup 关闭连接都不能单独证明送达。

原运行时夹具的 Esc 调用也传明确绑定并等待渲染，没有保留不带身份的并行驱动入口。其他菜单用途、信任按键、参数、hooks 3 秒、假认证及预算不变。

## 红态、静态绿态和反例

- [起点红态](window-binding-red-09a2/results.json)：真实 09A 快照使主控窗口只读；未连接、错窗格／active、禁输入的模拟窗口仍会被驱动发键并宣称 sent。此检查执行生产快照谓词与真实驱动分支，不启动 Electron。
- [最终静态检查](fix-static-09a2/result.json)：同一域／驱动检查 8/8；main/driver 语法、renderer 的 Vite/Oxc 内存 TSX 转换通过，未构建或写缓存。后台窗口身份检查 [5/5](controller-window-green-09a2/results.json)，worker stale attempt 与主控 spec/native 身份拒绝不放松。
- [收据检查](window-receipts-green-09a2.json) 12/12；只有完整同请求事实能确认，缺动作／准入／意图／写入／退休或身份错配都不能确认。
- [已知坏变异](window-receipts-mutant-09a2.json) 补造缺失写入收据，真实触发四项假送达判断（缺 written、错 request/window/sequence）；退出 1，原件保留。这是合成事实反例，不冒称真实 PTY 写入。
- [冻结静态检查](p1-preparation-check-09a2.json) PASS，73 个源码文件逐字节核对；隔离目录、两条场景、未批准模板、无 CLI 内部状态、syntax、原 notice、尺寸与 project-map status 均通过。实际 09A-2 尚未运行，结论 INCOMPLETE。

## 新实例与准确启动材料

实例 `/private/tmp/t078-2-p1-09a2-sm_du7jo`；task `t078-p1-09a2`；launch `d2d9c666-5621-4467-bbe4-d99450bd5503`；session `8fdb0112-15fe-4a99-b30a-08bcfcae7f5e`；thread `95a6c301-33dc-4944-a7d4-3a5e764bef9d`。角色仍为实际 ideation CLI，executor 控制端经 operator 凭据操作；没有冒称两个实际主控。

完整 CLI/shell argv、环境白名单、角色、追加 hooks 见 [approval.json](p1-materials-09a2/approval.json)；控制端／API argv、动态端口与隔离路径见 [control-plane.json](p1-materials-09a2/control-plane.json)；实际构建／Electron／continue argv 见 [scenario-driver.json](p1-materials-09a2/scenario-driver.json)。CLI 固定 2.1.296，Haiku 5.5/low/manual、公开 ANTHROPIC_AUTH_TOKEN、禁标题、theme=dark、debug、空 MCP，hooks timeout 3 秒；不使用 IS_DEMO/--bare、不改其他参数、不换版本。

HOME、CLAUDE_CONFIG_DIR、tmp、Electron user-data 全位于本隔离根；repo 初始只含 value.txt。无 CLI 内部状态、无用户凭据读取／复制，不碰用户 ~/.claude。API 启动时绑定 127.0.0.1:0，实际端口写 runtime-manifest；静态端口 0 不是实际启动地址。只有该运行端点允许变化，源码／nonce／角色／argv/env 其他值逐字节固定。

真实模型预算 0，根提交和主 Messages 请求预算各 2。第 1 请求只观察真实取消；第 2 请求只回声明的 P2_ACK/nonce2。launch 发键／输入 0，后续逐屏批准与 continue 才允许对应输入。

## 只请求 launch 批准

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-launch-09a2
```

launch 只记录启动，不声称首屏稳定。首屏与每次按键结果通过单独只读阶段保存原字节：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-screen-09a2 SCREEN_ID
```

逐屏把 [模板](p1-materials-09a2/screen-key-approval-template.json) 填入 approvals/SCREEN_ID.json，绑定当前原字节、目录、按键、用途、目标项、批准人／引用／依据，然后单独审批：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-key-09a2 SCREEN_ID KEY PURPOSE
```

同 08e：theme ArrowUp→Auto、ArrowDown→Dark、读回后 Enter→Dark；固定 Security notes 逐字相等才 Enter→Continue；workspace-trust ArrowDown→Yes、读回后 Enter，一次。无默认 Enter/Digit1/自动补键；同屏一次。涉及新的权限、认证、遥测、共享或不同提示即停。真登录阶段用户 HOME 出现任何引导屏一律停下，不按键。

到实际主提示符后另填 readiness.json 与 [动作批准](p1-materials-09a2/actions-approval-template.json) 的 actions-approval.json；批准动作是 fixture 自动化 Escape 与 queue-release，不能冒称用户本人亲手输入。之后另批：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-continue-09a2
```

A1：nonce1 paste+CR/UPS1/主请求1/busy/active1；A2：busy 中登记 nonce2、排队且未写出；A3：窗口绑定和 Esc 的实际五类收据/active 释放/API1 取消/busy-interrupted-held/无提前第二请求；A4：截图后放行按钮、库 user action 唯一；A5/A6：paste+CR2/UPS2 独立 prompt ID/主请求2/唯一 Stop2/idle/三份真实 hook 原件 exit 0/ACK2/截图。每一步缺证或矛盾即停，不补输入、不重试。

普通观测与窗口就绪各 30 秒；构建 90 秒；第一取消最多 90 秒、第二响应屏障 60 秒。不接通、禁输入、未写出、错误身份、提前送达、hook 失败／错回合、第三请求、未知写入或超限文件都为 INCOMPLETE；不把 cleanup 的连接关闭当取消成功。

最后另批 p1-cleanup-09a2，确认 manifest CLI/API/后台退出后归档，仅删除自己的实例。单文件 >5 MiB 停下报告，由主控外置并字节读回。

## Electron slot 清理归属

旧 slot `/Volumes/WD-Elements/a2a-workbench/t078-09-12a5d58e-29fd-4c81-addc-a2b9a168abd8` 由本 worker 的 09A continue 创建。归属由实际 build manifest.source（本 worktree/app）、continue/result 的 electron_build、Electron argv 的 --build 与 launch 共同确定。worker 负责提供清理脚本；执行主控在沙箱外运行。本轮没有删除它。

已准备独立清理命令，不能混成 launch 的隐含副作用：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-slot-cleanup-09
```

脚本须先见该实例 cleanup PASS、实际 Electron quit 原件及记录 PID 当前不存在，再保存 build manifest／文件尺寸清单／源快照路径，才删除这个精确 slot。外置盘未挂载、路径含链接、来源错配、PID 存活／重用或退出不明均 BLOCKED，既不删除也不发信号。其他 slot 不碰。旧输入／状态／屏幕／运行证据及外置 fixture 原件保留。

新 slot `t078-09-d2d9c666-5621-4467-bbe4-d99450bd5503` 仅在另批 continue 时创建；同样由本 fixture 所有，在 p1-cleanup-09a2 完成后，另批 p1-slot-cleanup-09a2 删除构建产物，原源码和运行证据仍保留。

## 静态重放

```sh
python3 -B evidence/2026-10-11-batch13/T-078/readback-09a.py --output /绝对路径/新读回.json
node workbench/tests/test_t078_window_binding.mjs /绝对路径/新域检查目录
python3 -B workbench/tests/test_t078_window_receipts.py --output /绝对路径/新收据检查.json
python3 -B workbench/tests/test_t078_window_receipts.py --mutant-no-write --output /绝对路径/新反例.json
python3 -B evidence/2026-10-11-batch13/T-078/p1-check-materials-09a2.py --output /绝对路径/新冻结检查.json
```

本次生成命令 `python3 -B evidence/2026-10-11-batch13/T-078/prepare-materials-09a2.py` 记录在生成报告；不可覆盖已存在的材料目录。变基后必须用新标签、新实例、新 ID、重新审批并完整重跑。T-078 仍 open、INCOMPLETE、待主控关闭；未 push、未 rebase、未启动真登录或新假服务探针。
