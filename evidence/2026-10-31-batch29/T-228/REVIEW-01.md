STATUS: FAIL

FINDINGS:

- [P1] [hc.ts:203](/Users/luckye/Documents/Code/a2a/workbench/src/hc.ts:203) — `lsof` 的路径字段可能经过转义，不能直接与原路径比较。例如 `LC_ALL=C`、数据目录为 `/private/tmp/测试/state` 时，非 ASCII 字节会被转义，第 204 行会拒绝自己的 core，导致后台无法启动。本机 `/usr/share/man/man8/lsof.8:2271–2317` 明确描述了这一行为。应使用不依赖 locale 的文件身份比较，或正确处理转义；新增测试第 45 行固定使用 ASCII 路径，覆盖不到此反例。
- [P2] [daemon.ts:61](/Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts:61) — `store.event()` 若因数据库锁定、磁盘写入失败等原因抛错，会跳过后面的 `throw error`，覆盖原始 hc 启动异常。该调用直接执行 SQLite INSERT（[store.ts:61](/Users/luckye/Documents/Code/a2a/workbench/src/store.ts:61)），没有保护；最外层只打印最终异常（daemon.ts:1119）。应同时保留原始启动失败与事件写入失败。

EVIDENCE:

- 已读 T-228、T-220、T-212 票面、相关规格与调用路径；确认五个候选文件逐字对应 `candidate.patch`，HEAD 为 `03ba1cf549e578a4dd6061a1e3a3cfdd316c4a5b`。
- hc.ts:195–207：仍检查 core 与后台的 PGID 不同，符合 T-212 的进程组 detach 要求；`lsof` 执行失败、超时会向外抛出，正常输出中缺少目标锁路径也会拒绝。普通的“该 pid 未打开私有锁”会被拒绝。
- 新测试的 holder/foreign 期望来自 T-228 验收。`red-holder-01/run.json` 的 `daemon_accepted_holder_core=false`；`red-foreign-01/run.json` 与 `mutant-any-lock-foreign-01/run.json` 均因接受外来 core、缺少拒绝事件而失败，变异具有区分力。
- `green-holder-01/run.json`：同 core、同 shell pid、接回事件及状态为 inexact 的检查全部成立。`green-foreign-01/run.json`：启动退出 1，拒绝事件包含私有锁路径，终端数保持 0。
- T-212 第 231 行保留私有 XDG 目录要求，新增 `initial-daemon` 符合 holder 沿用受控环境的票面事实；`t212-core-crash-02/run.json.core_restart.observed_environment` 支持该变化。
- REPORT 主要运行结论与所链 JSON 一致。第 36 行字段名称不准确：Electron 记录实际使用 `user_core_directory_unchanged`、`user_core_processes_unchanged`，两者均为 true。
- 未发现新增 fallback、重试、兼容分支或平行运行路径。

LIMITATIONS:

- 未运行测试、status 脚本、hc 或供应商命令；未修改文件。上述路径反例与数据库异常路径属于静态推演，未现场复现。
- 现有证据未覆盖 `lsof` 失败/超时、伪造 pid、同进程组和路径转义反例；“打开锁文件”也不等于证明持有排他锁。
- `t212-core-crash-old-assert` 的环境探针原文件已删除，无法独立确认 REPORT 第 32、40 行所述具体值；JSON 只保存了断言失败位置。