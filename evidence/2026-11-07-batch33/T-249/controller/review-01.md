# T-249-1 审查 01（2026-11-08，执行主控整理）

- 任务 `a2a+T-249-1`，attempt `6bab2eb9-0d63-4bb1-b325-f70fa6df2d2b`，候选 `0c3da7adedf5a2c0a61af32cf3d1bb2bb39b6083`，基线 `dc51588832c705aaee0463fb1b96b5586e4c91b7`。
- 审查员启动记录 `60d51e63-8e38-40e9-be26-bec893fb5505`：`gpt-6.1-sol` high。不是用户要的 `gpt-6-astra` xhigh（T-256）。
- 结论：需修复。这一轮的模型不符，它的结论不算通过依据；发现仍按缺陷处理。
- 门禁随后转入 `paused`（`review_shared_refs_changed`）。原因是执行主控在审查进行中向 main 提交了 `d67c4ae63`，审查员的结论已入库，只有回收后的清理被拦。审查副本与审查 worktree 留着，没有手动删（142M、141M）。

## 发现（原文）

```json
[
 {
  "location": {
   "path": "acceptance/T-249/check_git_graph.py",
   "line": 70
  },
  "failure_scenario": "[P1] 唯一完成条件只执行 CLI。独立把 renderer.tsx 的 PanelDock 挂载条件改成 false 后，冻结验收仍 exit=0、PASS，补充宿主测试也 8/8；删除受管写保护或 HEAD 虚线终点时冻结验收也仍通过。当前完成条件不能拒绝核心面板完全不存在等明显错误实现。",
  "suggestion": "由主控补充必经验收编排：运行已有宿主检查与真实 Electron 用户旅程，并要求断开面板挂载的变异失败；补全受管写保护和未提交虚线终点的必经证据。冻结 oracle 如需修改，应先按规则取得授权，worker 不应自行改需求。"
 },
 {
  "location": {
   "path": "workbench/app/panels/gitGraphModel.ts",
   "line": 464
  },
  "failure_scenario": "[P2] 选中的文件名含 Git pathspec 字符时，单文件 diff 会混入其他文件。真实夹具中同时修改 file*.txt、file-other.txt，候选 diffArgs/gitRead 对 file*.txt 的结果包含 +OTHER-FILE-SENTINEL；独立 git --literal-pathspecs 的期望只包含选中文件。根提交 show、普通提交及未提交 diff 都直接传入原始 path。",
  "suggestion": "在共用单文件命令层使用 literal pathspec，覆盖三种 diff 路径；增加带通配符或 pathspec magic 的真实文件名反例，明确断言不包含第二个文件的内容。"
 },
 {
  "location": {
   "path": "workbench/app/panels/gitGraphModel.ts",
   "line": 438
  },
  "failure_scenario": "[P2] 首次提交前暂存 first.txt 后，图正确显示 1 个未提交文件，但 fileArgs 无条件以 HEAD 比较；真实 gitRead 的 status 和 numstat 均退出 128、报 HEAD 不存在，CommitDetails 因此无法列出文件。diffArgs 的未提交路径也同样依赖 HEAD。现有 unborn 测试只验证空历史，未覆盖详情。",
  "suggestion": "根据 HEAD 是否存在选择正确的文件列表和 diff 基线，保留 staged/unstaged/untracked 文件；通过真实 Git 增加首次提交前的详情与 diff 覆盖，避免用吞错或空列表掩盖问题。"
 }
]
```

## 主控复现（真实 git，期望值来自 git）

P2 通配符文件名：argv ["diff","--no-color","--no-ext-diff","--no-textconv","5bc405f352d321145a67633b47b581051ef5cbb3","0f7335f4c97760bf9ca6c2d1f4b157577c714826","--","file*.txt"]
  候选 diff 含另一个文件的内容: true ; git --literal-pathspecs 含: false
P2 首次提交前：status 退出 128 "fatal: ambiguous argument 'HEAD': unknown revision or path not in the working tree."
  numstat 退出 128 ; git ls-files: "first.txt"


第 1 条（完成条件拒绝不了“面板没挂载”）：`check_git_graph.py` 只跑无界面入口，读脚本即可确认；审查员的变异结果见下。

## 审查员的完成条件与变异检查（原文）

完成条件不足以拒绝明显错误实现，不能单凭机械 PASS 合并。独立构造了以下 5 个少量错误实现，均只改 .review-t249/<名字>/ 中复制的产品文件，复制的验收与测试保持原样。统一重放入口为 python3 .review-t249/mutations.py；每个变异分别在其目录运行 /usr/bin/python3 acceptance/T-249/check_git_graph.py 与 node --test workbench/tests/test_t249_git_host.mjs，TMPDIR 指向该变异自己的 tmp。各目录保存 acceptance.txt、host.txt、mutation.json，汇总在 .review-t249/mutation-summary.json。
1. parents：把 parseLog 的 parents.split(' ') 改为 parents.split(' ').reverse()。完成条件 exit=1，明确失败于 all/current 父提交及泳道断言，共 4 项；宿主测试 exit=0。此变异被完成条件正确拒绝。
2. merge-edge：删除 layoutLanes 中 segments.push([lane, 0.5, k, 1, k, dashed[k]!])，保留其他逻辑。完成条件 exit=1，仅 merge 第二父连线断言失败；宿主测试 exit=0。此变异被完成条件正确拒绝。
3. managed-write：把 gitHost.ts 的 if (repo.managed) 拒绝条件改为 if (false)。完成条件 exit=0、PASS；宿主测试 exit=1，命中 managed write action is rejected without metadata changes。说明现有补充测试能检出宿主保护丢失，但任务卡唯一完成条件没有运行它。
4. no-panel：把 renderer.tsx 的 {dockOpen && <PanelDock 改为 {false && <PanelDock，界面永远不挂载面板。完成条件 exit=0、PASS，宿主测试也 exit=0、8/8。这个明显违反核心目标的实现仍能通过全部现有无界面业务检查，必须有真实界面入口的必经验收来拒绝。
5. no-dashed-head：删除 uncommittedRow 中 extra[headRow]!.push([lane, 0, headLane!, 0.5, lane, true])，使虚线不能接到 HEAD 圆点。完成条件 exit=0、PASS；宿主测试 exit=1，命中 uncommitted row stays in HEAD lane even beneath another branch 的虚线终点断言。冻结验收仅核对未提交文件数，没有核对连接。
因此并非所有变异都被拒绝：3、4、5 在冻结完成条件中存活，4 在补充宿主测试中也存活。缺失的必经证据包括界面实际挂载与用户旅程、受管写保护及未提交虚线终点。应由主控调整验收编排并运行真实 Electron 正例和针对性反例；本审查没有修改冻结 oracle。

## 审查员留下的未验证项（原文）

按 design-integrity-review 检查异常处理、回退、平行路径与清理所有权：localStorage 回退只影响视图偏好；lsof 失败退回启动目录、watch 失败依靠票要求的轮询，均有明确用途；写动作失败直接报告，没有新增自动重试。未发现另设 CLI 模型或另做门禁。RUN-OUTSIDE 的私有临时根、清理失败保留现场和指定断言判红逻辑已读，并通过其补充安全检查；这不能替代真实打包/清理实跑。
运行 python3 /Users/luckye/.agents/skills/design-integrity-review/scripts/design_integrity.py --cwd "$PWD" --base dc51588832c705aaee0463fb1b96b5586e4c91b7 --format json，虽然退出 0，但返回 root:null；一次性副本没有 Git 元数据，所以其空 findings/acceptance_changes 不作为结构通过证据。结构结论来自提供的差异和源码。
前端只完成源码及真实 Git 边界检查，未获得窗口交互证据。键盘路径仍有待验证：行仅有点击处理，Esc 处理又限制 activeElement 必须位于图内或 body；从终端转向提交详情时可能保留终端焦点，需在真实窗口核对。此项保留为未验证限制，没有当作已复现缺陷。
