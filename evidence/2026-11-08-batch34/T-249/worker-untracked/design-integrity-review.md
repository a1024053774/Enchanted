STATUS: PASS
SUMMARY: 本卡限定结构自查未发现已复现缺陷。按任务卡在实现会话内自查；不是主控安排的干净只读独立审查。
TARGET: scoped-repair.patch；相对 18c108fcaed1c4ecf51831f2272578a3b09427be，仅三个产品文件及两份开发测试的新改动。已测输入绑定 5ca17101d350e54582cb301d4f8c9166d63338b5，证据归入期间没有产品或测试变更。
FINDINGS:
- 无。
EVIDENCE:
- 扫描器标记 GitGraphPanel.tsx 的 openDiff catch。原 C 已有此边界，真实调用为文件点击 → host.git.read → IPC/gitRead；读取拒绝或 Git 失败进入这里。组件拥有当前文件的错误展示，新增选择身份核对后，只更新仍属于该次加载的状态。当前请求的错误没有被吞掉；关闭或改选后的旧结果不再更新界面。
- gitHost.ts 只为精确 no-index 形式把 Git 规定的“有差异”退出码 1 且无 stderr 转为既有 GitResult 成功码；其余失败原样返回。这是 Git 退出语义适配，没有重试或替代数据源。no-index-git-probe.json、local-01/host.txt 及 force-text 反例覆盖真实 Git 行为。
- 路径约束由实际执行 Git 的主进程拥有。diffArgs 生成参数，沿用 gitRead 与 diffRows；没有平行 API、浅包装或新依赖。unsafe-options 和 unsafe-paths 变异分别被选项和文件边界断言拒绝，真实 git-dir/common-dir 路径及文件原始字节保持。
- 主控窗口组 candidate 的 200 项检查通过；deferred-candidate 的 49 项检查通过，stale-diff 变异被“关闭 diff 后迟到内容不能重开”拒绝。后者是在测试副本中控制真实读取结果的返回次序，不伪造文件内容；正常候选另行运行。
- 旧 C 的列宽本来可以拖动与复原，候选仍为表头/行 128 → 192 → 128 px。本轮没有修改列宽产品实现；no-resize、no-reset 变异均被对应几何断言抓住。
- Stop hook 的原候选异常处理逐项来源、可达调用、失败和恢复归属见 stop-hook-check.md。保留合法处理，不为消除定位提示删除它们。
LIMITATIONS:
- 自查只围绕本次修复、只读边界和新增检测能力，不重审原 C 整套面板、RUN-OUTSIDE 或其他设计。准确恢复基线见 corrected-baseline-verification.json。
- 本次结果来自 worker 本地宿主测试与主控沙箱外真实 Electron 测试，执行者边界见 RESULTS.md。窗口原记录没有运行时提交字段；绑定依据和限制见 controller-evidence-import.json。
- 最终独立审查、新 Test 包和 Terra Computer Use 仍由主控完成；本结论不替代它们。窗口前的自查原文保留在 pre-window-self-check/。
RULE:
- 新增读取路径必须通过同一个 gitRead 边界，以真实 Git、原始文件和元数据原始字节核对；不靠子命令名或源码字符串证明只读。
