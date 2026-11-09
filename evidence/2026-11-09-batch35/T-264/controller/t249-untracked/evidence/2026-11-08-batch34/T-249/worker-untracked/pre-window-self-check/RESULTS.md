# T-249 未跟踪文件 diff 限定修复

INCOMPLETE。未跟踪内容读取已实现，宿主红绿和三项机械条件通过；真实 Electron 内容、列宽及迟到返回检查已备好，等待主控按 HANDOFF.md 在沙箱外执行。最终独立审查、新 Test 包与 Terra Computer Use 属于主控后续步骤，不能引用旧候选通过结论代替。

## 改动与恢复

- 主控 #110 更正：准确 B 是 C 的唯一父提交 `05002a377914d52372a4cd46a08fa40229d70e1f`，C=`18c108fcaed1c4ecf51831f2272578a3b09427be`；此前给出的 `c89b8ca4739f2a4106feeda8665f4e1aa8cec688` 是任务创建基线。已把准确 B→C 的完整 binary diff 应用到基于当前 attempt base 的临时文件快照，核对全部 15 个 workbench 文件和 135 份证据；145 份与当前文件字节相同，剩余五份恰是卡允许的限定修复。没有额外主线改动被覆盖，无需修改源码。详见 corrected-baseline-verification.json。原 recovery.json 和合并冲突输出保留为最初错误基线下的操作记录，不再作为准确 B 的依据。
- 最初使用错误 B 时，README 的三方合并在已经集成的后台说明处冲突，原始输出留在 readme-merge-conflict.txt，并经 issue 上报。最终只恢复 C 的 T-249 小节，保留当前 T-258/T-259 等后台说明；准确 B→C 完整补丁的期望与此结果相同，且重新应用没有冲突。没有恢复 C 的其他票后台、地图或治理变更。
- 本次新产品改动只有 gitHost.ts、GitGraphPanel.tsx、gitGraphModel.ts；开发测试改动只有 test_t249_git_graph_e2e.py 与 test_t249_git_host.mjs。scoped-repair.patch 是相对 C 的限定快照；scope-check.json 记录其余恢复文件字节一致及冻结文件未改。
- gitRead 接受一组精确的 no-index 参数，以 /dev/null 对比仓库内普通文件；拒绝目录、越界、符号链接、Git 元数据、额外参数和输出选项。没有暂存文件、写索引/refs/对象库，没有新接口或依赖。
- 详情复用 diffRows，空文件显示说明，二进制保留 Git 提示。加载结果只更新发起它的加载状态，关闭或更换选择后迟到结果作废。

Git 官方文档说明 no-index 隐含 exit-code，文件不同返回 1；本机 Git 2.52.0 的独立探针确认文本、空文件及二进制行为，记录见 no-index-git-probe.json。[Git 文档](https://git-scm.com/docs/git-diff)。首轮测试错误地期待空文件输出为空，实际 Git 给出新文件头部；原失败保留 host-green-01.txt，修正后按独立 Git 输出核对。

## Worker 已运行的证据

执行入口：

```sh
python3 evidence/2026-11-08-batch34/T-249/worker-untracked/run_local.py --output evidence/2026-11-08-batch34/T-249/worker-untracked/local-01 --tmp-root /private/tmp/a2a-requests-3IGepO
```

- 实现前红态 host-red-C.txt：有 HEAD 与 unborn 两项均明确失败在 `untracked content missing`，不是启动/导入失败。
- local-01/host.txt：27 个真实 Git 宿主场景通过，包含随机原始文本、字面特殊文件名、同目录哨兵、空文件和二进制；真实 linked worktree 的 git-dir/common-dir 路径与原始字节前后相等。
- local-01/acceptance.txt：冻结机械验收退出 0；local-01/outside-safety.txt：6 个脚本安全检查通过。
- local-01/old-C.txt、empty-binary-C.txt：新测试拒绝旧 C 的未跟踪内容与空/二进制路径。
- unsafe-options、unsafe-paths、force-text 三个定向变异各退出 1，命中缺失拒绝或伪造文本 hunk 的断言。具体变异与命令留在同目录，未改生产树。
- 所有本地夹具已清理，体量与删除状态在 local-01/summary.json；无 checksum 比较。未启动 Electron、后台、模型 CLI，未调用 ps。

## 主控 #113：驱动路径核对

PASS（不启动应用的预检）。当前 run_windows.py 的 ROOT 已是 `parents[4]`。新增 `--preflight` 在任何输出目录创建、依赖复制和临时夹具创建前检查：ROOT 为任务 worktree，模块目录不是链接，输出目录全新。实跑 ROOT 精确为 T-249-1-a6；模块目录当前不存在，预检没有创建 external-01。将定位改回 `parents[5]` 的变异被“ROOT 不是本任务 worktree”断言拒绝，未触及应用或任何复制/清理。记录为 driver-preflight-01.json，重放探针为 preflight-parent-mutant.py。业务断言、产品权限和产品源码未变。

## 尚待主控执行

HANDOFF.md 和 run_windows.py 已一次集中提供旧 C、完整候选、列宽/内容/迟到结果变异、原窗口回归的精确命令与持久输出目录。external-01 尚不存在；没有 root 实跑结果可引用，列宽交互、真实窗口内容及新窗口测试的有效性目前均为 INCOMPLETE。

design-integrity-review.md 为限定结构自查 PASS；behavioral-acceptance-review.md 为 INCOMPLETE，明确缺少真实窗口证据。两份都是 worker 自查，不冒充干净会话的独立审查。任务身份见 run-context.json。额外可写目录为 []，无额外目录改动；请求目录只放门禁请求和可清理临时文件，不进 Git。

**Works**：宿主的旧 C 内容红态及同一检查的新实现绿态，证明限定读取路径已有修复；窗口闭环尚缺主控实跑。

**No regression**：三条机械条件通过；旧窗口场景的重跑命令已保留，当前不宣称窗口无回归。

**Risk / undo**：等待沙箱外窗口与变异证据及新的独立验收。源码回退以 scoped-repair.patch 的三个产品文件为限定边界，或撤回本 attempt；保留原 C、原失败与当前后台，不重置共享引用。
