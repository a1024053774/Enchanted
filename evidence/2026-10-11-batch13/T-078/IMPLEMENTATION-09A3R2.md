# 09A-3R2：执行主控预批的模拟用户动作

2026-10-14，主控 #150。**驱动局部契约 PASS；真实 CLI／窗口行为 INCOMPLETE，尚未启动。** 原 09a3r 两包绑定 `16650926`，材料提交 `6f0cfdb2c042ac27251dd979b56c792e4874f720`；本次改变了冻结的测试驱动，旧包不能再用于 launch，原材料和结果保持原样。

REALITY GATE: PASS（选择一次 Ctrl+C 并用实际快照证伪的计划）；实际清空效果 UNKNOWN。

- GOAL / NON-GOALS: 消除执行主控无法操作窗口、必须依赖用户在场的步骤；不改后台删字、门禁、Stop、拦截、API exact oracle 或真实模型预算，不启动、不删除 slot。
- DECISION / OBSERVED: 主控 #150 已明确授权逐项预批的 test-simulated-user。官方文档支持无操作运行时第一下 Ctrl+C 清空输入，第二下可能退出，见 [按键依据](KEY-BASIS-09A3R2.md)；旧真实窗口快照有横线包围的两行恢复草稿。官方依据不是当前实例实测。
- MEASURED: 旧 runner 等人工声明导致两个自动化正例契约失败；父版本 Electron 分支不支持 Control+C。新 runner 局部 14/14、窗口分支 13/13、原收据 12/12 PASS，实际 UI／CLI 启动 0。
- UNKNOWN / PROBE: 新实例在 Esc 退休及 API1 取消后，先见恢复草稿，再同窗一次 Ctrl+C；完整控制 action／准入／intent／written、新 offset、窗口编辑区为空、截图和相同 PTY highwater 必须齐备。任何残字、未知区、退出、缺证或输入代次改变均停 INCOMPLETE，不换键、不重试。
- NEXT ACTION / OWNER: 主控提交代码后生成新两包；本轮只交正例 launch 审批，真实验证由执行主控另批执行。

## 最小改动

仅测试驱动与材料工具变更，workbench/src、app、hooks、core.ts／taskCards.ts 不改。`electron_driver.mjs` 的同窗口 terminal-key 分支新增受限 Control+C：只允许正确 launch／thread、active 已退休、busy／running、窗口可输入且中断引用匹配时发两个原生键盘事件（keydown／keyup），返回 attempted，不称送达。inspect 额外保存真实 snapshot 的 window／interruption／input_generation；没有修改 IPC 返回或后台状态。声明仍点击真实界面按钮，返回 source=test-simulated-user。

runner 在打开窗口或发 Esc 前核对 actions 全局身份／场景／source，以及每一步的批准人、引用和依据。正例计划为 Escape、clear-restored-draft（唯一 Control+C）、declare-empty-release（truth=empty）；反例为 Escape、retain-restored-draft、declare-empty-release（truth=intentionally-false）。不接受旧人工列表或只填总批准。

正例在同一编辑区观察空框，保存 cleared-draft PNG／JSON、编辑区行号及相同 highwater 的 PTY 原字节前缀，再点击声明；不是后台清空，也没有从 textarea.value 假造 CLI 空框。声明沿生产 UI 路径引用 Esc 和当时 input_generation，事件读回仍核对一致。反例不给 Control+C，保留恢复草稿后点击特意不真实的声明，原 hook block／exit 0、API1-only 的断言不变。动作结果及 driver 请求日志记录 executor 批准的 test-simulated-user；生产 user_inputs 按真实窗口路径保存，通过 window／request／sequence 的收据关联来源，不冒称用户亲手操作。

## 红绿与反事实

先保存 [旧人工 runner 红态](simulated-draft-red-09a3r2/results.json)：七项中 clean／block 自动化完成契约均失败，实际分支仍输出 manual-draft-handling 并等不存在的人工放行。修改后同七场景 PASS，另加七个逐项批准／未见身份 sentinel 的契约，[最终 14/14](simulated-draft-green-final-09a3r2/results.json)。首次七项绿态独立保留，不覆盖。

另以父提交的原 Electron driver 跑新按键契约，[红态](simulated-window-red-09a3r2/results.json) 在 Control+C 正例报 Unsupported terminal key probe；同一探针在新分支 [13/13 PASS](simulated-window-green-09a3r2/results.json)，包括旧八项窗口绑定回归及新四项错目标／中断／active／只读拒绝。原 [Esc 收据 12/12](simulated-window-receipts-09a3r2.json) 保持 PASS。

把真实 helper 的空框结果在内存强改为 true，[残字反例](simulated-empty-mutant-09a3r2/results.json) 只在 reject-residual-draft 失败，说明已停止依赖实际观察；把批准校验强改为无操作，[批准反例](simulated-approval-mutant-09a3r2/results.json) 触发缺逐步批准、错来源、旧 session、未批键、假 clean 声明及缺总引用六项违约。变异只在测试进程内，不修改候选文件，不运行窗口、CLI、模型或服务。

这些探针执行实际 runner／Electron driver 闭包，但 client、窗口／收据事实是合成的；不能替代真实 xterm 产生 0x03、CLI 清空、PNG 画面或 API 是否送达的边界证据。新两包的真实场景和独立 reviewer 仍 INCOMPLETE，不借用旧候选的通过结论。

## 版本与清理边界

新增 generation 09a3r2／block、新 source snapshot 和逐步批准模板。当前 outside 包装只选择 09a3r2，旧 generation 被拒绝；slot-cleanup 明确停在主控 #150 的删除保留要求，不调用删除工具。root cleanup 也不在本次 launch 审批范围，等主控到清理阶段再定。本轮不请求提权，不 add／commit，不 push。代码提交与最终材料提交均交主控脚本执行；尾注只由 hook 添加。
