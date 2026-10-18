# T-095-1 候选交付（2026-10-18，原生事实源补充）

**INCOMPLETE。** 已实现绑定原生会话的提问事实读取；真实红态原件回放中，折叠与展开均输出 `waiting_controller_answer` / “等待主控回答”，附 worker 与 launch 身份。真实绿态、关闭后的真实状态回落、离线原件外置盘归档和独立审查仍未完成；未 submit、验收或集成。本报告与源码绑定所在候选提交，task T-095 / attempt a1 / session `983db526-dfe8-473a-857b-b3f2af0af582` / launch `launch-4b1abba18e87460da9cbacec04905c78` / ready_rev 1；基线 `3c9016d0230223945f0e16543b230a047c2ad032`。

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

**红态关闭阶段的限制：** 归档的完整原生日志共有 40 条记录，仍保留待答请求，没有可关联的应答或跳过事件。因此该阶段回放为 unknown，并记录 `native=pending / screen=activity / herdr=working` 冲突。本候选不把它报告成状态已成功回落。真实绿态需要核对异步 skip 的落盘情况；若仍无机械解决信号，继续 unknown，不能上调。

## 检查与反事实

下列 PASS 仅适用于各行范围，不等于真实绿态或整票 PASS。报告文件均在本目录；重新运行使用新报告路径，避免覆盖旧证据。

按 T-088，本次详细检查输出收为 JSON 摘要，各文件的 `full_archive` 指向完整原件。20 份详细输出和 17 个失败夹具已复制到 `/tmp/t095-offline-native-evidence-p72mvbxh`，核对后共有 1,764 个文件、5,498,933 字节；原夹具也保留。`native-offline-evidence.archive.json` 保存逐文件字节数、目标与回放入口。外置盘写入须由主控运行下方脚本；当前清单明确为 INCOMPLETE，不能称已归档。

| 范围 | 证据与结果 |
| --- | --- |
| 真实入口合同、合成反例与小输入回放 | **PASS，66 项**；`native-contract-release-candidate.json`。覆盖普通思考 / 命令活动、无专属标记、身份替换、未绑定、半条日志、来源冲突、读取中变化、答案与空映射。 |
| 未裁剪的真实红态原生日志 + 真实读屏 | **PASS，3 项回放合同**；`native-full-raw-release-candidate.json`：折叠、展开为等待；关闭为 unknown 且有冲突。索引直接绑定外置盘原件，未把合成解决事件混入原件。 |
| 严格两种面板正判合同 | **PASS，2 项回放**；`native-panel-contract-01.json`，不允许用安全 unknown 通过。 |
| 已知坏实现 | `native-contract-before-01.json` 拒绝前一 UI 候选；`native-receipt-mutant.json` 拒绝“accepted 回执就是解决”的坏副本；`native-change-before.json` 保留未记录来源变化冲突时的失败。后两者的 FAIL 是反事实检出，不是当前候选通过结果。 |
| 当前 worker 的普通 working，真实只读入口 | **PASS，仅普通活动**；`native-live-ordinary-release-candidate.json`，核对真实原生 UUID，不增加模型回合。 |
| 绿态采集脚本离线接线 | **PASS，0 个真实模型回合**；`native-green-wire-release-candidate.json`。明确假 Herdr / Codex，采集等待 / 等待 / unknown，核对身份、1 次提示意图、无代按键、只关闭自建 pane、清理隔离 HOME 与空目录。 |
| 错误原生路径指向凭据 | **PASS，0 个真实模型回合**；`native-green-wire-reject-auth.json`。用假凭据 canary 验证拒绝日志头不符的源，不发布原生绑定，不归档该文件；检查所有归档文件没有 canary。正常归档也只复制重新核对后的绑定文件描述符。 |
| 清理 | `red-temp-cleanup.json`：`/tmp/t095-panel-pg9mo4yh` 只剩空 fixture，已用 rmdir 清掉，凭据与隔离 HOME 均不存在。失败夹具与坏副本保留，副本已纳入上述归档计划，尚未完成外置盘复制。 |
| 项目地图 | `native-map-status.txt`：0 problems / 0 stale living docs。 |

复现命令：

```sh
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_agent_status.py --report <新报告路径>
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_agent_status.py --full-native-red --report <新报告路径>
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_agent_status.py --panel-contract --report <新报告路径>
PYTHONDONTWRITEBYTECODE=1 python3 evidence/2026-10-16-batch16/T-095/check-green-probe-wiring.py <新报告路径>
PYTHONDONTWRITEBYTECODE=1 python3 evidence/2026-10-16-batch16/T-095/check-green-probe-wiring.py <新报告路径> --bad-source
```

中间失败未覆盖：`native-contract-after-01.json` 发现原生身份消失的漏拒绝，已修正；`native-contract-after-02.json` 记录一次显式假 Herdr 的启动超时，后续 66 项检查通过，不把这次失败改成 PASS。其余旧报告仍保留。尚未执行独立 behavioral-acceptance-review 或设计审查；由主控在真实绿态后针对冻结候选另开只读审查，不能由实现者自签通过。

## 交给主控的绿态脚本

红态已用 1 个根回合，**绿态最多再用 1 个**；不重试、不 resume、不自动回答。用户已确认 T-095 不用等名额。由执行主控在沙箱外的 Herdr 终端运行：

```sh
python3 evidence/2026-10-16-batch16/T-095/archive-offline-evidence.py --apply
python3 evidence/2026-10-16-batch16/T-095/controlled-panel-probe.py --approve-one-root-turn --phase green
```

第一条只复制离线原件，核对逐文件字节数、总文件数与总字节数，写外置盘 receipt；不删除源、不调用模型。第一条 PASS 后再运行第二条；已有目标、源变化或外置盘未挂载均停止，不覆盖异常现场。

不带 `--approve-one-root-turn` 只打印计划，见 `native-green-plan-release-candidate.json`。脚本开头和每个确认点都说明操作：先核对 SHELL_READY 与 CODEX_IDLE；COLLAPSED 前在自建 pane 按需 Shift+→ 折叠；收到 CAPTURED collapsed 后 Shift+← 展开；收到 CAPTURED expanded 后仅按界面明确提供的 Ctrl+] skip；返回脚本终端输入对应确认词。没有相应 UI 时终止，不猜键、不提交答案。

脚本固定 Codex 0.163.0、gpt-6.1-sol / xhigh / 请求 fast，保存完整 argv；HOME 只复制 auth.json，无全局配置写入。原始 get/read、逐次状态 JSON 与退出码、原生 UUID 绑定、读取字节截止点、手动操作和清理记录都写入同一个外置盘 run；结束关闭自建 pane、删除隔离 HOME，仅删除空 fixture。真实绿态采集完成仍显示 INCOMPLETE，须读回原件再作验收判断。`T-095 READY <sha>` 表示候选与脚本已交付，不表示整票 PASS。
