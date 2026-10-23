# T-156 逐项覆盖对照

状态：**INCOMPLETE，需要决定**。`test_t078_quality_host_bootstrap.py` 含唯一直接守护者；两份目标文件均保持原样。`run_t082_boundary.py` 的门禁检查已有替代或针对已废止契约，但仍被该 bootstrap 导入，不能单独删除。未修改 HISTORICAL.md，因为本轮没有执行删除或获准改变处置状态。

检查范围为当前起点 `8933ee0f4e4667a6f927e18975fe2cb8cc58729b`。逐项依据为任务卡、T-156、T-152 的 ASSERTIONS.md、T-141 的现行网络契约，以及以下测试的实际断言；没有把测试文件名相似或启动成功当成等价覆盖。

## 当前起点实跑

主控 #26 回传的命令为 `python3 evidence/2026-10-23-batch24/T-156/RUN-OUTSIDE-01.py`。脚本 rc=0 只表示两个入口均执行并捕获结果，不代表两份测试通过。小摘要见 [BASELINE.json](BASELINE.json)，完整原始摘要在 `outside-01-rdfqsz3d/SUMMARY.json`，未改写。

| 入口 | 结果 | 边界 |
| --- | --- | --- |
| `run_t082_boundary.py --source <本 worktree> --output /private/tmp/t156-baseline-ytdo105d/legacy-runner` | exit 1，INCOMPLETE | 正常 tracer 的 7 条断言通过、清理失败 0。随后第一个变异报 `mutation target is not unique: const sandboxMode = "workspace-write";`；四个变异均未运行，不能计为业务红态。 |
| `test_t078_quality_host_bootstrap.py --output /private/tmp/t156-baseline-ytdo105d/quality-bootstrap` | exit 0，PASS | 两代实际 quality host 凭据、清理、失败日志复制共 4 项通过。serve 在 socket 前被拦截，不证明 daemon/PTY 或原生 CLI 边界。 |

## 旧 runner

现行端到端文件记为 `workbench/tests/test_t082_review_boundary_e2e.py`；现行变异入口为 `evidence/2026-10-23-batch23/T-152/run_suite.py`。下列“已有覆盖”指代码中的具体检查，不把 T-152 旧版本的 PASS 当成本轮复验。其历史 `outside-05-wPqfIlhV` 绑定 `35f691dcc5d985664b4f939618176eb3c49e0d66`，四个启动变异均 PASS；本轮仅正常 tracer 在当前起点重跑。

| 原检查/辅助职责 | 当前对应检查 | 判定 |
| --- | --- | --- |
| 机械检查后建立审查 | `tracer_review_copy → start_review / T082-REVIEW-START` | 已覆盖，本轮 PASS。 |
| 正常 reviewer 的 sandbox、cwd、副本 worktree、网络、代理、确认策略和 tmp argv | `start_review / T082-REVIEW-ARGV` | 已覆盖，本轮 PASS；当前为网络开启。旧 runner 本身只调用此检查。 |
| 请求包含完成条件与 oracle_paths | `tracer_review_copy / T082-REQUEST-COMPLETION` | 已覆盖，本轮 PASS。 |
| 请求包含 2～5 项变异与报告节名 | `tracer_review_copy / T082-REQUEST-MUTATIONS` | 已覆盖，本轮 PASS。 |
| 非 Git 候选副本及创建事件 | `tracer_review_copy / T082-COPY-CREATED` | 已覆盖，本轮 PASS。 |
| 合法结果使任务 verified | `tracer_review_copy / T082-REVIEW-VERDICT` | 已覆盖，本轮 PASS。 |
| 副本物理删除与删除事件 | `tracer_review_copy / T082-COPY-REMOVED` | 已覆盖，本轮 PASS。 |
| readonly reviewer 变异 | `run_suite.py MUTANTS['readonly-argv'] → launch_boundary_refused` | 已覆盖：`T082-LAUNCH-REFUSED` 核对 `review_launch_boundary`，`T082-LAUNCH-PAUSED` 核对 paused/unknown，`T082-LAUNCH-ISSUE` 核对问题事件。当前起点未重跑该变异。 |
| 错误 workspace 变异 | `MUTANTS['wrong-workspace'] → launch_boundary_refused`，同上三条断言 | 已覆盖；当前起点未重跑。 |
| 网络开启须拒收 | T-141 已允许网络开启；现行 `T082-REVIEW-ARGV` 要求 true，`MUTANTS['network-disabled']` 经同上三条断言拒绝关闭网络 | 旧契约已废止；禁止保留“开启拒收”作为现行要求。 |
| 共享 tmp 可写变异 | `MUTANTS['tmp-writable'] → launch_boundary_refused`，同上三条断言 | 已覆盖；当前起点未重跑。 |
| 变异源码副本、退出码/报告聚合 | `run_suite.py` 的独立 Git archive 副本、精确断言/失败类型与清理失败判定 | 旧 runner 是执行基础设施，无独立业务契约；旧锚点失效已由本轮实跑保存，不为修绿而迁移。 |
| 失败前复制 stderr/stdout/start.json 的 `run_case` | `test_t078_quality_host_bootstrap.py / failed-run-copies-host-stderr` 仍调用旧函数 | 这是旧 runner 的诊断职责；没有找到新 runner 的同名复制检查，新 runner保留整份现场而非该复制协议。不能借删 runner 破坏仍有效 bootstrap 的 import。bootstrap 只断言 stderr 内容，不声称三个文件都已验证。 |
| owned fixture 归档/删除、mutation fixture 清理 | 当前 `run_suite.py` 保留现场，按 T-088 由主控归档 | 旧 runner 自有生命周期，无现行门禁安全检查缺口；本轮归档了正常 fixture，保留失败的 mutation 现场。不能把清理成功当作门禁通过。 |

## Quality host bootstrap

这里守护的是测试基础设施：共享 `QualityCase.start_host` 与 `quality_chain_host.ts` 确实会建立正确的隔离 operator 凭据。它不是生产权限或真实原生 CLI 验收。共享 host 没有在本轮被删；它仍由 `test_quality_chain_e2e.py` 引用。

| 实际断言 | 最近的其他覆盖与差异 | 判定 |
| --- | --- | --- |
| 实际 QualityCase 首次 spawn 被捕获一次，第二次 `start_host` 又捕获一次 | T-152 `ReviewBoundary.start_host` 是覆盖方法，启动 `t152_review_host.ts`；cards bootstrap 拦截的是 `DaemonCards → daemon_acceptance_host.ts` | **唯一直接守护者**：另外两条路径不执行共享 `QualityCase.start_host`。 |
| 外来 `A2A_OPERATOR_CREDENTIAL` 被替换为 fixture 内 `operator-01` 与 `operator-02`；不复用两代路径 | `test_t078_cards_host_bootstrap.py / actual-card-host-bootstrap-0/1` 检查其他 case 的两个 fixture；T-152 本身保存 owned path，但用覆盖方法 | **唯一直接守护者**：其他 fixture 或覆盖方法不能证明共享方法本身的两代命名/绑定。 |
| 实际 `quality_chain_host.ts` 在 serve 前创建可读 operator 凭据 | cards bootstrap 直接调用生产 credential API，没有加载这个 host；T-152 加载另一个 host | **唯一直接守护者**：删除该 host 的 `createOperatorCredential(root)` 会使本检查失败，其他两个入口仍不触达此文件。此为静态反例分析，本轮未注入变异。 |
| 两代 observed kind=operator，state=本 fixture 的 resolved state，mode 恰为 0600 | cards bootstrap 同名检查验证其他路径；`test_t126_desktop_credentials.ts / current_credential_moved_private` 验证 desktop 迁移，不验证 quality host；T-152 cleanup 检查已存在凭据的 state 与无 group/other 权限 | 生产 credential API 有部分覆盖，**实际 quality host 的创建调用与精确结果仍仅本文件直接检查**。不能把 API 测试等同 host 已调用 API。 |
| spawn 环境没有继承 `A2A_LAUNCH` | cards bootstrap 的 `inherited_launch_present` 检查另一子类；两者继承 `TaskCardsCLI.setUp` 的过滤；T-152 正常运行无外来身份注入 | 共享过滤有部分覆盖；本文件直接验证 QualityCase 实际 spawn 的 foreign identity 注入结果。与前述两代检查一起保留，不扩大称为所有 A2A 环境变量过滤矩阵。 |
| `capabilities-removed-before-archive`：调用真实 `QualityCase.close_fixture` 后无 operator-*.credential.json | T-152 有自己的 `close_fixture` 覆盖方法；cards bootstrap 手动 unlink | **唯一直接守护者**：相近清理实现不是同一个执行路径。此处只证明 probe 两代凭据被移除，不证明 live host 故障清理。 |
| `failed-run-copies-host-stderr`：以模拟失败结果调用旧 runner，复制后的 stderr 精确为 sentinel | T-152 保留原始 stdout/stderr 和 fixture，不执行旧 `run_case` 的诊断复制 | 旧 runner 自有协议，退役 runner 时可一并决定删除；目前它也是保留 bootstrap 对旧 runner 的直接依赖。该检查不是实际 host 启动失败的端到端证明。 |

## 处置与边界

`git grep` 在当前 `workbench/`、`scripts/`、`acceptance/` 中只找到 bootstrap 对 `run_t082_boundary` 的 Python 导入；未找到其他程序对 bootstrap 的导入。完整历史 evidence 中的命令记录不能当作当前调用者。

按卡第 3 项，含唯一守护者的 bootstrap 不删、不改，停止删除并上报。旧 runner 的业务检查本身可退役，但本卡禁止迁移；抽出 `run_case` 或改 bootstrap import 都需要新授权，不能在此票顺手做。两份文件和 HISTORICAL.md 均用 `git diff --exit-code HEAD -- <三路径>` 核对未变；实际 import 结果见 `local-checks-01.json`。没有删除，删除后回归不适用。

**Tracer bullet**：正常 tracer 的真实 CLI→daemon→门禁→Git/SQLite 链本轮经过，PTY/原生输入受控。**Deep modules**：不为删除一个文件新增诊断包装或平行 runner。**Ubiquitous language**：沿用“审查副本”“operator 凭据”“结束核对”，不把测试 host 的凭据隔离称为生产沙箱验收。

主控最小决定：保留此唯一守护者；或者明确裁定连同共享历史 host 的这部分检查退役后再删两文件；若要求迁移，应另行授权修改 bootstrap/辅助文件。当前不替构思主控选择。
