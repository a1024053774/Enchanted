# T-152-1 / a1 交付记录

状态：**INCOMPLETE**。04 的单个正常 tracer 已由主控实跑通过（7 条业务断言、清理失败 0）；原读回器字段错误已修复，同一现场离线读回 9 项全部 PASS。全套业务 mutant 红态、完整绿态与回归尚待 05，不能据此验收或集成。产品代码未改。起点 `32ffb4e6dcc0472b20bbb64331a355621c9b73a9`，分支 `exec/t152`，worker `b23-t152`。

## 逐条改动

编辑前逐项清单与独立依据见 [ASSERTIONS.md](ASSERTIONS.md)。预期来自 T-152、T-141 的用户裁定和 T-082 的仍有效契约；产品只用于定位变异，不提供答案。

1. `T082-REVIEW-ARGV`：旧网络关闭改为网络开启，旧强制代理关闭改为无此关闭覆盖；保留 workspace-write、cwd/worktree 绑定副本、共享 tmp 禁写。补 `-a never` 和 reviewer 一次性副本 untrusted 核对（T-141 的明确例外）。
2. 全部副本创建/删除、请求完成条件/变异要求、report 落库、共享 refs、workspace 绑定、脏结束作废检查保留。held socket 脏/干净两个对照都保留。`REVIEW-END-BEFORE-INTEGRATE` 额外要求错误为 `review_end_check_required`，并移到释放 socket 前检查，防止坏实现先集成后引起别的夹具错误遮住红态。
3. 默认绿态只排除 `launch_boundary_refused`：该检查必须提供非法启动变异，原默认把它与正常代码一起跑会要求同一合法启动既成功又拒绝。它的三条断言没有删除，沙箱外脚本逐个覆盖 readonly、错误 cwd、网络关闭、共享 tmp 可写。
4. 专用 `t152_review_host.ts`：仍调用共享 controlled PTY；仅在它第一次 Enter 打开隔离的 untrusted 文件夹后发 native ready。真实后台、CLI、门禁、Git/SQLite、Stop/relay 与结束回调均保留。测试新增 `start_host` 指向该 host，保留原有凭据、PID 和脱离进程组核对；未改共享 host 或 PTY 文件。
5. 专用 `t152_real_review_submit.json`：逐字节复制 Git 中 `32ffb4e6d:evidence/2026-10-15-batch15/T-082/protocol-red-green-01/real-review-submit.json`。原小输入受控但稀疏 checkout 缺失；没有从当前产品模板生成期望，原 roundtrip 检查全部保留。
6. 专用 `run_suite.py`：支持 `--summary` 新路径、`--revision`、`--mutant`；每次用 Git archive 创建临时产品副本，变异不写产品 checkout。只认指定 `ContractFailure` 为红态，harness_error、清理失败或错误 failure_id 一律 INCOMPLETE。保留原始现场，仓库只留小摘要；由主控按 T-088 归档。
7. 冻结候选 `dbd82308a` 的独立只读审查发现两项夹具阻断（见 `acceptance-review-01.md`）：按 T-123 在局部 `configure_host` 将 gate/packet/trailer 的任务身份统一为 `fixture+短名`，卡片 id 仍为短名；按 T-127 用现行 `reviewer_role_card` 与 `reviewer_role_card_revision` 替代旧 `reviewers` 数组。未修改共享 QualityCase。修正后尚未取得运行证据，原审查不替修正后的候选背书。

新增辅助文件只有上述 host 和 JSON 输入被本测试加载；`run_suite.py` 与 `RUN-OUTSIDE-01.sh` 是本票复跑入口。原 `run_t082_boundary.py` 被其他测试导入，不符合“只被它使用”的边界，未修改。范围外发现已经 `scripts/inbox` 上报 `20261023T190056Z-worker:b23-t152-issue-001`，正文见 [issue-legacy-runner.md](issue-legacy-runner.md)。该追加式 inbox 条目保留在工作区，未把 `.project-map/**` 纳入交付提交。

## 已运行

- 编辑前命令：`python3 -B workbench/tests/test_t082_review_boundary_e2e.py --source . --output /tmp/t152-baseline-01 --case tracer_review_copy`，exit 1。真实 host 已启动，但 `/bin/ps` 被沙箱拒绝，outcome=harness_error，零业务断言；不是红态。原始现场 `/tmp/t152-baseline-01`；夹具 `/private/tmp/q76-lgkwuo0t`，清理失败 0。
- 迁移后命令：`python3 -B evidence/2026-10-23-batch23/T-152/run_suite.py --mutant no-end-check --summary evidence/2026-10-23-batch23/T-152/sandbox-01.json`，exit 1，仍为同一 `/bin/ps` 权限失败；脚本正确记 INCOMPLETE，未误计为红态。版本、变异、命令、现场与 cleanup 见该 JSON。
- Python 两文件 AST 解析、`node --check workbench/tests/t152_review_host.ts`、`zsh -n .../RUN-OUTSIDE-01.sh`、`git diff --check`：PASS。只证明语法和差异格式。

## 主控沙箱外复跑

下一轮运行：`zsh evidence/2026-10-23-batch23/T-152/RUN-OUTSIDE-05.sh`。01～04 脚本和原始结果均保留。04 读回修正、离线验证及 05 步骤见 `REWORK-05.md`。

05 先用新 fixture 跑单个 tracer 与完整读回，再跑 8 个变异、全部正常场景与 T-090/T-141，摘要写入新的 `outside-05-XXXXXXXX/SUMMARY.json`。前置正例/读回失败即停止扩展，变异和完整绿态判据保持不变。

## 01 运行结果与第 2 轮改动

主控 #6 实跑 `RUN-OUTSIDE-01.sh`，绑定 `c4197a89b`，摘要 `outside-01-cudCk6ZY/SUMMARY.json`：T-141 reviewer PASS，其余 10 项 INCOMPLETE，均为旧 pane_release 调用导致 CLI exit 2、零业务断言。它们不计为红态。绿态完整现场 `/private/tmp/t152-m9rps0h_`，摘要逐项列出其他现场；原始现场均保留。

编辑前逐层命令清单与依据见 [REWORK-02.md](REWORK-02.md)。本次只在 ReviewBoundary 覆盖 release_worker，并移除本地 start_review 的 pane_release；两者都等待真实后台的 busy / fixture-turn-1 和绑定本次 launch 的 codex_startup_ready 事件。依旧由受控原生 PTY 输入触发，未直接调 drain、未造事件。

01 还出现 request 证据采集失败：旧共享 close_fixture 不接受产品创建的 `.a2a-tmp/`。本次局部覆盖原清理流程，保持数据库/Git 读回、进程身份与退出检查、凭据核对/删除及错误记录，只将请求证据采集迁成递归保留目录（包括空目录）与普通文件；仍拒绝 symlink 和特殊文件。复制清理流程是因为共享测试不在修改范围，未新增产品兼容路径，也未删除原现场来迎合旧检查。

本轮静态检查、目录采集反例结果写入 `local-checks-02.json`。它们不能替代 02 沙箱外端到端红绿态；最终状态继续 INCOMPLETE。

独立定向复审冻结代码 `dd52f5816`，记录见 `acceptance-review-02.md`：无新增静态发现，状态 INCOMPLETE，未运行 02，不据此宣布验收通过。

## 02 运行结果与第 3 轮改动

主控 #9 实跑 02，绑定 `02fe808bd`。摘要 `outside-02-JpvDMYo4/SUMMARY.json`：T-141 reviewer PASS，另 10 项 INCOMPLETE、零业务断言，均在自动放行后等待原生 turn 超时；清理失败为 0。现场与时间线核对见 `REWORK-03.md`。

专用 PTY 已在任务 Enter 时写 rollout，却没有发输出，因此真实后台没有及时触发 onData → scan。本轮只给非首个 Enter 后补异步普通文本输出，保留 wait_pane 与全部业务断言，不调 scan、不改门禁或共享 PTY。`node --check`、03 脚本 `zsh -n`、`git diff --check` PASS。尚无 03 端到端运行证据，状态 INCOMPLETE。

## 03 结果、整链走查与第 4 轮

03 主控实跑摘要 `outside-03-NM4823lV/SUMMARY.json` 绑定 `b3521197e`：T-141 reviewer PASS，另 10 项在 ACK 前 harness_error。首轮 turn 已绑定，但 Stop 被 question_origin_unverified 拒绝；relay 尚未执行。完整只读审计 `FLOW-AUDIT.md`（PLAN `a6a8e9c84`）区分了运行事实与静态下游契约，主控 #12 确认继续范围。03 的局部问题不能算业务 mutant 红态。

第 4 轮统一三处 Stop 信封，信号错误即时带详情失败；保留共享基类和原业务断言。新增 04 单例脚本，按既定契约逐项读回，不以一个进程 exit=0 替代完整流程证据。具体改动见 `REWORK-04.md`；本轮本地检查结果见 `local-checks-04.json`。04 正例、held-socket 及完整红绿态均未运行，不宣称 PASS。

## 04 结果与第 5 轮

主控 #13 实跑 04，版本 `971fafbf5`。正常 tracer outcome=passed、7 条断言全过、cleanup_failures=0，原聚合因读回器 KeyError('id') 记 INCOMPLETE。dispatch id 属于数据库行顶层，不在 data JSON 中；本轮只修读回字段并提取供 04/05 共用的 read_tracer_flow.py，没有改产品、测试或断言。

原现场完整离线重读 `offline-04-reread-01.json` 为 PASS、9 项全 true；原 `outside-04-UXB2hit2/SUMMARY.json` 保留 INCOMPLETE。具体证据与限制见 `REWORK-05.md`。本轮已准备 05，但未运行，T-152 总状态继续 INCOMPLETE。

局限：当前没有有效业务红态、绿态或 T-090/T-141 新回归通过证据；不声称真实原生 CLI 沙箱、网络访问或模型判断得到证明（原生 CLI/模型回合为 0）。不复用历史 PASS。最终验收、独立审查、submit/集成由执行主控门禁负责。
