# T-077：第一次变基停点已解决，待主控继续

状态：文件冲突解决与静态核对 **PASS**；变基、业务回归与最终交付 **INCOMPLETE**。没有执行 `git add`、`git commit` 或 `git rebase --continue`，没有启动真实模型。

固定停点：`HEAD/main = 7a1ecae84121b4dc43ddf79b595d6ff4917ab6c9`，`REBASE_HEAD = 446f25c3de00925dfcc2f1c3f1375713676e166b`。索引仍保留原五项 unmerged 状态。

| 文件 | 解决方式 |
| --- | --- |
| `acceptance/test_run_e2e.py` | 保留 main 的首次质量打回后 worker 未回收、原 attempt 和一次修复输入的断言。保留 S3 的隐藏引用及清理预期；此处 worker 尚未回收，不预期新增 attempt 清理引用，只预期 verifier 引用。 |
| `workbench/src/contracts/a2aGates.ts` | 同时保留 delivery、repair、review、quality 与 S3 rework、revalidation、cleanup、conflict 字段。 |
| `workbench/src/gates/cli.ts` | 同时解析 main 的 `score-file` 与本卡的 `overlap-reason`。 |
| `workbench/src/gates/core.ts` | 认领统一走带路径锁的 claim，保留 main 的 repair/review 重置和事件 task；速度记录用 default。verifyCandidate 接入 main 的完整质量串，供公开 verify 与 R8 共用；集成每轮都检查质量证据、审查绑定和提交来源，保留原子打分、重放核对及 S3 CAS 安全边界。 |
| `workbench/src/panes.ts` | 保留 main 的审查独立 home、原生身份、质量回写上下文、default argv 与停机逻辑；保留 S3 的结束会话判定、冲突回写、按工作目录归属 rollout 和 worker 名额释放。 |

合流交叉处还作了两项衔接：

1. `createThread` 的名额检查只针对 worker。已停且归档的旧 worker 释放名额；审查 pane 沿用 main 的独立生命周期。
2. 活跃 worker 完成冲突重交后，若质量串打回，新候选继续绑定门禁已记录的 rework 基线；提交时检查候选继承这个基线，再更新候选绑定，重新验收并按 main 的规则审查。没有让 worker 自行指定基线，也没有绕过原来的尾注、路径或身份检查。

这两项组合路径尚未取得变基后业务结果；全部提交重放后，须在 rebase-final-01 中覆盖“同 C 的 R8 重验沿用有效审查”“新 C 重新审查”“冲突重交后质量打回再提交”。旧通过证据不替此候选背书。

静态核对保存于 `rebase-stop-01/preflight.json`：四个 TypeScript 文件的语法、Python AST、模块导入通过；17 个 main 门禁方法、14 个 S3 方法和 10 个 main pane 方法与各自原文逐字一致；createPane 仅多 S3 的 nativeEnded 初始化。地图状态为 Problems 0、Stale 0。核对脚本首版误将 createPane 列为完全不变，原失败保存在 `preflight-01-probe-error.txt`，修正探针后通过，未据此修改产品。

重新生成静态核对：

```sh
cd /Users/luckye/Documents/Code/a2a-wt-t077
python3 evidence/2026-10-11-batch13/T-077/rebase-stop-01/audit-first-stop.py
```

主控在沙箱外执行一次：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/rebase-continue-01.sh
```

脚本先核对固定 HEAD、main、REBASE_HEAD、分支归属、原五项冲突清单、解决文件与留档原文一致且无冲突标记、语法；之后单独 `git add` 五个文件，再执行一次 `GIT_EDITOR=true git rebase --continue`。若后续提交冲突，脚本保留该停点退出，不重试、不跳过、不 abort。

`rebase-stop-01/unresolved/`、`main/`、`t077/` 保留本停点三份输入；`resolved/` 为首版解决稿，`resolved-final/` 为交付主控的当前稿；`resolve-first-stop.py` 记录从输入重建当前稿的确定步骤。没有单个证据文件超过 5 MB。
