# T-262 首轮审查补证与恢复

外部补证 PASS；T-262 整体 INCOMPLETE，尚未通过门禁独立审查或集成。

审查员 4900e31c 在自己的唯一候选副本构造四个 .diff。候选和变异在该副本都因没有 Git 元数据而在入口退出；原始 stdout/stderr、mutation-results.json、补丁和源码均保留。额度耗尽发生在 MCP 保存“需修复”草稿之后、Stop 之前，门禁未收到正式 verdict。原始回合错误见 T-264 证据；没有用该草稿替代门禁结论。

主控按任务卡外部测试分工，将审查员补丁原样用于自有候选 checkout，运行原完成命令。`external-01/summary.json`：正确候选 38 项 PASS；取消排序、回执任务过滤、会话过滤及完整回执四个变异均命中各自业务断言。运行者是主控，变异设计者是独立审查员，不声称审查员本人在沙箱中跑通。`run_external_mutations.py` 保留重现命令、源文件逐字节恢复和夹具清理。正常 worktree remove 已删除主控自己的外部 checkout，未改审查副本。

真实打包窗口的键盘补证在 ../controller-test/KEYBOARD-COMPLETION.md：原生 typeahead 选择任务、Tab 后选择 worker、切到仅回执任务和 Enter 展开 JSON 均可用。初次点击/箭头未完成的 CUA-RESULTS.md 仍保留为历史 INCOMPLETE，不覆盖。

用户重置额度后，原审查员仍被后台视为 busy；它的窗口只读，无 worker 的空输入放行入口。旧 attempt 已经正常 abandon（升级），review 标 cancelled，再经 gate reclaim 回收空闲、已交付 worker；C=6e92ec6f0d0b59423f5f1bcb85cc39174da70bf5 保留。取消审查不等于通过。下一次只对同一产品的这些补证做限定复核，不新增一轮整体盲审。

Works：38 个候选行为和审查员四个错误实现得到独立预期结果；键盘操作有真实窗口与 AX 证据。
No regression：双区过滤、源记录身份、原文、刷新切项目等由同一 38 项覆盖；未运行依赖 Claude 的旧全套测试，不声称全套通过。
Risk / undo：原生错误回合恢复缺陷另开 T-264；保留正式安装不变，候选尚未安装，可继续按门禁恢复审查或留作未完成候选。
