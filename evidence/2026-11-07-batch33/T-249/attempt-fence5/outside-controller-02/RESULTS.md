# T-249：补交主控真实窗口证据（fence 5）

**PASS（本次证据补交）**。审查 `170295e4-b8ce-4804-8954-925c1fca8bba` 唯一待补项是 no-details / no-diff 等窗口条件的实际检测能力。主控已在审查前跑完，但原候选没有带入这些文本；本目录把原始文本带入新候选，供最终限定核对。没有更改产品、测试或编排脚本，也没有重新执行窗口、打包或泛化源码审查。**INCOMPLETE（整票）**：门禁最终审查、terra 独立验收和用户敏感变更证据批准仍待执行。

## 身份与来源

- 实际窗口运行及打包执行者：执行主控；不是本次 worker。本次 worker 仅恢复候选、导入文本并核对结果。
- 实际被测代码 C：`1243bc15f979976967cfd2d5cdd3a2acce6df635`。原运行绑定 task `a2a+T-249-1`、attempt `b33751df-0d57-4223-834d-4d467b199e22`、fence 4、spec/card 5。
- 本次交付：attempt `90127e07-7aa0-41d3-ade9-55a56a9ff584`、session `edf0885f-f2d3-475c-9097-4f584c21813c`、fence 5、spec/card 6；当前身份由 Git 钩子记录。
- 窗口、打包及清理文本来源提交：`c1e737a6b608ae36f6537073422d3deac9c22e78`；来源根目录：`/Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-249/controller/`。
- 最后审查原文来源提交：`cee49e1df19627a77f77e54e22e7faf41058d3c2`，同一来源根目录的 `review-final-result.json`。
- [SOURCES.json](SOURCES.json) 逐文件记录完整提交、原相对与绝对路径、复制位置和字节数。46 份文本共 225726 字节均按 Git 原始字节复制；[核对结果](import-verification.json) 记录逐字节比较及指定结果检查，无校验值计算。复制的旧报告保留原运行身份与当时状态。

## 审查所需的真实正反例

| 主控运行 | 原始结果 | 本次核对 |
| --- | --- | --- |
| [第一次正例](window-details-cache-02/green/run.json) | PASS，142 项 | 无失败断言，退出 0 |
| [no-panel](window-details-cache-02/no-panel/run.json) | FAIL，符合预期 | “侧边面板存在” |
| [no-details](window-details-cache-02/no-details/run.json) | FAIL，符合预期 | “点击提交后详情可见” |
| [no-diff](window-details-cache-02/no-diff/run.json) | FAIL，符合预期 | “点击文件后单文件 diff 可见” |
| [parents](window-details-cache-02/parents/run.json) | FAIL，符合预期 | “每行父提交与 git rev-list --parents 一致” |
| [order](window-details-cache-02/order/run.json) | FAIL，符合预期 | “提交顺序与 git rev-list --date-order --all 一致” |
| [恢复后正例](window-details-cache-02/green-after-mutants/run.json) | PASS，142 项 | 无失败断言，退出 0 |

五项反例均退出 1，指定断言映射见 [mutants-result.json](window-details-cache-02/mutants-result.json)。原始 run.json 含命令、独立 Git 预期及窗口观察；详情通过可见提交行与文件按钮进入，覆盖根提交、普通提交、未提交、首次提交前，以及特殊文件名。这里的 FAIL 是坏实现被拒绝的预期结果，不是原候选产品失败。

审查在自己的沙箱运行 no-details 时，`/bin/ps` 被拒绝，尚未进入 Electron，不能作业务红态。[审查原文](review-final-result.json)明确没有认定新的产品缺陷。本目录已有主控真实 no-details / no-diff 指定红态，回应的正是这一条证据缺口；三条机械条件本身仍不足以证明窗口行为，不能替代这些结果。

## 首轮失败、清理和包版本

首轮标准脚本结果原样保留在 [outside-details-01/summary.json](outside-details-01/summary.json)。总脚本退出 1；正例与 no-details、no-diff、parents、order 五项因隔离后台启动超时为 INCOMPLETE，均不是业务红态；只有 no-panel 命中“侧边面板存在”。首轮自有 hc 缓存为空，随后补入固定缓存取得上面七次结果；不能据此断言下载是所有超时的唯一根因。

首轮六次与后续七次 run.json 都为 cleanup PASS、fixture_removed true、user_core_unchanged true。[清理记录](window-details-cache-02/cleanup.json)保留缓存、依赖、截图的目录、文件数与字节数；这些临时产物已由主控删除，待独立验收的 Test 包保留。正式后台 PID `81233`、启动时间 `2026-11-08 13:56:08Z` 前后不变；原进程清单与复核见首轮 summary 及 [formal-backend-after.json](window-details-cache-02/formal-backend-after.json)。本次 worker 没有操作这些进程或目录。

标准打包命令：`npm run package:mac -- --variant test --slot t249-fence4-details-20261108-01`。主控保留包：`/private/tmp/t249-outside-9iitgp1b/a2a-build-t249-fence4-details-20261108-01/Enchanted Test.app`。包内 revision 精确为 C、无 `+dirty`，bundle 为 `org.a2a.workbench.test`；固定 Electron 43.4.1、hc 0.1.15，标准签名检查通过。依据是 [保留与版本记录](outside-details-01-preservation.json)及 [package.log](outside-details-01/package.log)。本次文本提交没有重新打包，不把包标成新提交版本。

重放窗口的原命令、cwd 与临时目录见 [start.json](window-details-cache-02/start.json)及各 run.json：`/usr/bin/python3 workbench/tests/test_t249_git_graph_e2e.py --output <全新目录> --shots <本轮临时截图目录>`，反例追加 `--mutant no-panel|no-details|no-diff|parents|order`。主控当时 PATH 前置 `/opt/homebrew/bin`，TMPDIR/TMP/TEMP 指向自有临时目录，ENCHANTED_HC_CACHE_DIR 指向复制的固定 hc 缓存；本轮按恢复卡无需重放。

**Works**：实际被测版本 C 的窗口正例两次各 142 项；五项指定业务反例、首轮失败、清理和包版本文本均已进入本候选，来源与执行者清楚。

**No regression**：复制前后原文逐字节一致；当前 worker 的三条无界面复验结果见 [本次恢复报告](../RESULTS.md)。没有运行全仓测试，也没有宣称此次文本补交重新执行了窗口或打包。

**Risk / undo**：整票仍需最终限定证据核对、terra Computer Use 加常规测试、用户阅读敏感证据后批准。当前只交付，不集成、不 push；若要撤销本次补证，可在后续受管变更中删除本目录，不改写原主控证据或旧失败记录。
