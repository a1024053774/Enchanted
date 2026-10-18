# T-095-1 冻结读回（2026-10-18）

**INCOMPLETE；当前候选不具备验收通过条件。** 真实绿态的折叠、展开、手动 skip 后三个现场投影均为 unknown；经 `scripts/agent-status` 离线回放原件，也得到相同状态和原因。两种形态没有读出“等待主控回答”，关闭后的正常状态回落也未证明成功。本次按执行主控 #106 要求冻结、提交证据并写审查请求，不修改产品解析器，不将旧红态回放的 PASS 上调为真实绿态 PASS，未 submit、验收或集成。

产品代码仍为真实绿态所运行的 `504abc34ad2df27fa60b7cc998c499c122143d98`；本次新增证据、零模型回放工具与审查请求。冻结候选是承载本报告的提交，完整 SHA 见交付末行。task T-095 / attempt a1 / session `983db526-dfe8-473a-857b-b3f2af0af582` / launch `launch-4b1abba18e87460da9cbacec04905c78` / ready_rev 1；基线 `3c9016d0230223945f0e16543b230a047c2ad032`。

## 本次真实绿态：两种形态均未通过

原件位于 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-095/green-20261018T125458Z-76e72ee1`，清单见 `real-green.archive.json`：169 个文件、163,147 字节，直接采集到外置盘。探针身份为 worker `t095-probe-5c6f76bc7f`、launch `launch-t095-probe-79a62b96962f4f49908477009c041f71`、pane `wF:p6D`、原生 UUID `01a14f14-e6ef-7470-bf2e-f3b515e94ff2`。三次投影均已核对绑定身份；失败来自状态识别，并非缺少 launch 或日志身份。

| 阶段 | 原始 Herdr | 现场投影 / 原件回放 | 判断 |
| --- | --- | --- | --- |
| collapsed | blocked → blocked | unknown，`unverified_screen_tail`，退出码 2 | **NO_GO**。屏幕有 `• Queued follow-up inputs / ? 1 question / ⇧← to answer`；解析器未覆盖该折叠尾部结构。 |
| expanded | blocked → blocked | unknown，`composer_missing`，退出码 2 | **NO_GO**。控制条为 `enter submit / ⌃] skip / ⇧→ main prompt`，没有旧样本的 `option N/M`，且前方有 Working 与 Queued follow-up 行；当前面板匹配失败后落入普通输入框解析。 |
| cancelled | working → working | unknown，`screen_native_conflict`，退出码 2 | **INCOMPLETE，回落未通过**。原生仍为 pending，当前 UI 是普通活动，`conflicts` 如实保存；符合冲突时保守 unknown 的约束，但不是正常回落成功。 |

**人工操作（来源：执行主控 #106 / 主控 #5 的操作者记录）：** SHELL_READY 前台为 -zsh，CODEX_IDLE 为空闲输入框。提交约 7 秒后看到 blocked 与 Working、没有面板文字。**在输入 COLLAPSED 之前，操作者先 Shift+← 展开，核对固定问题，再 Shift+→ 折叠；随后脚本才采集折叠态。** 收到 CAPTURED collapsed 后再次 Shift+← 展开并输入 EXPANDED；最后按界面提供的 Ctrl+] skip，Herdr 变成 working，输入 CANCELLED。首次展开再折叠是人工介入，不能把这个样本称作“从未展开的默认折叠态”。它对布局变化是否有因果影响尚未证明。

原生日志共 20 条、94,654 字节，三次现场投影的字节截止点均等于整个归档长度。第 12 条是提问调用，第 13 条是同 thread / turn / call 的发布，第 15 条是 `accepted:true` 回执；没有关联的应答或 skip 解决事件。日志最后一条时间为 12:56:04.930 UTC，关闭阶段采集结束于 12:56:53.457948 UTC；这段时间没有落盘解决信号。不能把缺失补成答案，也不能把 accepted 当作已经解决。

脚本记录 pane close 返回成功，隔离 HOME 已删除、fixture 与 scratch 均已清理；本 worker 只读核对这些路径确已不存在。单次 1 个根回合、0 个自动答案；红绿合计 **2 / 2 个根回合，剩余 0**。不再次运行真实探针，不 resume，不向已关闭 pane 发命令。

## 原件回放与归档读回

```sh
PYTHONDONTWRITEBYTECODE=1 python3 evidence/2026-10-16-batch16/T-095/replay-green.py --report <新报告路径>
```

本次输出见 `green-readback-01.json`：`replay_status=PASS` 只表示三个状态、原因、冲突与现场投影一致、身份核对正确、只执行 get/read；`acceptance_status=NO_GO`，总状态 INCOMPLETE，命令退出 1。期望值来自 ticket：两种面板必须等待，当前关闭后的普通活动应回 working；没有把 actual unknown 抄成通过预期。

回放用测试输入 `real-green-inputs.json` 中的原始 get/read 与启动记录，在临时目录重建只读查询用索引，把 `native_store` 改为该临时索引；worker、launch、pane、原生 UUID、cwd 和原生前缀字节不变。明确假 Herdr 可执行文件只返回归档读数，调用实际 `scripts/agent-status`，不接触服务器和已关闭 pane，不调用模型。边界限制：外层采集早于现场投影内部读取，不能还原未保存的内部每次屏幕；现场投影的原始 stdout 本身另存于原件 command 026 / 033 / 040，不能用回放代替现场结论。

离线原件归档现已 **PASS**：主控执行后保存的 receipt 与本 worker 逐文件名称、字节数读回相符，共 1,764 文件、5,498,933 字节，原件未删除。见 `native-offline-confirmed.archive.json`；先前 `native-offline-evidence.archive.json` 的 INCOMPLETE 是执行前的历史清单，不改写该事实。

本次新增回放夹具与完整读回报告共 34 文件、367,016 字节，源保留在 `green-replay.archive.json` 指向的 `/tmp` staging。其外置盘复制仍待主控在沙箱外执行；仓库只保存摘要、小输入与清单，不纳入 sqlite 或完整 fixture。此命令不消耗模型回合：

```sh
python3 evidence/2026-10-16-batch16/T-095/archive-offline-evidence.py --manifest green-replay.archive.json --apply
```

审查请求见 [REVIEW-REQUEST.md](REVIEW-REQUEST.md)。目前没有独立审查结论；实现者的回放不是独立验收。

## 红态原件与前一候选

原始目录为 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-095/red-20261018T110936Z-f4d263d1`，文件数、字节数和回放入口见 `real-red.archive.json`。原件未修改；仓库只留文本记录和测试读取的小输入。

- **2026-10-17 T-094：** ticket 与执行主控报告，当时 worker 在提问面板待答，Herdr 显示 working，用户先发现。本 worker 没有取得当时的读屏原件，不能补称已独立复验。
- **2026-10-18 受控红态：** 折叠、展开时各两次 Herdr 原值均为 **blocked**；手动 Ctrl+] skip 后为 working。折叠屏幕只有 Working 活动行、普通输入框和底栏；展开才有选择行及 `enter submit / ⌃] skip / option N/M / ⇧→ main prompt` 控制条。两次观察不一致，原因未知；屏幕的 Working 字样不能替换 Herdr 原值。
- **原 ticket 的“两种形态当前读成 working”未复现，仍不能勾选。** 本次原件能证明缺少独立提问状态，不能补成 ticket 要求的 working 红态。
- 原件只有 1 个根回合，1 次 `request_user_input_async`、3 次 `clock.sleep`，0 个自动答案，没有命令或文件工具调用。主控手动按 Ctrl+] skip；这不是自动应答，也不是 Esc。

前一候选 `7c0dbddcce9bfc5842ec75988c2cc3495de7f0d7` 仅用 UI，折叠保持 unknown；其检查与失败报告全部保留。执行主控 #102 随后确认增加“结构化提问 / 解决信号”，要求按启动记录绑定原生会话，来源不可读、身份不符、事件不完整或来源冲突时输出 unknown。以下是按该确认补充的候选。

## 唯一读取入口与机械依据

唯一产品入口仍是 `scripts/agent-status`；不改 dispatch、工作台或门禁，不另存一套产品状态。Ubiquitous language 统一为内部值 `waiting_controller_answer`、显示名“等待主控回答”。`native_questions.py` 隐藏索引查询、身份核对和事件关联；这是入口到真实只读边界的 Tracer bullet，没有新增后台服务。

已有启动记录可显式指定已核对的索引，例如读取本 worker：

```sh
scripts/agent-status --root /Users/luckye/Documents/Code/a2a --launch launch-4b1abba18e87460da9cbacec04905c78 --native-store /Users/luckye/.codex/state_5.sqlite
```

也可用该 launch 记录中的 `native_store`；参数与记录冲突时 unknown。**必须已有 `native_session` 绑定**，读取器不猜测、不补写绑定。探针只在自己新建且仅有一个 worker 的隔离 HOME 内建立首次绑定，随后也走相同读取入口。

按启动记录的原生 UUID，只读 SQLite `threads WHERE id=?` 得到 `rollout_path`，再核对日志头里的 UUID、cwd、CLI 来源和版本。路径名称不参与身份判断；不扫描其他 worker 的记录，不改 Herdr、Codex 或全局配置。启动记录、live pane / worker / terminal / cwd、可观测原生身份和读取前后稳定性均须核对。`revision` 只作观察字段，不当作进程身份。没有绑定、缺索引、错日志头或半条事件均为 unknown。

| 原生事实与当前 UI / Herdr 的组合 | 投影 |
| --- | --- |
| 本会话本回合的提问调用、对应异步发布与 accepted 回执齐全；两份普通活动结构；Herdr blocked | 等待主控回答，collapsed |
| 同上；两份完整面板控制条与一致的选择位置 | 等待主控回答，expanded |
| 没有待答问题；两份普通活动结构；Herdr working | working |
| 没有待答问题；两份结束结构；Herdr idle / done | idle |
| 原生问题仍待答，屏幕与 Herdr 已恢复普通 working；或原生已清除但屏幕仍是面板 | unknown，保存 `conflicts` |
| 读取 UI 期间原生问题状态改变 | unknown，保存前后来源冲突 |

不匹配问题正文，不解释自然语言答复。`accepted:true` 仅证明已接收，**不是解决信号**。同 call_id 的正式 `answers` 映射或空映射可关闭请求；格式依据本地 CLI 0.163.0 生成的 schema，出处见 `native-schema-source.json`。这些解决分支目前只用合成事件验证，尚未取得本次异步 skip 的实际对应事件。

**红态关闭阶段的限制：** 归档的完整原生日志共有 40 条记录，仍保留待答请求，没有可关联的应答或跳过事件。因此该阶段回放为 unknown，并记录 `native=pending / screen=activity / herdr=working` 冲突。本次真实绿态也未取得该解决信号；两次都不能报告为状态已成功回落。

## 检查与反事实

下列 PASS 仅适用于各行范围，不等于真实绿态或整票 PASS。报告文件均在本目录；重新运行使用新报告路径，避免覆盖旧证据。

按 T-088，前次详细检查输出已收为 JSON 摘要，各文件的 `full_archive` 指向完整原件。20 份详细输出和 17 个失败夹具已经主控复制到外置盘，并完成本次读回核对；新确认清单为 `native-offline-confirmed.archive.json`。以下旧检查只证明各自列出的合同或回放，不覆盖本次真实绿态新布局。

| 范围 | 证据与结果 |
| --- | --- |
| 真实入口合同、合成反例与小输入回放 | **PASS，66 项**；`native-contract-release-candidate.json`。覆盖普通思考 / 命令活动、无专属标记、身份替换、未绑定、半条日志、来源冲突、读取中变化、答案与空映射。 |
| 未裁剪的真实红态原生日志 + 真实读屏 | **PASS，3 项回放合同**；`native-full-raw-release-candidate.json`：折叠、展开为等待；关闭为 unknown 且有冲突。索引直接绑定外置盘原件，未把合成解决事件混入原件。 |
| 严格两种面板正判合同 | **PASS，2 项回放**；`native-panel-contract-01.json`，不允许用安全 unknown 通过。 |
| 已知坏实现 | `native-contract-before-01.json` 拒绝前一 UI 候选；`native-receipt-mutant.json` 拒绝“accepted 回执就是解决”的坏副本；`native-change-before.json` 保留未记录来源变化冲突时的失败。后两者的 FAIL 是反事实检出，不是当前候选通过结果。 |
| 当前 worker 的普通 working，真实只读入口 | **PASS，仅普通活动**；`native-live-ordinary-release-candidate.json`，核对真实原生 UUID，不增加模型回合。 |
| 绿态采集脚本离线接线 | **PASS，0 个真实模型回合**；`native-green-wire-release-candidate.json`。明确假 Herdr / Codex，采集等待 / 等待 / unknown，核对身份、1 次提示意图、无代按键、只关闭自建 pane、清理隔离 HOME 与空目录。 |
| 错误原生路径指向凭据 | **PASS，0 个真实模型回合**；`native-green-wire-reject-auth.json`。用假凭据 canary 验证拒绝日志头不符的源，不发布原生绑定，不归档该文件；检查所有归档文件没有 canary。正常归档也只复制重新核对后的绑定文件描述符。 |
| 清理 | `red-temp-cleanup.json`：红态 scratch 只剩空 fixture，已用 rmdir 清掉，凭据与隔离 HOME 均不存在。旧失败夹具与坏副本的外置盘副本现已核对；本次绿态 scratch 也已不存在。 |
| 项目地图 | `native-map-status.txt` 与本次 `frozen-map-status.txt`：0 problems / 0 stale living docs。 |

复现命令：

```sh
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_agent_status.py --report <新报告路径>
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_agent_status.py --full-native-red --report <新报告路径>
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_agent_status.py --panel-contract --report <新报告路径>
PYTHONDONTWRITEBYTECODE=1 python3 evidence/2026-10-16-batch16/T-095/check-green-probe-wiring.py <新报告路径>
PYTHONDONTWRITEBYTECODE=1 python3 evidence/2026-10-16-batch16/T-095/check-green-probe-wiring.py <新报告路径> --bad-source
```

中间失败未覆盖：`native-contract-after-01.json` 发现原生身份消失的漏拒绝，已修正；`native-contract-after-02.json` 记录一次显式假 Herdr 的启动超时，后续 66 项检查通过，不把这次失败改成 PASS。其余旧报告仍保留。尚未执行独立 behavioral-acceptance-review 或设计审查；由主控在真实绿态后针对冻结候选另开只读审查，不能由实现者自签通过。

## 冻结边界

真实探针预算已用尽。`controlled-panel-probe.py` 保留为已运行程序的来源，不构成继续运行的授权。其配置为 Codex 0.163.0、gpt-6.1-sol / xhigh / 请求 fast；完整 argv、输入、人工操作和原始输出均在红绿两个外置盘 run，未改 Herdr 或全局配置。

当前未覆盖的两种绿态 UI 布局需要后续修复；真实 async skip 的可关联解决事实仍缺失。冻结本身不改变目标、验收条件、事件完整性要求或模型预算；后续处理由执行主控依据独立审查结果安排，本 worker 不自行扩大范围或追加真实回合。
