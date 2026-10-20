# T-108 / a1：无模型完整入口 PASS，整票 INCOMPLETE

分支 exec/t108，起点 6411bdff8482ba47da207efa6a295a12666222aa。未运行任何真实模型回合，model_calls=0、vendor_calls=0。CLI 原生交互探针只连接本地假 API，未使用正常登录。

## 主控 #6 复跑处置

旧入口 `/private/tmp/t108-native-e2e-01.json` 为 INCOMPLETE，保留原文件与夹具。失败在驱动第 3 次调用 prompt，尚未点击答复。驱动模板把 `\r` 展开为 JavaScript 字符串中的裸回车；独立解析复现 SyntaxError。已用 JSON.stringify 序列化终端字节，补 renderer-console.jsonl 和错误回执中的 console 摘要。选项禁用与所有原有断言保留。

局部验证：`node workbench/tests/test_t108_driver.mjs /private/tmp/t108-driver-fix-02.json`，PASS。相同解析路径拒绝旧的裸回车，候选驱动实际脚本可解析，写入字节严格等于 bracketed paste 和单独 Enter。它不替代 Electron 入口复跑。

清理实际执行了 daemon_stop 且移除了 daemon.pid；遗漏的是原生 CLI 的退出核验。产品 terminate 对 controller/worker 只等待 PTY shell，未像 shell 窗格一样确认子进程，CLI 的独立进程组可能存活。范围外缺口已报 triage：20261020T055224Z-worker:s18-t108-issue-001。未改产品关闭或门禁语义。

处置脚本先检查完整 session、debug 路径、启动时间、PID 和 argv，再向准确的测试 PID 发信号；PID 被复用或归属无法核实时拒绝，不删除旧夹具。新的入口 finally 绑定本次捕获的原生 CLI／daemon 身份，清理后确认两者退出；摘要填入 model_calls、vendor_calls 与假 API 请求数。Electron 未退出时保留构建目录。

交主控执行，结果均待回传：

```sh
zsh evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-CLEANUP-01.sh /private/tmp/t108-cleanup-01.json
zsh evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-NO-MODEL.sh /private/tmp/t108-native-e2e-02.json
```

## 已有局部证据

- Claude 2.1.304 实际 CLI hook：单选 `/private/tmp/t108-claude-probe-05.json`、自由答复 `/private/tmp/t108-claude-free-01.json`、两题 `/private/tmp/t108-claude-batch-01.json` 为 PASS；多选探针失败，未开放多选写回。
- Codex 0.163.0 实际 CLI hook：同步单选 `/private/tmp/t108-codex-probe-03.json`、自由答复 `/private/tmp/t108-codex-free-03.json` 为 PASS；异步 `/private/tmp/t108-codex-probe-02.json` 只返回 accepted，不证明阻塞，保持未知。
- 新功能的旧实现红态 `/private/tmp/t108-red-02.json`：真实 signal 入口拒绝 PreToolUse，属于未实现新合同的预期红态。早一场 red-01 是夹具未建立 turn_submitted，不作为红态。
- 当前 hook／PTY 局部合同 `/private/tmp/t108-green-02.json`，12 项 PASS；IPC `/private/tmp/t108-ipc-01.json` PASS，保留原拒绝检查。
- T-107 只读回归 `/private/tmp/t108-sidebar-01.json`、`/private/tmp/t108-readonly-01.json`、`/private/tmp/t108-review-regressions-01.json` 为 PASS；后者包含旧实现与写入变异对照。

这些是局部或无模型证据，不证明正常登录、实际模型提问或系统通知。真实模型计划须先通过无模型完整入口，再交主控批准。T-093 正常登录入口固定 Claude 2.1.302，当前只安装 2.1.304，版本缺口未绕过。

`project_map.py status` 存在起点已有的 8 项稀疏 checkout 缺失链接，尚未满足票中 0 问题；不修改地图或其他 ticket 消除该报告。

## 主控 #8／#9：第二次入口超时

清理脚本 `/private/tmp/t108-cleanup-01.json` 为 PASS。第二次入口 `/private/tmp/t108-native-e2e-02.json` 仍为 INCOMPLETE，model_calls=0、vendor_calls=0，CLI 与 daemon 均已确认退出，没有残留。

`Matched Stop after answer` 是 until 超时的说明：要求问题回答后原生回合结束，匹配 Stop 推回 idle；不是禁止 Stop。保持该验收期望。故障属于测试夹具，未修改产品状态逻辑。

现场独立证据：

- 假 API 根请求数和总请求数均为 8。原生 hook 只有 UserPromptSubmit、PreToolUse、PermissionRequest、PostToolUse，没有 Stop；PostToolUse 确认回答为“西区”，native_question_resolved 已为 answered。
- 原生 session 文件中 msg_t108_2 的 content 为 text=""、stop_reason=end_turn；后紧跟 CLI 自身追加的 `[Your previous response had no visible output. Please continue and produce a user-visible response.]`。
- claude-debug.log 在 05:56:23.732 读到第二个流，05:56:23.797 再发请求；之后 409 重试直到清理。夹具把最终正文写进 content_block_start，却没有 content_block_delta/text_delta，CLI 因而组装出空回复，并撞上夹具原有的两次请求上限。

修复：按 [官方 SSE 文档](https://platform.claude.com/docs/en/build-with-claude/streaming) 发送空 text block start、text_delta 正文、block stop、end_turn 和 message_stop。同一错误也在 Claude 独立探针夹具中修正。两次根请求上限与 idle 断言均保留；额外要求原生最终文本为“已收到答复。”，唯一 Stop 与唯一 UserPromptSubmit 的 prompt_id 相同，pane_idle 事件在 answered 之后且携带该 Stop。摘要无论成功失败都保留已收到的 hooks、回合事件和每次假请求的 tool_result ID。

局部反事实（同一个实际 HTTP handler，无模型）：

```sh
python3 -B workbench/tests/test_t108_fake_stream.py --source /private/tmp/t108-e2e-before-sse-fix.py --summary /private/tmp/t108-sse-red-01.json
python3 -B workbench/tests/test_t108_fake_stream.py --source workbench/tests/run_t108_native_e2e.py --summary /private/tmp/t108-sse-green-01.json
```

第一条 rc=1，准确拒绝未传 text_delta 的最终回复；第二条 rc=0，PASS。Python 3.9 语法与 git diff --check 通过。这不替代实际 CLI／Electron 完整入口。

新的完整入口交主控执行，摘要尚未生成：

```sh
zsh evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-NO-MODEL.sh /private/tmp/t108-native-e2e-03.json
```


## 主控 #11：候选与真实回合计划

主控回传 `/private/tmp/t108-native-e2e-03.json` rc=0，PASS。六项均通过：实际 controller_start／已安装 CLI、Electron 问题与选项及等待状态、DOM 作答写回原 PTY、PostToolUse 确认后匹配 Stop／idle、answer 用户输入引用该问题、重复作答拒绝。model_calls=0、vendor_calls=0；假 API 根请求与总请求均为 2，两个测试进程确认退出。仓库保留 `no-model-03.summary.json` 与小型 `native-hook-samples.json`，不保存截图、SQLite 或运行日志。

Codex 当前 CLI hook 原件回放 `/private/tmp/t108-codex-hook-replay-green-01.json` PASS，已知坏对照 red-02 因 running != waiting_controller_answer 准确失败；red-01 是夹具缺字段，未计作红态。原件来自实际 0.163.0 CLI＋本地假 API，不是供应商真实模型证据。

交主控提交当前候选：`zsh evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-COMMIT-01.sh`。脚本固定本 worker 的公开身份环境，原钩子核对启动记录并自动加尾注；git add 带 --sparse，只加本票文件。不运行 submit、不 push、不写 git config。提交尚未执行，SHA 待主控回传；候选未经过本次独立 reviewer 审查，不宣称可集成。

真实模型计划见 [REAL-TURN-PLAN.md](REAL-TURN-PLAN.md)：仅申请 Claude 1 根，预计 2 条生成请求，T-093 正常登录，600 秒 F/D 生命周期。当前缺该入口固定的 Claude 2.1.302 二进制，不用已装 2.1.304 绕过。准备工具和真实命令均未运行，未读取正常登录凭据。Codex 选择已保存原生 CLI hook 原件回放，新增真实预算 0；来源与同步真实模型证据的缺口明确保留，不能靠改口径标全票 PASS。

合并冲突位置见 [CONFLICT-LINES.md](CONFLICT-LINES.md)：sidebar.ts 5、22–24、46–48、101–102；renderer.tsx 12–13、16、56、300。未改侧栏树结构或树渲染。

另有起点已有的 Codex xhigh 强制规则与当前 high 规定冲突，已报 triage 20261020T061048Z-worker:s18-t108-issue-001。本票不修该规则、不绕过门禁开真实 worker。

## 主控 #13：记录当前版本，真实运行待外部执行

首个候选已由主控提交为 **16b412964**。用户逐字：“跑真实回合,版本不重要,以后肯定要经常更新 cli 版本的”。主控据此批准 Claude haiku 5.5 low 的 1 个根回合，T-093 正常登录；失败不补发、不自动重跑；Codex 原件回放新增 0 根。effort 冲突由主控另票处理，本修订未改 panes.ts。

三处发行号锁已去除：claudeLaunch.ts 与 claudeLoginSession.py 校验本次版本记录的结构，claudeLogin.ts 在受保护环境读取 --version 并与本次 manifest 观测值核对，拒绝运行期间版本变化；不再要求等于 2.1.302。准备工具自动读实际安装版本；启动记录的 cli_version、role_card_revision 与最终 facts 的 cli_version／internal_state_version 跟随该次版本。保留私有 session/manifest 等值、auth_original_reads=1、版本失败、当前身份、隔离 HOME、网络与凭据清理检查。

没有静默认定 2.1.304 的内部状态仍可用。现有 T-093 onboarding/auth 探针改为读取并核对当前版本，其余安全检查、未知屏幕停止、禁止业务按键及清单差异判定均保留；外部探针尚未运行。真实脚本要求探针 PASS、清理成功、无凭据泄漏且版本仍一致，再走原保护入口；只发送一次根输入并沿用已通过的 Electron 问题/作答路径。实际登录与模型执行尚未发生。

本地验证（全部无真实凭据读取、无供应商模型调用）：

| 信号 | 结果 |
| --- | --- |
| test_t093_launch_profile.ts，修前 16b412964 产品源码 | /private/tmp/t108-version-profile-red-01.json：因 normal_login_version_requires_probe 精确失败；不是其他入口故障 |
| 同一版本构造合同，修后 | /private/tmp/t108-version-profile-green-01.json：PASS，4 项；动态 2.1.304、非法版本拒绝与原 hook 合同 |
| test_t093_session_once.ts | /private/tmp/t108-version-once-green-01.json：PASS，4 项；实际构造使用 2.1.304 替身，严格一次消费未变 |
| test_t096_restore.mjs | /private/tmp/t108-version-restore-green-01.json：PASS；样本改为记录 2.1.304，保存版本不一致仍拒绝，正常登录恢复仍拒绝，原变异继续拒绝 |
| test_t091_claude_version.mjs | /private/tmp/t108-version-refusals-01.json：PASS；缺 CLI、探针失败、版本不一致、并发身份拒绝及原变异保留 |
| test_t093_probe_safety.py | 22 项 PASS；仅合成探针辅助检查，不是实际 CLI／OS 探针 |
| test_t093_prepare_failure.py | /private/tmp/t108-version-prepare-failure-01.json：PASS，3 项 |
| test_t093_forwarder_port_policy.py | /private/tmp/t108-version-port-policy-01.json：PASS，10 项 |
| test_t093_session_cleanup.py | /private/tmp/t108-version-session-cleanup-01.json：PASS，5 项 |
| Codex 原件回放 | /private/tmp/t108-version-codex-replay-01.json：PASS，新增真实根回合 0 |

相关命令均为 `LC_ALL=C node [--experimental-vm-modules] workbench/tests/<上表脚本> <摘要路径>` 或 `LC_ALL=C python3 -B workbench/tests/<上表脚本> [摘要路径]`。Python 3.9 AST、zsh 语法与 git diff --check 通过。

按顺序交主控执行（尚未执行修订提交，不能冒报 SHA）：

```sh
zsh evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-COMMIT-02.sh
zsh evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-VERSION-PROBE-01.sh /private/tmp/t108-version-probe-01.json
# 仅上一步 PASS 后：
zsh evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-REAL-01.sh /private/tmp/t108-version-probe-01.json /private/tmp/t108-real-01.summary.json
```

外部版本探针与真实回合均待运行，整体仍 **INCOMPLETE**。新真实脚本仅做语法和调用合同核对，未取得 OS／CLI／供应商边界的新绿态；不复用旧 T-093 或无模型 PASS 代替。
