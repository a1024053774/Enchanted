# T-249-1 第六版恢复卡交付

**PASS（worker 恢复与补证范围）**。按任务卡从基线 B 到候选 C 恢复既有实现和证据，补入主控已完成的真实窗口结果，并在当前 worktree 重跑三条完成条件。**INCOMPLETE（整票）**：仍待显式 submit 受理、最终限定审查、terra 独立验收、用户批准及门禁集成。

## 恢复与版本边界

当前 worktree 基线：`05002a377914d52372a4cd46a08fa40229d70e1f`。恢复命令：

```sh
git diff --binary b7cce248c5ed85dd9342ade10886287365273863 1243bc15f979976967cfd2d5cdd3a2acce6df635 | git apply
```

命令退出 0；原补丁中的历史日志触发 20 行空白警告，原文保留。没有 cherry-pick 旧身份提交、移动共享引用或修改 sparse 设置。恢复涉及的 15 个 workbench 文件已与 C 逐字节核对；其余 workbench 和 acceptance 在当前基线与 C 无差异。没有新增产品、开发测试或脚本逻辑。

Tracer bullet：保留 C 已有的 Workbench → PanelDock → preload/main → gitHost → Git 路径，CLI 复用同一模型与命令。Deep modules：没有新增接口或包装层。Ubiquitous language：沿用 Git 图、受管 worktree、no-details、no-diff 与指定断言名称。

本次身份：task `a2a+T-249-1`，attempt `90127e07-7aa0-41d3-ade9-55a56a9ff584`，session `edf0885f-f2d3-475c-9097-4f584c21813c`，fence 5，spec/card 6。派发配置为 Codex `gpt-6-astra` xhigh；实际提交身份与模型由钩子自动追加，不手写 A2A 尾注。

## 当前 worker 实跑

| 命令 | 结果 | 证据 |
| --- | --- | --- |
| `/usr/bin/python3 acceptance/T-249/check_git_graph.py` | PASS，退出 0 | [acceptance.txt](acceptance.txt) |
| `/opt/homebrew/Cellar/node/26.5.0/bin/node --test workbench/tests/test_t249_git_host.mjs` | PASS，22/22，退出 0 | [host.txt](host.txt) |
| `/usr/bin/python3 workbench/tests/test_t249_outside_safety.py` | PASS，6/6，退出 0 | [outside-safety.txt](outside-safety.txt) |

各次 TMPDIR/TMP/TEMP 都指向 `/private/tmp/a2a-requests-lnFual/` 下本次创建的独立子目录，PATH 前置 Node 26.5.0 所在目录，PYTHONDONTWRITEBYTECODE=1；精确环境及命令保存在各日志。三个临时根清理前都是 0 文件、0 字节；先保存状态再清理，*-cleanup.json 记 temporary_directory_removed=true。没有创建窗口、构建缓存或安装产物。

## 补交审查需要的证据

[主控窗口证据报告](outside-controller-02/RESULTS.md)包含首轮五项启动超时、随后两次各 142 项正例、五个指定业务反例、清理、正式后台与用户 core 不变、Test 包版本。窗口和打包的执行者是主控，实际被测版本为 C，不是本 worker 或本次文本提交。46 份原始文本共 225726 字节，完整来源提交与路径见 SOURCES.json，最后审查原文也已导入。

本轮只回应 review `170295e4-b8ce-4804-8954-925c1fca8bba` 的唯一证据条目；不再泛化源码审查或重复扫描。主控既有 design-integrity 扫描与人工核对见复制的 DETAILS-WINDOW.md，不能把本轮恢复写成再次执行。

提交前检查暂存 workbench / acceptance 与 C 无差异；提交后还将运行 `git diff --exit-code 1243bc15f979976967cfd2d5cdd3a2acce6df635 HEAD -- workbench acceptance`，将含最终提交号的结果保存到本次请求目录的 `t249-fence5-verification/final.txt`，避免为正常回执再造提交。项目 status 证据保存在本目录；恢复引出的 REVIEW.md Verified stale 按第六版卡交主控集成后处理，worker 不改冻结文档、地图或 ticket。

额外可写目录：派发为 `[]`，无改动。请求目录仅用于本轮临时夹具、提交后核对文本与 CLI 请求，不进入 Git。

**Works**：既有实现按指定补丁恢复；主控实际窗口证据已导入且来源字节一致，三条当前无界面完成条件通过。

**No regression**：当前冻结验收 PASS、宿主 22/22、脚本安全 6/6；产品和测试须保持 C 原样。未运行全仓、窗口、打包或新产品评审，符合本次恢复卡范围。

**Risk / undo**：本次仅提交并显式 submit 一次，queued 不代表受理。整票还需最终审查、terra、敏感变更用户批准和 gate integrate；不 push。撤销须由主控经门禁处理，不回收或接管其他 attempt；原失败证据保留。
