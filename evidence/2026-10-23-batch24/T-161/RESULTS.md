# T-161-1 / a1：只读查看与窗格角色

**PASS（T-161 行为验收）**。执行主控 #76 确认本票行为验收满足：06 的 green 17 项通过，四个变异均仅在预期业务断言被拒，无运行错误；T-157 recover/expired、T-159 split 通过。全套汇总仍为 **INCOMPLETE**，唯一失败是已知 T-165 的 Stop 输入回归，不把它改写为通过。后续门禁审查、集成与原始夹具归档由执行主控安排。

本次验证候选为 `18ba7ced315d334511084c4e4804d6752c27e1df`；产品实现提交为 `57b5c0b42a49dde905350d40e490f2dd50238700`。05→06 仅修测试观察与报告，产品代码未变。此后按主控 #76 只整理证据，不改产品或测试。

## 授权与实现

- worker `b24-t161`，task `T-161-1`，attempt `a1`，分支 `exec/t161`。修改范围见任务卡；未改地图、术语表、AGENTS 或他人票测试。
- 主控 #73 已确认 T-157 合并，并在沙箱外变基本分支；接手 HEAD `374cbb384`。重新阅读 T-157 的焦点、输出、交付拒绝与恢复入口后实施。未修改 main/preload 或后台权限。
- renderer 的自动焦点仅在 snapshot.input_enabled 为 true 时执行，保留本次可见状态回放完成、每次显式请求只服务一次的条件。
- 焦点模式序列仍由原 xterm 解析器消费；只有可写窗格发送 observeFocus。真实输入失败仍走原 failInput，停止发送并显示提示。
- 窗格按 launch 复用 sidebar 已确认的 role_label，头部显示“普通终端 · 执行主控”（或构思主控）；重命名后完整标签仍在，交回角色后恢复普通终端。没有改变原 shell 身份、权限或侧栏分类，保留 T-159 的“普通终端”标签。
- README 仅同步焦点与标签。Ubiquitous language 继续区分普通终端这一载体和确认角色；没有新增存储、API 或包装模块。

## 01～06 运行记录

| 运行 | 结果与定位 | 当次结论 |
| --- | --- | --- |
| 01：red-20261024T032952Z | setup 超时，checks 为空，未启动 Electron。UPS 缺 transcript_path，被拒 question_origin_unverified，三个受控 CLI 均退出；原 idle 等待还误认 SessionStart 后的瞬时空闲。诊断见 FIXTURE-01.md。 | INCOMPLETE，不是产品红态。 |
| 02：red02-20261024T033623Z | envelope 与 Stop 已走通，但交付因 model/effort 均 unknown 被门禁拒为 delivery_facts_unknown；checks 为空，未启动 Electron。见 FIXTURE-02.md。 | INCOMPLETE，夹具协议缺输入。 |
| 03：red03-20261024T034323Z | 补明确标识的模拟回复和 Stop effort 后，真实门禁启动 reviewer，Electron 已复现六条缺陷；随后等待输入错误时返回 DOM 节点，CDP 无法序列化。见 FIXTURE-03.md。 | RED / INCOMPLETE，缺陷失败保留，但运行未完整结束。 |
| 04：red04-20261024T034907Z | 修前 `3c56f743fa605ce0b3c7b99e4278b933202cf627` 上，恰好六条缺陷失败，九条对照通过，error/cleanup_errors 均无值。见 RED.md。 | RED / PASS，完整修前红态。 |
| 05：/private/tmp/t161-outside-05.KIeFyq | 候选 fdcf721f3，green 17 项通过，观察/焦点/角色三变异业务反证成立，recover/expired/split 通过。输入错误变异因 until 等不到提示而报超时；另有 T-165 回归失败。摘要与 green 截图见 OUTSIDE-05/。 | INCOMPLETE，原件保留。 |
| 06：/private/tmp/t161-outside-06.NITT3y | 候选 18ba7ced3，green 17 项通过，四变异准确失败且无 error，recover 12 项、expired 9 项、split 46 项均通过。只剩已知 T-165。见 OUTSIDE-06/。 | T-161 PASS；全套 INCOMPLETE。 |

重放入口均为本目录的 `RUN-OUTSIDE-01.sh`～`RUN-OUTSIDE-06.sh`，每次生成新路径，原始结果不覆盖。01～04 的小摘要、日志与截图直接保留；05/06 保存原始汇总、退出码、候选号与 case 摘要。06 另保留五场 T-161 原始 summary 和全部 34 张截图，其他原始模型消息与夹具保留在 /private/tmp，交主控按 T-088 归档。没有删除失败现场或改写原始状态。

## 验收与反证

| 条件 | 06 证据 |
| --- | --- |
| reviewer、历史 worker 只读查看无输入横幅，不请求输入焦点 | 两类 focus-mode/readonly/no-input-credential 对照均通过，view_has_no_input_error 与 no_requested_input_focus 均通过；green-reviewer.png、green-history.png。 |
| 可写主控与 worker 仍获得输入焦点，真正输入拒绝仍提示 | 两个 writable_*_receives_input_focus 与 real_input_failure_still_visible 均通过；green-real-input-rejected.png。输入通过真实 xterm onData→preload→IPC，超限内容由原 main 校验拒绝。 |
| 隐藏侧栏、重命名后仍可辨认主控，保留普通终端 | confirmed_executor_header_with_sidebar_hidden、renamed_controller_keeps_carrier_and_role 通过；green-controller-sidebar-hidden.png。释放角色后不再显示主控的对照也通过。 |
| 已知坏实现能被业务断言拒绝 | observation：两类 view_has_no_input_error；focus：两类 no_requested_input_focus；role：隐藏侧栏与重命名的角色断言；input-error：real_input_failure_still_visible。四场均 exit=1、17 项检查完整、无 error/cleanup_errors。 |
| T-157/T-159 相邻行为 | recover/expired 与 split 均通过，详见 CASES.json 与相应截图；没有更改这些测试或使用旧候选的通过结论。Stop 输入项另列 T-165。 |

05→06 的测试修正没有改变判据：等待最多 4 秒内出现可见的“输入尚未确认”提示；缺失时该检查为 False，后续截图与零模型请求检查仍执行。CDP/运行异常仍作为 error 抛出，没有 catch 吞错。输入错误变异在 06 精确失败于该断言，证明观察器已能区分隐藏提示。

## 已知 T-165 与证据边界

05、06 的 t157-stop-input 均在“worker 及门禁反馈回到空闲”超时；原 Stop submit 已接受。执行主控 #75 提供独立基线：不含 T-161 的 main 上也 2/2 失败，另开 T-165 交 b24-t165 修；本 worker 未自行复跑该对照，也未改相关产品代码。主控 #76 明确本票行为验收满足。

06 汇总只在原 submit 已接受、无业务断言失败、且唯一错误完全匹配该基线超时时标 known_baseline_failure=T-165；该项 passed 仍为 false，全套 status 仍为 INCOMPLETE。不同错误不按已知问题排除。T-161 范围结果另列 t161_status=PASS，不表示全产品可发布。

全部运行供应商模型回合为 0。T-161 用真实 Electron、后台、SQLite、门禁与受控原生 PTY；模拟 model=t161-controlled-pty-no-model / effort=low 只表示测试替身协议数据，不是供应商模型、推理或服务档位证明。T-157 用真实 Claude CLI 和本地脚本化 Messages。未写用户全局配置，测试后台按既有夹具脱离调用者进程组，原始副本不入仓库。

## 本地检查与交接

- `BUILD-01.json`：实现候选通过标准 `node app/build.mjs --slot t161-candidate`，独立 /private/tmp 构建槽完成后已清理，只代表构建通过。
- `T157-IDENTITY-01.json`：四项隔离身份状态通过，不代替真实 CLI/PTY/GUI 证据。
- 本票 Python、嵌入 peer、05/06 oracle、zsh 语法、UTF-8 回读和差异空白检查通过。主控运行真实检查；worker 核对 06 的全部摘要与反证，并目视核对 reviewer 无横幅、侧栏隐藏后头部显示普通终端及执行主控。
- 新开只读上下文按 behavioral-acceptance-review 对冻结候选 `9f7deae97425c1602af10f434ea41c690c637010` 审计，结论 PASS，无发现，保留 T-165 和受控 PTY 的局限；见 `ACCEPTANCE-AUDIT.md`。这是交付证据审计，不代替主控的门禁审查和集成。
- 此交付不 push、不合并 main，不回收其他会话；由执行主控继续门禁、独立审查与集成。T-165 保持独立处理。
