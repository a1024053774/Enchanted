STATUS: PASS

FINDINGS:

- [P2] `workbench/tests/test_t230_terminal_hc_isolation_e2e.py:173` — `agent_call.exit` 只记录、不参与判定。如果终端里的 hc 在实际调用前失败，holder 正常恢复仍可让全部检查通过。建议断言夹具中的调用退出码为 0，并核对 `ls` 的有效响应。本次 `green-ui-05/run.json` 的 `agent_call.exit` 确为 `"0"`，因此不阻塞当前候选。
- [P2] `T-230-evidence/REPORT.md:36`、`:39` — T-216 worker 实际执行的是门禁 CLI，使用 `A2A_CAPABILITY`，并非项目终端的 `a2a issue`；不能据此推导“只依赖终端令牌”。依据：`test_t216_prompt_provenance_e2e.py:29`、`scripted_claude.py:66`、`src/gates/cli.ts:209`。跨终端投递及来源记录的覆盖成立，报告应准确区分身份路径。

EVIDENCE:

- 已逐字比较 `candidate.patch` 与五个文件相对 HEAD 的 diff，一致；HEAD 为 `121c43f21`。
- `src/panes.ts:311`、`:331`：hc 项目终端启动前删除四个变量，保留独立注入的 a2a 身份。worker/reviewer 使用 `:1030` 的显式环境白名单；旧主控入口使用 `claudeLaunch.ts:76` 的显式环境，均未传入四个变量。
- `red-race/run.json`：`parent=1`、`holds_private_lock=false`、`foreign_state_exists=true`，且原 shell 消失；绿态三个判据相反，原 shell 接回。当前证据中的竞争调用没有空转。
- `src/hc.ts:128` → `src/panes.ts:1949` → `src/daemon.ts:842` → `app/renderer.tsx:504`：提示来自 hc 的 screen 状态，只对明确的 `inexact` 显示；exact、缺失或未知值不显示。已查看绿态两张截图。复位与接回代码未改。
- `green-boundaries-02/run.json` 五场景通过；`red-boundaries/run.json.error` 明确显示四变量泄漏；`mutant-leak-xdg-02/run.json.error` 显示仅 XDG 泄漏、四变量仍不存在。缓存路径调整未削弱损坏缓存拒绝断言。
- T-216 两份 provenance summary 的 `system_not_user`、`same_body_claim_once` 均通过；GUI summary 记录完整派发及原生实际提交。回归结果与 REPORT 一致。
- 候选生产代码未新增吞异常、fallback、兼容分支或平行路径。

LIMITATIONS:

- 全程只读，未重跑测试、启动服务或连接 hc/供应商。
- 历史运行未逐次记录完整源码版本；红绿态的版本归属依赖所提供的报告，失败现象与基线代码相符。
- 未实测用户真实 HOME；未知 screen 值的界面行为仅作静态核对。