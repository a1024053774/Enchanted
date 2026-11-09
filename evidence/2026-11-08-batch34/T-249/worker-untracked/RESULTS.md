# T-249 未跟踪文件 diff：限定修复交付

PASS（本卡 worker 限定修复与检测能力）；整票最终验收仍为 INCOMPLETE。主控真实 Electron 窗口组 12/12 达到预期，本地 8 项结果全部符合预期。候选内容、列宽与迟到返回已有实际证据；主控后续仍须限定独立审查、新 Test 包、Terra Computer Use 与常规测试，再决定集成和安装。

被测产品与开发测试绑定 `5ca17101d350e54582cb301d4f8c9166d63338b5`，与 `a6718ffa5f4ffccb75bb9bcd801c0cb57c280994` 的 workbench 和冻结 T-249 验收完全一致。本轮只归入证据和更新报告，没有修改产品、测试或驱动。入库核对读取了 724 个现存受控输入的原始字节；来源、复制清单与绑定边界见 controller-evidence-import.json。窗口原报告未内嵌提交号，绑定依据是主控 #116、受管会话源码变更记录和当前字节核对，不冒称运行时生成了源码指纹。

## 修复与正确恢复范围

准确 B 是 C 的唯一父提交 `05002a377914d52372a4cd46a08fa40229d70e1f`，C 为 `18c108fcaed1c4ecf51831f2272578a3b09427be`。完整准确 B→C patch 包含 15 个 workbench 文件与 135 份 T-249 证据。以 attempt 原基线应用该完整 patch 后，145 份与当前文件逐字节相同，另五份恰是以下限定修复；执行位与 C 一致。没有通过任务创建基线 c89 的大差异继续推导恢复范围。详见 baseline-correction.md 与 corrected-baseline-verification.json。

- 产品新改动仅 gitHost.ts、GitGraphPanel.tsx、gitGraphModel.ts：未跟踪文件通过现有 gitRead 执行精确 no-index 读取；主进程拒绝多余参数、输出选项、目录、越界路径、符号链接和 Git 元数据。未暂存文件，未写索引、refs 或对象库，未增加依赖或公开 API。
- 详情复用现有 diffRows；空文件给出说明，二进制保留 Git 提示；迟到结果只能更新发起它的加载状态，不能覆盖改选或关闭后的状态。
- 开发测试仅改 test_t249_git_graph_e2e.py 和 test_t249_git_host.mjs；旧占位说明预期已改为原始文件与独立 Git 内容断言。冻结 acceptance、REVIEW.md、AGENTS.md、任务票未改。其余 app 和旧 batch33 证据按 C 恢复；README 只并入 T-249 段落，保留 T-258/T-259 等已集成说明，后台没有回退。

原错误 B 下的操作、README 三方冲突以及首轮错误空文件预期均保留。独立 Git 2.52.0 探针确认：no-index 的文本、空文件和二进制差异退出 1；空文件有新文件头部而没有 hunk。见 no-index-git-probe.json 与 [Git 官方文档](https://git-scm.com/docs/git-diff)。host-green-01.txt 是修正测试预期前的失败记录，不计入最终通过。

## Worker 本地证据

```sh
python3 evidence/2026-11-08-batch34/T-249/worker-untracked/run_local.py --output evidence/2026-11-08-batch34/T-249/worker-untracked/local-01 --tmp-root /private/tmp/a2a-requests-3IGepO
```

local-01/summary.json 记录 8 项：宿主 27 场景、冻结机械验收、脚本安全 6 场景为绿；旧 C 文本、旧 C 空/二进制、unsafe-options、unsafe-paths、force-text 均被对应检查拒绝。实现前 host-red-C.txt 已在有 HEAD 与 unborn 两项取得“untracked content missing”业务红态。随机原始内容、特殊文件名和邻居哨兵不由产品生成；linked worktree 的实际 git-dir/common-dir 路径和原始字节前后相等，没有 checksum 比较。

worker 未启动 Electron、后台或模型 CLI，未调用 ps。本地夹具已经清理，清理体量与状态在 local-01/summary.json。驱动 `--preflight` 与 parents[5] 变异的只读结果见 driver-preflight-01.json；该预检是在窗口组启动后补入，不能冒称实跑 wrapper 已使用它。

## 主控沙箱外窗口证据

原始来源：`/Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-249/controller/untracked-window-01`。本次归入 controller-window-01/ 的 27 份小型文本，共 280,589 字节，逐份与原文比对；未复制夹具、数据库或图片。执行者是主控，worker 只读复核。

实际 wrapper argv（按 summary.json）：

```sh
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 evidence/2026-11-08-batch34/T-249/worker-untracked/run_windows.py --output '/Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-249/controller/untracked-window-01'
```

主控 #116 记录 wrapper exit 0，wrapper.stdout.txt 记录 PASS。每个实际子命令及 Node/Git 版本在各 run.json，原始解释器由 /usr/bin/python3 解析为 Xcode Python；导入时首次误把两者当成同一字符串的核对失败单独留在 import-preflight-initial.json，不当成产品失败。

| 场景 | 实际结果与指定观察 |
| --- | --- |
| candidate | PASS，200 项检查；有 HEAD/unborn 的未跟踪普通文本、特殊文件名、空文件、二进制均符合独立文件/Git oracle；原窗口场景保持 |
| deferred-candidate | PASS，49 项检查；挂起真实读取后关闭或改选，再释放旧结果，当前选择保持 |
| old-C / no-untracked | FAIL，均命中未跟踪文本内容断言；前者仍显示旧占位，后者误显示空文件，均被拒绝 |
| no-resize | FAIL，拖动后仍为 128 px，命中几何断言 |
| no-reset | FAIL，双击后仍为 192 px，命中复原断言 |
| stale-diff | FAIL，关闭后旧 diff 重开，命中迟到内容断言 |
| no-panel / no-details / no-diff | FAIL，分别命中面板、详情、diff 的可见性断言 |
| parents / order | FAIL，分别命中独立 Git 父提交与排序断言 |

正常候选的真实鼠标输入使表头与行的日期列同时由 **128 → 192 → 128 px**；原 C 的列宽也通过，没有据工具 noWindowsAvailable 改列宽实现。deferred 场景是测试副本中的确定性返回顺序探针，真实文件读取保留；candidate 不带该插桩，两者分开记录。

所有 12 项都记录 cleanup PASS、fixture_removed=true、user_core_unchanged=true。组 cleanup.json 记录 31 个残留临时文件、2,780,541 字节，随后自有临时目录与复制依赖均已删除。该 user_core 观察不替代最终验收阶段对正式应用进程的核对。

## 自查、边界与交付

本次经工作台窗口人工续接，原话与续接前 34 项脏文件清单保存在 human-resumption.json。续接仅完成证据核对、报告和提交；没有重跑已有大组或修改产品、测试、驱动。

design-integrity-review.md 与 behavioral-acceptance-review.md 均为本卡限定自查 PASS，窗口前的 INCOMPLETE 报告保留在 pre-window-self-check/。这不是干净只读会话的独立审查，最终门禁审查与 Terra 验收由主控安排。Stop hook 的原候选异常处理逐项核对在 stop-hook-check.md，没有为静默扫描而删处理。

project_map status 的两个 stale 仍是 README/REVIEW 的 Verified 治理状态，指向原脚本恢复及执行位更正；正文已核对，不在本卡擅改冻结文档或地图。此前已上报主控，状态不冒称清零。任务/attempt/session/fence/spec 见 run-context.json；额外可写目录为 []，无额外目录改动。请求目录不进入提交。

**Works**：宿主业务红绿与主控真实窗口内容红绿一致，列宽及迟到返回均有正例和指定反例。

**No regression**：三条机械完成条件和适用旧窗口场景通过；原五项窗口反例继续命中。没有以全套旧通过报告为本次变更背书，也未为证据归入重复测试。

**Risk / undo**：本卡 worker 范围已完成；最终独立审查、新 Test 包与 Terra 验收、治理 Verified 更新、集成安装仍由主控完成。需要撤回时只撤本 attempt 的限定改动，保留原 C、失败证据和当前后台，不重置共享引用。
