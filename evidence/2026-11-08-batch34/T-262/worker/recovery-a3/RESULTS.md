# T-262 attempt 3 恢复交付记录（2026-11-09）

恢复与文本补证归档 PASS；T-262 整体 INCOMPLETE。本轮按主控 #125 恢复原产品，未重新实现页面、修改业务预期或重跑 Electron、ps、构建。原完成条件和本次 merge candidate 的独立补证复核仍由执行主控安排。

**Works**：三个产品／测试文件、54 份旧 worker 文件已从 C 原字节恢复；三个文件同时与 green04 快照一致。新增 60 份小型文本副本（530,422 字节），保留父版业务红态、候选绿态、两组变异结果、原审查 Git 启动失败和两阶段键盘记录。逐项来源、字节数与比对结果见 [provenance.json](provenance.json)。

**No regression**：本轮产品和测试与 C 无字节差异，未写卡外路径、冻结验收文件、其他任务或额外目录。历史候选两次真实后台／Electron 完整场景均为 38 项 PASS，包含原文、人工介入、完整回执、刷新、跨项目及迟到响应、错误恢复、空态和窄窗；这些是 C 的外部执行证据，本轮没有运行完成条件或全仓测试。

**Risk / undo**：恢复候选还需完成本次门禁验收与唯一一次限定补证复核，不能提前称为可集成。原点击／方向键展开菜单的操作仍未证实；typeahead、Tab、Enter 路径有补证。需要撤回时，由执行主控通过正常门禁拒收或另派回退；保留 C 与旧失败记录。未 push，额外可写目录为 []，额外目录改动为 []。

## 本次身份与恢复边界

| 字段 | 值 |
| --- | --- |
| task | `a2a+T-262-1` |
| attempt | `23cd9c84-73af-473d-bce9-50124ad48243` |
| session | `c3a100a6-1bd4-489d-aa74-55583a7d997e` |
| fence / spec_rev | `3` / `3` |
| base | `80a6304225cdd567737362dd045dabf97a625c56` |
| B（共同祖先） | `3647a07bdacb514cdc303965be8c52b84d9356b2` |
| C（恢复源） | `6e92ec6f0d0b59423f5f1bcb85cc39174da70bf5` |

开始时 HEAD 等于任务卡 base，工作区干净；base 相对 B 的 `workbench/app/RecordsPage.tsx`、`workbench/app/records.css`、`workbench/tests/test_t262_records_e2e.py` 无变化。恢复只读取 `git show C:<path>` 的原始字节，不计算哈希；旧 `worker/RESULTS.md` 和全部旧证据未改写，本文件是本次收尾入口。新提交完整版本由 Git 提交与本次 submit 请求绑定，提交尾注由钩子生成。

调用链已核对：`renderer.tsx` 按所选项目挂载 RecordsPage；页面通过 preload 的 `records` / `receipts`，进入 main 的 `a2a:records` / `a2a:receipts`，再由后台 `user_input_records` / `relay_receipts` 读取原始记录。本轮只恢复页面、其 CSS 与原 E2E，未修改上述调用者或后台。

## 补证来源与可核对事实

原始证据根目录为 `/Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-262/`。下表链接指向本目录的原字节副本；每个副本对应的绝对原路径在 provenance 中列明。截图未复制，准确原路径也列在 provenance 中。

| 证据 | 实际结果与归属 |
| --- | --- |
| [controller/behavior-results-08.json](sources/controller/behavior-results-08.json) 及同目录八份原报告 | 执行主控外部运行：父版 `red-outside-05` 在倒序与双区任务筛选上出现业务红态；`green-outside-04` 38 项 PASS；原四个 mutant 均有对应业务失败。`green-outside-02` 的 INCOMPLETE 与 `green-outside-03` 的 FAIL 原样保留。 |
| [review-01/mutation-results.json](sources/review-01/mutation-results.json)、各 `.stdout` / `.stderr` 和四份 `.diff` | 独立审查员 `4900e31c-18a1-4e29-b460-b064605abcd3` 构造补丁；其副本缺 `.git`，五次执行在 Git 入口退出，没有到达业务断言。仍为 INCOMPLETE，不能算变异被业务检出。 |
| [review-01/external-01/summary.json](sources/review-01/external-01/summary.json) 及五份原 JSON | **独立审查员构造，主控外部执行**。主控在 C checkout 原样应用四个补丁，正确候选 38 项 PASS／退出 0，四个错误实现均 FAIL／退出 1，并命中各自业务断言。源码恢复与清理有记录。 |
| [controller-test/KEYBOARD-COMPLETION.md](sources/controller-test/KEYBOARD-COMPLETION.md) 与四份 `keyboard-*.txt` | 主控在已打包 C 的真实 Test 窗口用原生 typeahead 选 T-1（输入 4／回执 3），Tab 选 worker-one（3／3），再选 T-3（0／1），Tab、Enter 展开含 `r-only` 的完整 JSON。 |
| [controller-test/CUA-RESULTS.md](sources/controller-test/CUA-RESULTS.md) | 初次点击、Space、方向键未观察到选择变化，保留原 INCOMPLETE；后续键盘补证没有把这个历史结果改成 PASS。 |
| [controller-test/source-binding.json](sources/controller-test/source-binding.json)、[package-command.json](sources/controller-test/package-command.json) | 打包源绑定 C；本轮另直接比对 C、green04 三文件快照、恢复文件及审查员源码备份，均一致。这证明产品字节相同，不替代新 base 上的门禁验收。 |

外部四个错误实现的独立预期分别为：取消排序 →「每区最新在前，同时间按记录身份稳定排列」；忽略回执任务 →「任务筛选同时约束双区」；忽略会话 →「同一 launch 的输入与回执一起筛选」；替换完整回执 →「完整回执与原始存储一致」。每份外部原 JSON 的 `failed` 都包含相应名称，属于业务失败。复现命令和工作目录保留在 [run_external_mutations.py](sources/review-01/run_external_mutations.py) 及 summary；本轮没有执行该脚本。

[首审恢复记录](sources/review-01/RESULTS.md) 与额度前草稿一并保存。草稿不是正式 verdict；原 review 已 cancelled，未据此宣称通过。状态滞留问题另属 T-264，本轮没有扩大处理。

## 本轮核对与交接

只读复核命令（从本 worktree 根目录运行）为：

```sh
python3 evidence/2026-11-08-batch34/T-262/worker/recovery-a3/verify_bytes.py
git diff --check
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
```

恢复比对结果存入 `byte-check.json`，结束前 project-map 输出存入 `project-map-before-commit.txt`。检查目标是确认恢复字节、证据来源、路径边界和地图状态；业务完成条件仍是原命令 `/usr/bin/python3 workbench/tests/test_t262_records_e2e.py`，本轮遵照任务卡不运行。

实际结果：逐字节与路径核对退出 0，产品 diff 检查退出 0；新增文本以 UTF-8 回读，无 BOM 或替换字符。project-map 开始时 Problems 0 / Stale 0；恢复后 Problems 0 / Stale 1，退出 1，指向 `workbench/README.md` 的页面覆盖范围。此提示与 C 的旧 worker 收尾记录相同，需由执行主控在集成时同步 README 与地图；两者都不在本卡写入范围，按本次指示不重复 issue 等待，也不把地图状态写成 PASS。

首次 `git add` 因证据目录不在 Git sparse-checkout 列表内而退出 1，原提示摘要保留于 [git-add-01.json](git-add-01.json)。按 Git 提示，对相同四个卡内路径独立执行 `git add --sparse` 后退出 0，未改稀疏列表或权限配置。暂存区字节、来源、路径和产品／自写文本的 diff 检查见 [precommit.json](precommit.json)；历史证据的空白保持原字节。

执行主控下一步在本次 merge candidate 上运行原完成条件，并新开只读的限定补证复核；外部执行与审查判断分别署明归属。worker 提交后按本 attempt/session/fence 显式 submit 一次，排队回执只代表请求存在，不代表验收或集成通过。请求文件留在本 attempt 请求目录，不进入 Git。
