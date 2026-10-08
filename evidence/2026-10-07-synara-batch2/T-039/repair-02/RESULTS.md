# T-039 决定01执行记录（2026-10-08）

**BLOCKED，待主控决定；ticket保持open，待主控关闭。** 授权的两类修复已经取得红/绿证据，35项重跑通过；新真实运行完成 submit、独立oracle与CAS，但原自动run在回收时失败。没有把后续成功清理改写成该run成功，没有扩大未知状态分类或再次调用模型。

候选 `fc9e36c75af3bbcf701551abbb911883b94217c2`，父版本 `fa3fc3352805d00e41c454fa6f810807528de3a9`。本地fork提交只含 `apps/server/src/a2a/orchestration.ts` 和 `service.test.ts`；service.ts未改，不碰T-038、门禁核心或合同。未push。

## 三项验收

| 条件 | 当前结论与证据 |
| --- | --- |
| 一次完整真实run accepted且引用等于worker提交 | BLOCKED。[原run收据](real-01/run.json) exit1、`integrated_reclaim_failed`。业务task已accepted，C=M=worker HEAD=集成引用，oracle12/12；后续经门禁回收成功，但原run仍非completed，第一项不勾选 |
| home删除、用户数据不变 | PASS，限主控决定01指定核对范围。[清理](real-01/cleanup.json)确认两home不存在、进程组无存活进程、私有token删除；[前后比较](user-data-comparison.json)显示 config/rules大小及mtime、Synara顶层元数据、herdr status完全相同。未复制这些用户文件的正文或凭据，不宣称全机逐文件审计 |
| 不回答无人值守权限或问题对话 | PASS（本次运行）。原生快照无pending interactions，门禁human_intervention为空，observer始终healthy；未输入第二条任务、批准或回答对话。控制回收是资源清理事件 |

## 授权修复与反事实

目前没有跨SQLite投影与provider内存状态的原子快照接口，二者并发读取也不能变成共同快照。没有添加重试循环、sleep补丁、平行入口或修改GateRuntime合同。

- shell尚无turn、provider已有activeTurnId：保留turn=null，报告running，原run的有界观察继续读取；submit仍须匹配已投影turn，所以不能从该输入交付或推进oracle/CAS。两个非空turn不同仍拒绝。
- interrupted且provider运行时已不存在：可由原受锁reclaim停止、归档并读回；run观察仍拒绝为非完成。error、矛盾中断（provider仍活跃）和未知running输入继续拒绝。

测试只替换原生shell/provider服务边界，实际gate service、唯一门禁入口、SQLite操作锁和Git均保留。预期来自主控决定，失败方式在 [PLAN](PLAN.md) 中先列出。

| 证据 | 结果 |
| --- | --- |
| `seam-red.log` | INCOMPLETE，初始夹具漏project id；不是业务红态，保留不覆盖 |
| `seam-red-02.log` | 旧产品3失败/3通过：未投影派发、未投影deadline、中断回收的业务断言失败 |
| `seam-green-02.log` | 新候选6/6通过；包括两个非空turn不同仍拒绝、没有stop/archive或门禁状态推进 |
| `seam-final-parent-red.log` / `counterfactual.json` | 最终测试在父版观察转换上再次3失败/3通过；固定源码按原字节恢复，与已提交候选一致 |
| `orchestration-18/` | PASS，18/18，原T-037套件与原边界替身不改；候选版本在command.json中绑定 |
| `delivery-recovery-17/` | PASS，原8项交付+9项恢复全通过；T-036组合副本入口与独立oracle不改 |

17/18项的原始夹具保留原目录，并归档于 `retained-35-fixtures.tar.gz`。没有登记内嵌Git目录为gitlink。Trace保存真实命令、SQLite/Git回读、故障信号和业务断言；不能外推为真实模型证据。

## 全新真实运行及新状态差异

根为 `/private/tmp/a2a-t039-r02-lp49osng`，证据独立保存在 `real-01/`，旧run-01与首轮独立审查FAIL完全保留。

| 身份或配置 | 值 |
| --- | --- |
| task / run | `t039-pagination-r02` / `9f73fdd0-169f-4ea9-aecb-f80d20331b10` |
| attempt / session_id | `c7407179-e223-422d-b45a-06ca6ba8cef7` / `cc101b0c-4a96-4ca0-8f60-3c0387fe34a9` |
| fence / spec_rev | 1 / 1；规范synara-m1验证接缝2、T-039与主控决定01 |
| Synara thread | `18e0e6a3-4cb7-45fa-a930-65573fbf6a6f` |
| Codex原生会话 / turn | `01a11a3f-7ec7-7643-84f7-d34ee23074a2` / `01a11a3f-90d9-7111-a434-f439eeb218b1` |
| G / C=M=集成引用=worker HEAD | `07feda555805334a27a773ee101a38804cf481e8` / `b1f5f5178585377150ae046b5ee3fc27f4b10970` |
| runtimeMode / 模型 | full-access（沿T-035与brief）；gpt-6.1-sol、xhigh、fastMode=true |
| CLI | 固定standalone Codex 0.161.0；真实argv含 `-c 'service_tier="fast"' -c check_for_update_on_startup=false` |

只启动一个真实模型turn；provider后来有thread/resume连接，原始生命周期记录未隐去，不将连接重建误称新模型turn。原生设置报告serviceTier=priority、approvalPolicy=never、dangerFullAccess，只证明配置，不证明供应商计费、性能或成本收益。

原生 `a2a_submit` 的started/completed与原始结果在 [配对activity](real-01/native-submit-activities.json)、`native-submit-log-lines.json`和完整provider/rollout日志中；门禁 submitted→verified→integrated 在 [事件摘录](real-01/submit-events.json)。独立 [Git/合同/oracle读回](real-01/independent-readbacks.json)确认候选版本、冻结合同和oracle原字节不变，验证worktree与worker工作目录不同，12项包含unseen sentinel。

新失败时间线来自原始 [native-lifecycle-raw](real-01/native-lifecycle-raw.json) 与run收据：

- 06:44:17.080Z，原生turn/completed；06:44:17.116Z，session/closed。
- 06:44:17.242Z，gate waitForIdle读到provider不存在，但shell/latestTurn/session仍running；shell.updatedAt为06:44:13.926Z，拒绝 `run_external_unknown`。此时submit、oracle和CAS已经完成。
- 在原生completed读回后，用原attempt发 [reclaim](real-01/reclaim-after-failed-run.json)，返回 `stop_unconfirmed`。这是stop命令回执与投影读回之间的另一处差异，未隐去。
- [再核对](real-01/native-before-cleanup.json)确认session已stopped、turn completed、无pending。随后同attempt的 [门禁回收](real-01/reclaim-confirmed-idle.json)成功，[归档读回](real-01/native-archived.json)确认stopped/archived。该步骤是有新外部事实后的受控清理，不是新模型重试；原run失败收据不变。

这不是GPT模型提前结束或分工协调缺陷；worker已显式交付。属于原生运行时、投影与门禁观察之间的工程状态差异。主控决定01明确要求未知仍拒绝；把provider已退出但投影仍running改成可等待、或增加stop/archive的投影完成屏障，都需要明确下一步分类/一致性授权。最小选项是在同一接缝补这些输入的红态，选择有证据的原生状态或投影完成机制，再用新根重跑；本轮未实施。

## 隔离、检查与交接

服务直接从冻结checkout执行 `apps/server/src/index.ts`；没有使用可能过期的bundle。`candidate-sources-02.tar.gz`的1676个普通文件逐字节匹配checkout，绑定见 [candidate-binding](candidate-binding-02.json)。服务脱离调用者进程组，仅停止自己的PID 86488与其原生子进程。工具链/缓存经外置盘入口，未回退内置盘。

CODEX_HOME只复制auth.json，配置只信任核对过的夹具根，只有git add/commit两条allow规则，无hook。运行时实际CODEX_HOME和CODEX_SQLITE_HOME均在本次根。9个链接中6个数据链接在隔离根，3个临时执行链接指向固定Codex二进制，见 `real-01/home-isolation.json`；没有把执行链接误判成用户数据链接。源home与整个overlay已删除；凭据不入证据或Git。保留fixture/worktree和门禁状态原目录及归档，含私有认证状态的Synara userdata不归档。

| 检查 | 结论 |
| --- | --- |
| typecheck-02 | PASS，8/8；首次测试只读字段赋值错误日志保留 |
| lint | PASS，既有警告保留 |
| fmt:check | NO_GO，仅原有未跟踪 `.grok/settings.json`；自己的文件已用项目格式器检查 |
| 全仓test / Windows / 迁移 | NOT_RUN；新真实运行触发决策点，未继续全仓test。没有平台进程或迁移改动；不宣称全仓或Windows通过 |
| 用户前后核对 | PASS，指定大小/mtime与顶层列表一致；herdr status原始输出也完全相同。只读，不连接或修改用户Synara数据 |

命令、版本、时间与退出码见每轮 `*.json` / `command.json`，包括实际create、run的600秒submit期限、回收请求、observer状态、人工介入事件及原始失败。主控为任务书指定的Claude Code `wF:pM`；执行和实时观察由s2-t039完成，不称为独立monitor。本worker自身受管attempt/fence未提供，保持未知；表中身份均为夹具子会话。

新的fresh-context只读审查及冻结范围见 [acceptance-review](acceptance-review.md)、[frozen-manifest](frozen-manifest.json)和 [review-provenance](review-provenance.json)。它不能将手工补充回收改判为原自动run通过。当前交付不证明完整M1、UI、切换或发布。a2a提交号以最后 `T-039 DONE BLOCKED` 回执为准；原首轮报告与所有失败证据保持原样。
