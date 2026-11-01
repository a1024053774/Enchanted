STATUS: FAIL
TARGET: round6-candidate-review1.patch（审查时名为 round6-candidate.patch）
EVIDENCE:
- 已批准 Claude/Codex 的原生提交默认记录为用户输入；只有后台已实际送出且未认领的 inbox 派发可排除一次。
- 冻结候选先持久化 hc_send_intent，再调用 terminal.send；两者之间退出可留下未发送意图。
- 独立只读审查从冻结补丁提取 claimShellInboxPrompt 原体，用 Node SQLite :memory: 构造 intent→恢复 unknown、没有实际发送的记录。结果 actualBackendSends=0，actualNativeSubmissions=1，claimedAsSystem=true，claimEvents=1。
FINDINGS:
- [P1] workbench/src/panes.ts:487 — 仅有意图加未知也可认领，恢复后用户相同正文漏记。纯意图不能消耗系统排除名额。
COUNTEREXAMPLE:
- 未实际发送的正文，在 intent→恢复 unknown 后由用户原生提交，候选错误排除；现有 provenance 未覆盖此窗口。
LIMITATIONS:
- 审查时完整矩阵未完成；反例是冻结方法的隔离逻辑复现及静态可达性分析，未运行真实入口故障注入。
- 本次独立 explorer 只读审查未修改文件、调用供应商或连接 hc，不替代 agy 审查。
RULE:
- 增加 intent 落库后、RPC 发送前退出的真实入口场景；恢复后提交该正文，应留一条用户输入且无系统认领事件。
