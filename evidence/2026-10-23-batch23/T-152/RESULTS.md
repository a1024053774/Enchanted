# T-152-1 / a1 交付记录

状态：**INCOMPLETE**。测试迁移候选已完成；沙箱外红态、绿态和回归尚未运行，不能据此验收或集成。产品代码未改。起点 `32ffb4e6dcc0472b20bbb64331a355621c9b73a9`，分支 `exec/t152`，worker `b23-t152`。

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

提交后运行：`zsh evidence/2026-10-23-batch23/T-152/RUN-OUTSIDE-01.sh`。

它先运行四个有效检查变异，再运行四个非法启动变异，最后跑全部正常案例、T-090 直接继承方的 HEAD/branch/dirty 三例和既有 T-141 双 CLI reviewer 启动契约。摘要写入新的 `outside-01-XXXXXXXX/`，聚合 `SUMMARY.json`。结束核对、workspace、refs、假删除副本分别必须命中 `REVIEW-END-BEFORE-INTEGRATE`、`REVIEW-REQUIREMENTS-WORKSPACE`、`REVIEW-REFS-INVALIDATE`、`T082-COPY-REMOVED`；启动反例必须让三条拒收/暂停/上报断言全过。

局限：当前没有有效业务红态、绿态或 T-090/T-141 新回归通过证据；不声称真实原生 CLI 沙箱、网络访问或模型判断得到证明（原生 CLI/模型回合为 0）。不复用历史 PASS。最终验收、独立审查、submit/集成由执行主控门禁负责。
