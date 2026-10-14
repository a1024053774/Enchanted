# T-077：两项修复与 final-02 沙箱外阶段

准备 **READY**；静态检查 **PASS**；新的完整业务结果 **INCOMPLETE，尚未运行**。真实模型新增 0 回合，没有启动独立审查，没有请求提权。

## 诊断与独立提交

| 项目 | 结论与证据 | 提交 |
| --- | --- | --- |
| 原 run 清理例 ERROR | 夹具把 reviewing/null 当作不匹配；原 status 的 C/attempt 一直相同，后续 review_requested/started 的绑定也正确。仅在原有 12 秒期限内等待尚未建立的记录，保留错误绑定、审查变化、未知状态和缺事实的拒绝。局部测试修前红 1/0，修后 5/0/0。 | `7b3463c4a55381d0fb97f782e69cc0029522f6da` |
| reviewer worktree | 按 attempt 的已存审查意图递增为 `<project>/<task>-a<N>-review-<K>`；有效结论入库且 reviewer 停止、归档确认后，核对身份、HEAD、干净状态再删除并读回目录和 Git 登记。清理事件单独追加，review_result 对象不改写；脏、未知及退出未确认沿用原暂停/上报语义。 | `5d0bf1e84c02fbcb4b7699cdd9a48c4f6582c6b4` |

原 run 的只读诊断为 `DIAGNOSIS-rebase-final-01.md`，原失败仍在 final-01，未改成 PASS。第二个提交也纳入了此前未提交的夹具迁移、三条 joint 测试、变基留档、主控交回的 `.out` 与 final-01 原始结果；没有重新纳入已归档的 r2/r3 原始目录。两次提交各有九项唯一尾注，读回为 `rebase-final-02-commits.json`。

审查清理的先红证据为 `review-lifecycle-recorded-red-01/run.json`：final-01 原受控真实入口现场已有唯一 review_result/review_reclaimed，独立读回仍存在目录和 Git worktree 登记，1 failure、0 errors。该探针只读原场景，不冒称新开过入口；final-02 将另用修前提交的产品源码在新夹具中取得新的真实 CLI 反例，再跑候选。

## 执行命令与输出

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-sandbox.sh rebase-final-02
```

总报告：`outside-rebase-final-02/run.json`。同名目录不得存在；不覆盖 final-01。候选固定为 `5d0bf1e84c02fbcb4b7699cdd9a48c4f6582c6b4`。每阶段前后核对 HEAD 和准备归档中的原始字节，不要求 main 引用不变。

共 39 个子阶段，保留 final-01 的全部 33 个阶段，并增加以下六个阶段：

1. driver readiness 五项局部检查（只是 fixture client 证明）。
2. 在 `7b3463c4` 的修前产品副本上，四条新入口反例分别命中 `REVIEW-DIRECTORY-REMOVED`、`REVIEW-S3-NAMES`、`REVIEW-DIRTY-PRESERVED`、`REVIEW-UNKNOWN-HEAD-PRESERVED`，不得有 harness/cleanup errors。
3. 候选上的四项 reviewer worktree 正反例：存库后删除及事件顺序、同 attempt 两次审查的序号、脏目录保留上报、干净但 HEAD 改变的未知现场保留上报。正常两例最后均经合法审查绑定和显式评分实际集成。

之后仍完整运行三条 joint 变体红态、七条冲突红态、joint 候选三例、S3 25、8/9/18、CAS、cards；relay 全部回归与全库去重变体；controlled-trailer-proofs 候选两例；T-076-2 tracer/wide/reviewer 故障/协议控制/来源冻结入口；身份、停机、原生记录、dispatch-state 和 panes。不会借 final-01 已通过的 24 项跳过新候选重跑。

修前副本由已提交的 Git 对象重建，测试只控制 PTY、进程/原生事实和明确外部动作；真实 CLI/socket/daemon/relay/gates/Git/SQLite 不替换。结果记录完整命令和原始输出。临时变体源码不提交；归档只含原候选与精确配方。单文件超过 5 MB 时停止交主控归档；任何非预期失败立即停止，没有自动修复或兜底重试。

## 已做的准备检查与边界

`rebase-final-02-preparation-01/` 保存冻结源码/夹具、计划和静态核对。产品和全部验收文件与提交一致；核心审查绑定、同 C 复用分支、质量证据、冲突/R8、原生身份和 CAS 方法保持既有实现；旧 T-076 tracer/wide 原文未改。Node/模块导入、Python AST、变体目标唯一性及语法通过，地图 Problems 0、Stale 0，无超 5 MB 文件。

全局 diff 空白检查会指出原始 unresolved 变基快照的冲突标记和 Git stdout 末尾空行；这些是原始证据，不规范化以消掉检查。产品、测试、README 的 scoped 检查通过，记录为 `commit-review-worktree-checks.json`。

RESULTS 已记录当前 INCOMPLETE。issue 的实现已并入本卡，是否关闭仍由主控处置。full final-02 的绿态、fresh-context 独立审查、最终主控验收均未冒称完成。
