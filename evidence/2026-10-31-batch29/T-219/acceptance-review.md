STATUS: PASS
TARGET: 基线 a09da15f93d949eff9f81b46b071e58b9ba28af6 加 T-219-evidence/candidate.patch；仅限冻结的 12 个测试及夹具文件，不是产品发布结论。
EVIDENCE:
- 12 个工作树文件与 frozen-candidate 逐字节一致；差异没有产品文件。起止 project_map status 均为 0 problems、0 stale。
- 独立依据 T-123/124/108/141/187/191/193/195/200/203/096 重建契约：项目限定任务身份、attempt 卡快照中的 CLI、完整 hook 来源、review_submit 文件提交、空 shell 空闲、未批准 Claude 未知、主控可跨已打开项目。
- baseline-01-repeat、02、03、04、05、06c、07、08、09 均保留了对应失败。7/8 的基线确实停在夹具 card_save；没有把它们冒充恢复或窗口业务红态。
- green-01、02、03b、candidate-04b、green-05、candidate-07d、green-08-final、green-09 支持八项测试修订。7 的五个恢复测试均完成；8 实际启动 Electron，截图显示真实任务、已认领、只读和未知窗格；9 检查双向跨项目与真实 pwd，同时保留未打开项目、cwd、符号链接和未批准身份拒绝。
- baseline-06c 使用真实 Codex TUI、真实记录及文件权限，仅模型传输改为仓库本地脚本 API。实际失败与日期诊断吻合：纽约回拨日相邻日历日期相距 25 小时，24 小时上界漏扫次日。
FINDINGS:
- [P2] workbench/src/nativeLink.ts:139 — 既有产品缺陷：日历递增配合固定 24 小时扫描上界，在回拨窗口漏掉次日目录，读不了该目录时仍可能返回可用旧链接。此候选正确保留红态；后续产品缺陷票应修扫描范围并补固定日期的回拨反例，不能靠改时区或放宽断言关闭。
COUNTEREXAMPLE:
- mutant-01：空 shell 伪报运行中，被 home_terminal_header_known 拒绝。
- mutant-02/03b：忽略中断、把 Esc 改为 Enter，分别被缺少 runtime 调用和实际按键比较拒绝。
- mutant-04c/05：丢弃有效 relay、未批准 Claude 伪报运行中，分别被 Stop 记录数量和 unknown 状态断言拒绝。
- mutant-07/08/09：丢失 interrupted、伪造 snapshot 状态、恢复跨项目拒绝，均在业务断言失败，已越过相应夹具准备。
LIMITATIONS:
- “九项均经完整真实 CLI 入口复验”不受证据支持：2/3 明确为 L1 隔离逻辑；4 为真实 daemon/relay/CLI 传输加 PTY spy；7 为真实 daemon、SQLite、Git 加受控 agent；1/5/6/8/9 含真实本地入口。报告应逐项标层，不合并上调。
- 新增期望没有导入产品答案；契约与错误变异提供独立支持。8 的 bridge 名单只证明导出表面，不证明名单内每个方法可用。
- 能力范围：编排、异步、身份、交互、文件与本地 Git 副作用适用；恢复仅证明受测本地边界。检索记忆 N/A；生产渠道、部署和真实模型判断 N/A。
- 未重跑昂贵测试或调用真实模型。初轮 TMPDIR 越界写入属于单列的操作边界问题，本 PASS 不覆盖它。
RULE:
- 产品缺陷票的真实 native_link 验收应加入固定 DST 回拨日期、不可搜索次日目录和新线程记录，要求身份无法核实时链接不可用。
