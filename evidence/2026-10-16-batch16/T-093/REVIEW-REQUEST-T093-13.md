# T-093 完整派发文本精确比对与共享调用点回归交接 13

**INCOMPLETE：夹具 oracle 已修复，局部精确比对／IPC／状态回归通过；新 OS primary、green、六场及跨票恢复集成回归待执行。**
候选绑定最后 `T-093 FROZEN <完整 SHA>`。task T-093 / attempt a1，worker s16-t093；受管 session 67f986cc-92e4-4089-9c22-802a1143b645，native session 01a14ae2-a3df-7731-a7b0-1b679b3bce95，launch launch-45148b6732394eccab3b21224b238513。
本次不改产品源码、profile、门禁或假 CLI；不运行真实 CLI、认证、上游或模型。
实现冻结 ed2e57d0ad43c533612549db90132761f684feab 的限定独立审查见 [MANAGED-PROMPT-REVIEW-01.md](MANAGED-PROMPT-REVIEW-01.md)。局部精确 oracle 与反例通过；总状态 INCOMPLETE。审查后仅补文本证据并更正下表的方法名，运行代码未改。

## 原因与精确合同

主控 #111 的 cb1208a0f primary 已通过真实 C/libproc 前台身份，独立上游收到两条 POST /v1/messages、bearer 匹配、400／200；收尾完整。
失败为旧上游 oracle 把发送后的完整消息与未包装的 fixture.prompt 比较。不是模型选择了其他 prompt，也没有证据指向 UTF-8、system 或消息位置变换。

规范源 native-cli-orchestration-2026-10-10.md:88、125 要求派发带 `⟦主控 #序号⟧`。
真实链为 store.register 加 `⟦主控 #1⟧\n` → Panes.drain 逐字括号粘贴 → 编译假 CLI 去掉终端包装 → Python peer 将原文本置于 messages[0].content。
原件只有布尔收据，未保存请求正文；不能补称从原件直接读回了文字。源码数据流、真实 hook 已接受该派发、局部真实 dispatch 检查和字节数一致支持此定位：未包装 JSON 为 218 字节，完整派发 JSON 为 247，原两条实际 body 均为 247。
摘要见 rehearsal-03-primary-summary.json；旧错误／原件保留，不覆盖。

修复预期在 R 中根据外部合同和本次随机输入构造：
`{"messages":[{"role":"user","content":"⟦主控 #1⟧\n" + 原输入}]}`。
本轮原输入无末尾换行。这个新库的第一条 dispatch 必须为 #1。预期不从生产 register 返回值、PTY 读回或上游正文复制；实际返回只与已存在的预期比较。
独立 U 对**整个解码 JSON 对象**精确相等，包括完整消息数、role、content 和字段；不做包含、trim、大小写、换行或 Unicode 归一化。
JSON 编码／缩进不同但解码结构相同可以通过；content 内部字符差异一律失败。新增 system 字段、额外消息或键、错误序号／role、CRLF、内部空白和末尾换行差异均拒绝。
收据只写结构布尔值、类型、数量和长度，不写正文、头或认证；仍先脱敏后进入公开证据。C 与 V 保留全部原路由／认证／计数／清理断言，并新增结构事实核对。

## 局部证据

- upstream-prompt-red-02：同一实际 U.do_POST 在旧 oracle 上拒绝完整合同正例；green-02 共 13 项通过，含独立 R 预期、随机多行 Unicode 输入和各结构反例。
- upstream-content-only-mutant-01／upstream-contains-mutant-01：只比第一条内容或使用包含的错误修法均被业务断言拒绝。
- managed-prompt-green-01：实际 Panes.dispatch／store／PTY 写入四项精确断言通过，未启动真实 PTY、CLI 或网络。
- T-091 IPC 11 项及其旧版本反例、版本合同 8 项和去版本比较变异通过；T-078 runtime 11 项、controller relay 22 项通过。详情为 t091-ipc-regression-01、t091-version-regression-02、t078-runtime-regression-01、t078-relay-regression-01。

以上都是 L1／给定外部边界。当前产品与 cb1208a0f 一字未改，原 primary 的 OS 身份／计数／清理事实仅按实际到达阶段报告，不冒称 green 或完整反例通过。

## processInfo 影响范围

这是一项全 pane 产品变更，不能只验 T-093 的正常登录。以下为当前候选的全部直接调用，其他路径经这些入口间接依赖它：

| 调用点 | 影响行为／回归 |
| --- | --- |
| daemon.ts:38 settleInboxFeedback | 延迟收件箱反馈的会话／leader 重查；T-078 relay、T-093 两次 hook/Stop |
| daemon.ts:148 window assertCurrent | 主控窗口输入、composition、放行的身份；T-091 IPC 与 T-078 输入/空声明 |
| daemon.ts:251 pane_process_info | 对外进程事实命令；observer、alias 及实际 C primary |
| panes.ts:487 sendGateFeedback | worker／主控反馈队列身份；conflict_panes 与 relay |
| panes.ts:647 releaseByUser | 用户声明空输入后的放行；pane_runtime、empty_declaration_entry |
| panes.ts:670、675 interruptThread | 中断前及写入前两次核对；pane_runtime、输入竞态 |
| panes.ts:693 release | 初始化放行；primary、T-096 就绪放行 |
| panes.ts:735 screenKey | 启动按键前台身份／原屏幕绑定；T-078 startup_pending 与 T-096 引导 |
| panes.ts:877、882 caller/controller | 原生 Stop 请求和执行前重查；controller_relay、T-093 完整链 |
| panes.ts:894 caller/worker | 受管 worker 活动身份；pane_runtime／旧门禁套件 |
| panes.ts:901 readThread | worker 存活／结束／替换；conflict_panes／runtime |
| T-096 recover(daemon) 的 openPanes 循环内 processInfo（其冻结来源约 265 行） | 恢复后是否真正得到原 CLI；完整 argv、旧记录、版本、session、兄弟隔离回归 |

T-091 的六条 IPC 合同不变：snapshot、input、composition-start、release-queue、focus-observation、output。
每个进程只注册一次，全窗格按 sender＋pane key 分流；各 pane 独立 window_id／sequence／输出游标；iframe／跨窗 key、错 task／旧 launch、重复 launch 均拒绝，拒绝前不发凭据；关闭竞态不影响别窗。
IPC mock 不证明底层进程查询，必须同时看 observer／alias 及真实 C primary。

## 回归命令

以下输出必须不存在。前四条已在本候选局部运行通过；是纯合同／SQLite／给定进程边界，不启动 vendor、daemon 或真实进程查询。

```sh
node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs /private/tmp/t093-r13-t091-ipc.json
node --experimental-vm-modules workbench/tests/test_t091_claude_version.mjs /private/tmp/t093-r13-t091-version.json
node workbench/tests/test_t078_pane_runtime.ts /private/tmp/t093-r13-t078-runtime
node workbench/tests/test_t078_controller_relay.ts /private/tmp/t093-r13-t078-relay
node workbench/tests/test_conflict_panes.ts --product "$PWD" --output /private/tmp/t093-r13-conflict.json
node workbench/tests/test_t093_process_observer.ts /private/tmp/t093-r13-observer.json
node workbench/tests/test_t093_process_alias.ts /private/tmp/t093-r13-alias.json
```

runtime／relay 读取各目录 results.json；其余读指定 JSON。均要求 rc 0／PASS，无失败／跳过，原变异仍命中业务断言。
T-078 有真实 socket／hook 的补充入口，需执行主控在沙箱外用其隔离夹具规则运行，未在本轮 worker 执行，不以 mock 代替：

```sh
node workbench/tests/test_t078_empty_declaration_entry.ts /private/tmp/t093-r13-t078-empty-entry
node workbench/tests/test_t078_dispatch_newline_signal.ts green /private/tmp/t093-r13-t078-newline
# 捕获的原材料需先按归档清单恢复到外置盘，不生成替代屏幕／stdin：
node workbench/tests/test_t078_startup_pending.ts /private/tmp/t093-r13-t078-startup "$startup_materials"
node workbench/tests/test_t078_claude_epochs.ts /private/tmp/t093-r13-t078-epochs "$hook_materials"
```

前两条只有本场 daemon／hook 与模拟 PTY/进程身份，不调用模型。后两条需主控指定已核对的原 captured-screen／hook 材料目录；缺材料即 INCOMPLETE。

## T-096 的跨票集成前置条件与命令

本 worktree 不含 T-096 实现；只读核对来源为 exec/t096 的 d61876fe29916ccf577da7b9b912cf305d9fdd9d。没有修改或重放另一票 attempt。
已确认集成检查项，见 [ISSUE-T096-INTEGRATION.md](ISSUE-T096-INTEGRATION.md)：恢复入口直接复用旧 record，而旧记录无 executable_path；不能让新查询把合法旧会话误判成缺 leader。
应在已有恢复版本校验后、PTY 启动前确定运行时规范身份，原启动记录不可变、原 argv 不变；有旧身份字段时不得绕过目标一致性。测试 subprocess／realpath 替身需映射实际新协议，不能删业务断言或直接固定 leader 成功。

以下只能在**同时包含两票的受管集成候选**运行；本票当前分支不能运行，也没有其通过证据：

```sh
node --experimental-vm-modules workbench/tests/test_t096_restore.mjs /private/tmp/t093-r13-t096-restore.json
node --experimental-vm-modules workbench/tests/test_t096_daemon_restart.mjs /private/tmp/t093-r13-t096-daemon.json
python3 -B workbench/tests/test_t096_process_probe.py /private/tmp/t093-r13-t096-probe.json
```

必须保留：旧启动记录、完整原 argv、版本／session／缺 argv 拒绝、一个窗格失败不影响其他、worker 保持未恢复且 attempt 不变、未放行时不写提示；去完整 argv 与版本等变异仍失败。
原 T-096 原生 runner 还会在自己的 evidence/T-096 目录写 label.run.json 文本摘要。下列两条属于执行主控的 T-096／跨票回归范围，本 T-093 worker 不执行、不写该目录；外置盘输出也不能取代该范围核对。

纯合同通过后，再沿 T-096 RUN-RESTART 的既有逐屏审批／隔离／收尾规则，用新标签在外置盘做三格＋失败隔离真实入口回归。示例（仅执行主控，CLAUDE 为已核对路径，不登录、不发模型提示）：

```sh
python3 evidence/2026-10-16-batch16/T-096/run_restart.py --source "$PWD" --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-093/t096-r13-three --label t096-r13-three --approval-ref 'T-093 processInfo 跨票回归' --claude "$CLAUDE" --claude-version 2.1.302 --panes 3 --expect restore --startup-wait-seconds 600 --check-close
python3 evidence/2026-10-16-batch16/T-096/run_restart.py --source "$PWD" --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-093/t096-r13-isolation --label t096-r13-isolation --approval-ref 'T-093 processInfo 跨票回归' --claude "$CLAUDE" --claude-version 2.1.302 --panes 3 --expect restore --startup-wait-seconds 600 --fault missing-argv
```

沿用原规则，命令文本不预先批准任何 Enter／信任／登录屏；真实 POST／模型必须为 0，正常收尾和历史／argv／task／attempt 原件均须核对。缺材料、权限或审批时保留 INCOMPLETE，不以原 T-096 PASS 背书。

## 先重跑 T-093 primary

修复后的严格 oracle 用全新输出；此命令只合成 auth／编译假 CLI／本地假上游，profile 不变：

```sh
repo=/Users/luckye/Documents/Code/a2a-wt-t093
candidate=替换为本次完整冻结SHA
bash "$repo/evidence/2026-10-16-batch16/T-093/REHEARSE-CHAIN-01.sh" \
  "$repo" "$candidate" /private/tmp/t093-rehearsal-04-primary.json primary
```

期望 rc 2／INCOMPLETE，但 primary_failure 恰为 rehearsal_primary_probe、两条 receipt.prompt_matches_fixture=true，structure 精确标志全成立，upstream_requests=2、cleanup_failures=[]、fixture_removed=true。
错误不同即停，回传结构诊断／主失败，不继续 green／六场。不要保存请求正文或凭据来诊断。
primary 达到预期后，按请求 12 的 green／V 命令改用 rehearsal-04-green、rehearsal-04-check；再运行尚未执行的正式 chain-07 六场。
本请求不代替独立验收、submit 或集成。跨票恢复项未验证前，不给出全 pane 非退化或集成 GO。
