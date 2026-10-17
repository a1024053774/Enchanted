# 09A-2：Esc 后的输入草稿与放行方案

2026-10-14，按主控 #124，只读诊断与方案交接。**产品验收 INCOMPLETE，方案待决定；本轮没有实现任何放行、清空或 hook 行为。** 假服务实跑使用 Claude Code 2.1.296，真实模型 0；记录绑定产品 `7cd19b586fe757268384d99f243f5d0a583a5ad3`。以下事实不能外推至其他 CLI／版本／用户键位配置。

## 已确认的事实

原件在保留根 `/private/tmp/t078-2-p1-09a2-sm_du7jo`，launch `d2d9c666-5621-4467-bbe4-d99450bd5503`。本轮 [读回](draft-readback-09a2/result.json) 保存了库事件、动作、实际 hook 小份、17,573 字节 PTY 输出和 Esc 后重绘增量；PTY 与 [原外置归档](external-archive-93611737c0674a7aa55d1fcf3863a0b0.json) 对应成员逐字节相同。

1. 第一 dispatch 已独立 paste＋CR 提交，UserPromptSubmit exit 0，busy/active1 成立。Esc 的同窗口请求有准入 seq 86、意图 87、写入 88、退休 89；active=null、busy、interrupted=true，第二 dispatch 仍排队。API1 在 05:50:59.726455Z 观察到 peer 关闭，发生在放行及 cleanup 之前。
2. 发 Esc 前窗口已解析输出至 offset 11,917；放行前截图解析至 13,245。此增量含第一 nonce 的重新绘制，第二 nonce 尚未出现。[放行前实际截图](p1-materials-09a2/continue-esc/electron/before-user-release.png) 已目视核对：第一条的标记与 nonce 位于底部可编辑输入框，光标在其末尾；不是仅凭正文出现就推断草稿。窗口 header 的 active_dispatch 仍是较早快照，后台 active=null 以同请求退休事件及 pane_status 为准，不能用 header 覆盖后台事实。
3. `user_draft=true` **不是 CLI 输入框检测结果**。`panes.ts` 的 userInput 对每次非二进制输入先设置 userDraft=true，Esc 也如此。PTY 输出只用于终端协议应答及展示，没有回写“CLI 草稿内容”。此标记表示后台保留用户输入占用；不能证明文本非空，也不能证明清空。
4. 放行 action 被记一次；05:51:00.606Z 产生 user_queue_release，随后只有第二 dispatch 的 paste_intent/paste_written 各一次、独立 CR 提交一次。releaseByUser 仅把 active/prompt ID/userDraft/interrupted/state 的后台状态复位，再调用 drain；它没有向 PTY 发任何清空编辑框的控制键。第二次声明写入是 `ESC[200~`＋**第二条登记正文**＋`ESC[201~`，300ms 后单独 CR；没有再次注入第一条。
5. 第二次实际 UserPromptSubmit 原始 stdin 的 prompt **逐字等于第一条登记正文＋第二条登记正文**，两者连接处没有额外换行；该 hook exit 1。API 主请求记录共三条：第一条正文正确，后两条的最后一个 user text 都是同一拼接正文。fake API 按独立声明拒收请求 2，并保留首个 api-error，不改成“接受拼接”。后台只登记／提交第二 dispatch 一次；不能把第三条 HTTP 请求算成 a2a 再派发一次，CLI 内部为何重复请求未在本轮进一步确认。
6. 进程清理已执行，CLI 退出核对 PASS；cleanup 的整体状态仍 INCOMPLETE，因为保存了 API 失败并保留根。原 slot-cleanup BLOCKED 也保留，不能改写成 PASS。旧 09 的独立 slot 已由主控清理 PASS；本次 09A-2 slot 尚在。

**推断：** CLI 在中断响应后把被中断提示恢复进编辑框；第二 paste 插入其末尾，CR 把二者一起提交。中断后的输入框截图、无其他用户文本输入、仅第二条的新注入以及 hook/API 的精确拼接共同支持该机理。CLI 内部恢复代码没有检查，不能声称已定位其内部函数或恢复触发条件。

**未知：** 同版本在用户已输入新草稿、移动光标、中文组合输入、其他编辑模式／改键位时的恢复与清空行为；我们没有文档化的未提交草稿读取能力，也没有证明某个按键或一个后台布尔值能给出输入框为空的可靠确认。不把读屏／关键词规则加入忙闲或草稿业务判断。

## 最小方案与取舍

保持 spec 第 6 节：Esc 释放当前 active，队列仍 held/busy；只有用户放行才能继续，注入仍是 bracketed paste 后独立 CR。下列方案均不能把 Esc 后自动继续当作修复。

| 选项 | 最小可用流程 | 取舍与停止条件 | 用户输入记录语义 |
| --- | --- | --- | --- |
| **A：用户处理草稿，再确认输入框为空后放行（建议）** | 草稿占用／中断状态下，普通放行拒绝并提示用户先自行保留、修改或清空 CLI 草稿；用户实际看到编辑框为空，再提交一条明确的“输入框已空，放行”确认。确认只解除对应中断的占用，在现有写入串行通路中核对窗口／输入代次；确认后又有键入／组合输入就拒绝陈旧放行。 | 不增加后台自动删字，不需要把终端画面当状态机。**只加 `if user_draft: reject` 不够**，因为 Esc 自身就置 true，清空按键也不自动证明空：必须设计解除占用的明确用户确认入口，否则队列永久不能放行。代次核对只能挡新的用户输入，不能证明 CLI 在确认后不会自己恢复草稿；该未知需新 tracer bullet 验证。不能宣称人工确认等于机器读取输入框。 | 真正手动按键仍记用户输入／控制 action；放行 action 增加“用户确认编辑框为空”的明确声明和对应中断引用。它是用户声明，不是 observed CLI 状态。记录内容有扩充，交构思主控确认；不能把 CLI 自行恢复的文字新记成用户亲手输入。 |
| **B：用户明确批准丢弃当前草稿并放行，后台先清空再送** | 独立、明确的“丢弃当前输入草稿并放行”动作，核对目标与输入代次后，经同一后台写入通路清空、读回确认，再 paste＋CR；任何新用户输入、未知编辑上下文或无法确认清空都停，不能先送后补检查。候选键为 CLI 无运行操作时的一次 Ctrl+C，而非一次 Ctrl+U。 | 操作更少，但会删掉用户刚打的真草稿，不能把普通“放行”暗中升级成删字批准。a2a 的 busy/interrupted 不证明 CLI 当前无运行操作；必须先在新隔离实例证明上下文、一次清空、多行／粘贴、空输入时行为及竞态。若没有独立清空确认能力，这个方案不能直接上线；不能靠固定 sleep／重试获得“已空”。 | 新增丢弃草稿的用户批准 action；后台自动控制写入独立留系统事实并指向批准，不伪装为用户亲手 Ctrl+C，不把恢复旧提示记 message。批准含义及记录来源都扩大，须构思主控决定。 |

建议先决定 A：它保留 CLI 对编辑框的所有权，避免后台删掉未提交文本。不是批准，也不是完整可靠性结论；仍须明确用户确认入口、并发输入拒绝和提交错配的处理。实现只留在现有 Panes/window 输入边界（**Deep modules**），不加另一个绕过记录器的终端写入入口。用 **Ubiquitous language** 区分“后台草稿占用”与“CLI 编辑框草稿”，不能把两者当同一个事实。

## 清空按键的官方依据及限制

2026-10-14 核对 [官方交互模式：通用控制与文本编辑](https://code.claude.com/docs/en/interactive-mode#keyboard-shortcuts)：Ctrl+C 在无运行操作时先清空输入，再次按可退出；有操作时用于中断。Ctrl+U 删除光标至当前行起点，多行需多次；不能用一次 Ctrl+U 代表整框清空。双 Esc 在非空草稿时清空，空框时可能打开 rewind；Ctrl+S 在有草稿时暂存并清空，空框时会恢复暂存内容。因此它们都不能在未知上下文中盲发。文档是当前官方说明，不是 2.1.296 在本工作台中按键实测。

暂存 Ctrl+S 可作为用户在 A 中的手动保留方式；不另建自动暂存方案：需要确认非空、当前 Chat 上下文、既有 stash 及恢复时机，空框误触会把旧 stash 恢复进来。[官方 keybindings](https://code.claude.com/docs/en/keybindings#chat-actions) 也说明 Chat/Agents 上下文不同；真登录用户键位不能默认等同于隔离夹具，不改用户设置去迎合探针。

当前产品的控制键分类只列 CR/LF/Esc/Backspace；若 Ctrl+C/U/S 经 xterm 发出通常的单字节 0x03/0x15/0x13，userInput 会走 message 记录分支，而非 terminal-key action（本轮未实际发送这些键）。选用这些用户手动编辑键时，应明确机械控制字节的记录形态；该形态修正也属需交构思主控核对的用户输入语义。本轮没有顺手修正。

## 独立的提交前阻断选项

本轮实际第二 hook exit 1 后仍发请求，符合 [官方 hook 退出码](https://code.claude.com/docs/en/hooks#other-exit-codes) 的非阻断语义。已有“登记注入正文与实际 prompt 精确相等”的检查拒收了 a2a 回合信号，却没有拦住 CLI 调模型。[UserPromptSubmit 的阻断方式](https://code.claude.com/docs/en/hooks#userpromptsubmit-decision-control) 可在处理前拒绝 prompt（exit 2 或明确 JSON block）。

这可作为 A/B 的独立防错补充：仅对明确登记的当前注入提交发生错配时阻断，保留诊断和待处置状态，不能通过裁剪旧正文、容忍拼接或自动重送“修好”。它不清空草稿、不单独完成放行验收。不能把所有 signal 拒收统一改 exit 2，否则可能误挡真实用户提交或改变 Stop 行为；必须按结构化提交来源与 hook 事件区分。属于 hook 处理语义的另一个决定点，本轮不实现。

## 决定后的最小验证

**REALITY GATE：INCOMPLETE。** 目标是保持用户放行语义、避免把草稿合进登记派发；非目标是重新设计忙闲、使用读屏判状态或放宽 fake API 的独立 oracle。当前证据足以确认缺陷，不足以选择自动清空方案。

下一步由主控／构思主控选择 A 或 B，并确认记录语义与是否加提交前阻断。之后的 **Tracer bullet** 只做“实际 CLI Esc 恢复 → 草稿处理 → 一次用户放行 → 第二个独立 prompt/hook/API”，每次真实 CLI 启动仍单独审批、隔离 HOME、假服务、真实模型 0。不在已停止的 09A-2 根上恢复输入，不用旧 PASS 给新候选背书。

新探针必须包括多行恢复提示、用户另打一段未提交文字／组合输入、确认后的新输入、空框清空风险；分别核对正文没有合并、草稿未被未授权删除、来源记录正确、队列不提前放出、错配不消耗真模型。预期仍来自 spec／明确声明，不改变 API 的 exact input 断言。出现未知／矛盾即停，不重试。

## 保留根和 slot 的归档／删除交接

外置原件 8,124,728 字节已经存在并有主控字节读回 PASS；本轮只读取明确成员，未删除根或 slot。根内有 `latest` 和 CLI URL Handler 的符号链接，后者指向用户安装的 CLI；归档必须保留为链接，不能沿链接复制／删除其目标。

[处置脚本](dispose-draft-09a2.py) 固定绑定本根与本 launch 的 slot `/Volumes/WD-Elements/a2a-workbench/t078-09-d2d9c666-5621-4467-bbe4-d99450bd5503`，通过原 approval、实际构建来源／路径、Electron argv 与退出原件确认归属。执行主控确认诊断后另批：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-draft-disposal-09a2-01 '实际主控批准条目引用'
```

该阶段不启动任何 CLI／API／Electron，不发信号，不依赖产品 PASS。它要求已知 CLI 退出核对 PASS、daemon_stopped/Electron quit，并重新检查 manifest 的 shell/CLI/API/daemon/Electron 五个 PID 均不存在；PID 存活／重用或状态不明即 BLOCKED，不停未知进程。

原 cleanup INCOMPLETE 与 slot-cleanup BLOCKED 不改写。先在外置盘的新目录 `/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/draft-disposal-09a2-01/` 独占创建 root.tar.gz 与 slot.tar.gz，完整保存根／构建槽、不跟随链接；核对成员集合、链接目标及每个普通文件字节。两份都读回通过并保存清单后，才删除两个精确自建目录。外置未挂载、路径／来源错配、来源变化、归档失败均保留现场；不覆盖、不重试、不碰其他 slot。仓库只留小份清单／脚本／重放路径；新大归档直接位于外置盘，不落仓库。

[归档函数静态检查](draft-disposal-static-09a2/result.json) 已在新建本地夹具上核对保留链接；已知坏“跟随链接”变异体实际复制了公共夹具目标，被读回拒绝。未执行实际进程检查、外置写入或删除；脚本执行结果仍未验证。旧 73 文件快照不含本次处置入口，本入口单独提交／审批；不会再使用旧材料继续运行。

只读与本地重放：

```sh
python3 -B evidence/2026-10-11-batch13/T-078/read-draft-09a2.py --output /绝对路径/新读回目录
python3 -B evidence/2026-10-11-batch13/T-078/check-draft-disposal.py --output /绝对路径/新归档函数检查目录
```

原根处置后，完整诊断小份和外置完整归档仍保留；届时读取原根的命令不能冒称可直接重跑，应从新归档提取到另一个只读副本并记录路径。原材料中的运行 argv／批准／屏幕及失败命令全部提交保存。T-078 仍 open、INCOMPLETE、待主控关闭；本轮停在方案决定与处置审批，不启动下一探针。
