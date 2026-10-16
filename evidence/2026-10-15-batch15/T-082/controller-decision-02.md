# T-082 主控记录 02（2026-10-15 UTC）

worker 第一切片后，沙箱外批次均由主控运行（OUTSIDE-COMMANDS-01..07）。worker 三次自行请求沙箱外升级（主控两次 Esc、用户一次选 No），之后改为全部交脚本。
- 01：副本复制探针，经 ROOT 路径错、目标不在 state、仓内 symlink 解析回源三次失败后 PASS（仓内 symlink 按内容复制、越界拒绝，SYMLINK-POLICY.md）。主控代删 worker 留在 /tmp 的 3 个临时项。
- 02：tracer + 四种启动参数变异；首轮 wrong-workspace 未被拒——产品缺陷（reviewLaunch 未核对 argv -C），修后全 PASS。脚本 find /tmp 不跟随符号链接，8 个 q76 目录由主控打包入证据后删除。
- 03/05/06：结束核对 PASS；T-077 PASS；T-076 质量 runner 被自带源码审计拒收（审计要求验收文件相对 a7f4cc30 不变，而 D3 必须替换只读断言，属预期后果）；主控否决了用 MAIN_ROOT 跑回归的 04（测不到候选）。
- 07（检查点提交 0dd00d09d 上）：票据点名的 T-076 三项性质 tracer_wrong_candidate、tracer_reused_native、tracer_writer_cannot_review PASS。
- 待：launch-policy 夹具错疑为旧快照 taskCards.ts 无 oracle_paths（需在 main 上证明既有）；T-076 runner 锚点是否迁到新基线作为待决问题上报；真实 Codex 回合（≤4）脚本待主控审。

## 真实 Codex 第 1 回合 #44–#46（2026-10-16 UTC）

REAL-CODEX-COMMANDS-01.sh 两轮审查后改为纯产品路径（daemon_start → card/create/claim/submit/verify → createReview → Panes），外置盘夹具，逐回合 JSON 批准。主控签 round-1（#44）。
- fixture-01：verify 拒 isolated_codex_home_required（脚本把 daemon HOME 与 CODEX_HOME 放成 HOME/.codex），未启动 reviewer、未耗回合。
- fixture-02：pane_release 拒 foreground_codex_required（隔离 home 缺信任配置，Codex 停首屏；屏幕未存），未耗回合。
- fixture-03（隔离 home 写入夹具根信任、git add/commit 两条 prefix_rule、首启 UI 标记，均留证）：reviewer 完成 1 个真实回合（消耗 1/4）。报告内边界证明齐全：副本写入与测试成功；审查目录、worker worktree、共享 .git 写入 Operation not permitted；git update-ref exit 128；curl 域名/直连 IP 均失败；完成条件节 3 个变异均被拒。但门禁以 review_request 拒收 review_submit（review_protocol_failed，task paused），runner 900 秒超时保留现场。
主控处置：转录 gzip 归档外置盘（含 Codex 指令原文，不入仓库），daemon_stop 停 31690，删除隔离 home（含 auth 副本）读回 absent。#46 交 worker 查 review_submit 解析契约并补红绿。

## 真实第 2 回合 PASS #48（2026-10-16 UTC）

检查点提交 7f2bd4061（review_submit 契约修复 + 报告节键检查，离线 12 项 PASS）。fixture-04 偏弱任务卡（目标要求 value.txt 与 details.txt，oracle 只查 value.txt）。主控签 round-2（#48）运行：real-readback 九项全 true（入库、候选不变、审查目录移除前干净、worker worktree 干净、共享 refs 不变、副本删除、审查目录移除、review_reclaimed、哨兵不变）；报告含"完成条件与变异检查"、5 个变异；reviewer 判"需修复"并指出漏查 details.txt。隔离 home 删除读回 absent。累计真实回合 2/4。#48 让 worker 收尾 RESULTS.md。

## 改前红态补齐与独立审查 #49/#50（2026-10-16 UTC）

OUTSIDE-COMMANDS-10.sh（起点 451be8462 源码，外置盘夹具，受控 PTY，0 真实回合）：wrong-workspace、network-enabled、tmp-writable 三案在旧门禁上 T082-LAUNCH-REFUSED 失败（ok:true，未拒收），对应候选绿态已有；只读 argv 红态见 red-state/。提交 9c771dc72（收尾证据）、f589d1938（红态补证）。
#50：新开 fresh Codex reviewer s16-t082-rev（wF:p4B），argv 同 T-078 审查员；只写 independent-review-01.md 与 REVIEW-OUTSIDE-01.sh。

## 独立审查 01 NO_GO 与返工 #50–#54（2026-10-16 UTC）

fresh Codex reviewer s16-t082-rev（wF:p4B）审 f589d1938。其沙箱外脚本经三轮（归档白名单过窄、读库路径失效两次脚本缺陷后）跑通：01–13 段全部 verified（5 个错误实现均被对应断言检出）；14、15 段 contract_failure。结论 NO_GO：[P1] 收到报告即 verified、结束核对前可 integrate 并前移 main，事后失败不作废（审查经真实 socket 复现）；[P2] review_requirements workspace 未与本 review 副本绑定；[P2] 结束核对负例覆盖不足（M3 被放过）；[P2] T-076 launch-policy 默认 tier 负例被换观测点；[P3] 同值条件表达式。审查报告提交 f09f0dcc8，审查窗格回收，/tmp 输出与夹具归档外置盘后删除。#54 派 worker 按此返工。
