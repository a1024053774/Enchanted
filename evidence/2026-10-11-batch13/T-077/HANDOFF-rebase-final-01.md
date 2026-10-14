# T-077：冻结候选的合流复验阶段

准备状态 **READY**，静态检查 **PASS**；本轮业务红/绿 **INCOMPLETE，尚未运行**。固定产品与验收代码为 `c3eb705cd8b8c949850c8483c861ddb9d7f87b89`，基于主控所述 main `5e057109`；脚本不要求 main 引用保持不变。没有修改产品源码、hook 或 `acceptance/test_*.py`，没有启动真实模型、后台或独立审查。

执行命令：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-sandbox.sh rebase-final-01
```

总报告为 `outside-rebase-final-01/run.json`；该目录尚不存在，脚本拒绝覆盖同名输出。每个子阶段保存命令、原始 stdout/stderr、结果和临时仓库读回；质量场景另存库、Git 引用和 worktree 清单。单个证据文件超过 5 MB 时停止交主控归档，不自动搬运或删原失败；任何预期之外的退出、夹具错误、协议错误或产品失败都停止，不兜底重试。

## 三条新增组合路径及反事实

由 `workbench/tests/test_s3_quality_joint_e2e.py` 经真实 CLI/socket/daemon/Panes/relay/gates/Git 驱动。只控制 PTY、进程与原生日志输入；worker 的整理、reviewer 的 JSON 结论和执行主控打分均由夹具作为明确外部动作给出，没有直接写门禁状态或塞入通过结果。预期来自 T-077 Acceptance、R8 与 spec 第 3/4/8 节。

| 路径 | 候选必须提供的读回 | 先运行的隔离变体及失败点 |
| --- | --- | --- |
| 同 C 的 R8 沿用有效审查 | G 改变后生成新 verification/M；path、completion、rule 均在新 verification 上重跑；只创建一份审查结论，有绑定新 verification 的 review_reused；实际 Git 到新 M。 | 禁用同 C 的审查复用分支；必须在 `JOINT-SAME-C-REUSE` 失败。 |
| 新 C 重新审查 | C1 先获有效审查；新 G 使新的 M 不满足独立完成条件；原 worker 合法提交 C2；须产生不同 review/session/launch/native，C2 审查通过后才能集成。 | 已有通过审查时跳过新审查；必须在 `JOINT-NEW-C-REVIEW` 失败。 |
| 冲突重交后质量打回再提交 | 真正同一行冲突 → 原 worker 整理 C2 → 完成条件拒收 C2 → 同 attempt/fence/native 显式提交 C3 → 重跑机械检查、审查并集成；保留门禁已记录的 G 与 host 内容。 | 去掉质量修复对既有 rework 基线的续提授权；必须在 `JOINT-CONFLICT-QUALITY-SUBMIT` 失败。 |

三个变体仅存在新建的 /tmp 隔离副本，先运行变体、核对明确的 ContractFailure 与零 cleanup failures，再运行候选三例。变体语法错误、字段缺失或其他 HarnessFailure 都不算红态。提交证据只保存原候选源码和精确变异配方，不提交变体源码。

## 本阶段的全部检查

按以下顺序共 33 个子阶段运行：

1. 三条组合路径各自的已知坏变体；原七条冲突场景的受控红态（省略冲突写回与错误合并分类使用不同变体）。
2. 候选三条组合路径；worktree 生命周期 e2e 全量 25 项，包含七条冲突绿态。
3. 原 8/9/18，CAS 1，cards 15。
4. relay 冲突闭环；controlled-trailer-proofs 候选两例（额外尾注拒收、生产 Git hook 生成九项尾注后实际集成）。不重跑已留档的尾注数量变体。
5. identity 4、shutdown 4；T-076-2 最终入口：tracer 13、wide 15、reviewer 故障 3、协议控制 8，以及来源/候选冻结 2。
6. relay core、cli、scope 与全库 request_id 去重变体；native-final、dispatch-state；pane 生命周期 4 项。

`run_s3_rebased_regression.py` 保留原测试方法身份和固定套件成员数量，并将全部验收文件逐字核对到冻结 c3eb705c。原 S3 auditor 的坐标属于 T-076-2 之前的源版本，不能把 main 已批准的质量串变更判为本卡越界；旧 auditor 没有修改，旧证据仍可原样重放。没有通过 adapter 覆盖验收测试方法。

## 合流夹具的必要适配

- `controlled_quality_pty.ts` 只补真实 rollout 已证实具有的 `session_meta.cwd`；pane 单元夹具补 role 和每 pane 的 CODEX_HOME。
- T-076 的 `relay_result` helper 按 launch/request_id 读取真实请求记录关联的结果，不再猜全局 `id:<request_id>`；其全部业务 check/assert AST 不变，tracer/wide 原文不变。
- relay scope 的受控 binding 补 main 要求的 `role=worker`，请求 payload 仍不含 role，所有业务断言保持原样；此项由 relay.ts:71 的字段核对发现，未将夹具缺字段当作业务红态。
- 旧冲突 host 接入 main 的受控 reviewer runtime，补受控 worker 的 sessionFacts/qualityFeedback；relay/trailer host 提供独立 reviewer home、准确的 turn_context 和显式 reviewer/executor 动作。
- 集成测试经受管 dispatch 提供来源与分数；保留手工 claim 的来源拒收反例。run 正例由显式执行主控完成审查/打分；首次质量打回仍保留 worker，S3 的打回清理例先显式回收已 idle 的原 attempt，才核对结束后的目录和隐藏引用。

以上只改 `workbench/tests/` 与本卡证据。没有改 T-076 的业务期望；没有放宽身份、路径、尾注、审查或 CAS 的产品检查。

## 冻结与现有证据

当前可执行准备版本为 `rebase-final-preparation-03/plan.json`、`frozen-source-and-harness.tar.gz` 和 `static-checks.json`。准备版本 01/02 保留原样；版本 02 增补 T-076 的来源拒收/候选冻结入口，版本 03 补全 relay scope 的 role 元数据，未运行或覆盖任何旧业务结果。

已完成四类静态核对：语法与冻结输入；五个变体的目标各唯一且修改后可被 Node 解析；T-076 业务 check/assert 与冻结版一致；全部验收文件与冻结 HEAD 逐字一致。运行前后及各子阶段之间直接比较源码字节，不使用哈希。原始 rebase 控制台输出（包括主控交回的 `rebase-continue-05.out`、`rebase-main-02-controller.out`）留在本卡证据中，待下一次提交纳入；本轮没有执行 Git 写操作。

源码核对另发现 reviewer worktree 的命名/结束清理尚未接入，已按角色卡非阻塞上报 `20261014T023857Z-worker:s13-t077s-issue-001`，正文为 `ISSUE-review-worktree-handoff.md`。这部分在已批准 PLAN 中交由 T-076-2 接入；冻结代码仍保留 main 方法，本阶段不偷偷修产品，也不把 pane 回收算作 worktree 清理证明。即使上述受控阶段通过，完整 ticket 结论仍须说明此项处置。

真实模型回合新增 **0**。独立审查仍待主控读回本阶段后明确启动，本轮没有 spawn reviewer。
