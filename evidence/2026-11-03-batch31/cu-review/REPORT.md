# 四张票独立审查

审查对象是本次工作区未提交的 `workbench/` 差异；没有修改产品代码、票或地图，也没有提交。下文 `独立证据` 均指 `evidence/2026-11-03-batch31/cu-review/independent/`；主控证据与本次独立运行分开标注。测试设置了 `ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/hc-cache`。这是一次只读审查，不代表已完成对修复的复审。

## T-231

- **满足**：主控的 `evidence/2026-11-03-batch31/T-231/bisect.txt` 记录 `f3a4a54162^` 为 0/9 失败、`f3a4a54162` 为 8/9 失败；代码显示 Codex 的 hook 身份核对发生在该路径的后续扫描之前。旧夹具用 hook 触发绑定因此失效，支持“测试夹具过时”的结论。
- **无法判断**：这还不能证明真实产品绝无缺陷。`workbench/src/questions.ts:23` 对尚未绑定的非空 session ID 判为不匹配，`workbench/src/panes.ts:2037` 对 Codex 在核对前不做 Claude 专属扫描；如果真实 hook 先于输出扫描绑定到达，就存在拒绝路径。现有证据没有证明该时序在真实入口可发生，也没有证明不可能发生；本次没有复现真实 Codex 的该时序。不能仅以夹具修复宣称产品绑定无缺陷。
- **满足**：`node workbench/tests/test_native_final_read.ts <独立证据>/t231` 九个场景通过；`evidence/2026-11-03-batch31/T-231/mutant-no-final-read.sh <独立证据>/mutant` 的已知坏实现九个场景均被检出。脚本退出 0 表示反例检出成功，不是坏实现通过。见 `t231.log`、`t231/results.json`、`mutant.log`。
- **无法判断**：是否需要按产品缺陷的真实入口红态及修复，取决于上述时序事实；本次审查有未解决的证据缺口，不能认定独立审查验收已全部满足。

## T-232

- **满足（主控留存证据）**：修前夹具残留清单见 `evidence/2026-11-03-batch31/T-232/red-residue.txt`；本次未独立重跑旧实现。
- **满足（本次故意失败场景）**：`python3 evidence/2026-11-03-batch31/T-232/forced_failure.py <独立证据>/ff.json` 如预期抛出 `T-232 deliberate failure after start`，包装脚本退出 0；`ff.json` 的 `INCOMPLETE` 是故意失败，不能称为业务 PASS。随后 `bash evidence/2026-11-03-batch31/T-232/residue.sh /private/tmp/t216-` 无输出、退出 0，见 `t232.log` 和 `residue.log`。
- **满足（现有正常场景证据）**：主控的 `green-t216-gui.json` 和 `green-user-core.json` 分别记录正常运行与用户 core 对照；本次两个 T-233 运行也报告用户 core 目录及进程未变，但它们不替代 T-232 的正常 `Fixture` 场景。未独立重复主控的全部正常运行及用户 core 对照。
- **无法判断**：仅凭上述有限场景不能证明所有不经 `Fixture` 的同类测试都已清理；本票独立审查发现之外的覆盖范围，需按具体入口核实。

## T-233

- **满足（主控留存证据）**：`evidence/2026-11-03-batch31/T-233/red-old-selector/run.json` 记录两个窗格与旧选择器下的未完成结果；本次未独立重跑旧选择器。
- **满足**：`python3 workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --output <独立证据>/t233` 和同命令追加 `--mismatched-screen`、输出到 `t233-mismatch` 均退出 0；详见 `t233.log`、`t233-mismatch.log` 及各自 `run.json`。真实界面的双窗格手动切换也符合预期，见下节。
- **满足**：本次只读审查未复现该票的阻塞缺陷；这不意味着其他三票通过。

## T-235

- **满足（主控记录）**：`evidence/2026-11-03-batch31/T-235/RESULTS.md` 在运行结果中列出轮询、并发读取、读取失败、索引不匹配和后台状态差异等可能方式；不能据此断言已经覆盖全部原因。
- **满足（历史证据）；本次未复现**：票内记录基线历史失败次数和状态，主控新运行的基线未复现，详见该票及主控 `RESULTS.md`。这两组证据使用的测试环境并不完全相同，不能把新通过结果当作否定历史红态。
- **不满足**：未确定根因，也没有产品修复，故不存在“修后连续通过”的证据。本次 `python3 workbench/tests/test_t165_queued_stop_e2e.py --scenario unrelated-stop --summary <独立证据>/t235-1.json` 和第二次改为 `t235-2.json` 均 PASS、`red_reproduced: false`；仅证明这两次未复现，不证明间歇问题消失。
- **不满足**：根因及修复验收仍未完成，本次审查不能批准该票关闭。

## 发现与反例

1. **阻塞：T-235 没有可验收的修复。** 输入与步骤：对当前候选运行上述 unrelated-stop 两次，另在隔离 UI 中运行普通终端 Claude；前两次自动测试均 PASS、没有重现原失败。观察：产品无代码改动、失败原因未确定，故不存在修复前后对照。这是验收证据不足，不是声称这两次重现了原 worker Stop 缺陷。
2. **阻塞验收判断：T-231 的真实早到 hook 时序未证实。** 反例条件：Codex 的非空 `session_id` hook 在输出触发的 session 绑定前进入 `signal()`；静态代码会走不匹配拒绝。实际：本次没有从真实入口复现这一顺序，因此这只是待证实风险，不报告为已复现的产品缺陷。需要真实入口时间顺序或独立约束证据，才能判断测试过时是否是全部根因。
3. **非阻塞观察，不等同于原缺陷：普通终端 Claude 状态保持未知。** 步骤与截图见下。它不是受管 worker 的 Stop 重叠场景，也没有同步记录后台状态，因此不能据此声称复现 T-235 原缺陷或断言标题栏落后后台。

## Computer Use

- 只以任务书指定的隔离包和参数启动，`process-start.txt` 显示后台使用 `/private/tmp/a2a-cur/state`；项目列表只打开 `/private/tmp/a2a-cur/project`。在该目录初始化 Git 仓库，在界面新建两个项目终端，各运行 `echo CU_FIRST_231`、`echo CU_SECOND_235`。期望点击任一侧栏行显示对应输出；实际两次对应正确，截图 `independent/first.png`、`independent/second.png`。
- 在第二个项目终端执行 `claude --model claude-haiku-5-5`；仅对 `/private/tmp/a2a-cur/project` 的 CLI 工作区信任框选择同意。发送“请回复：测试正常。不要操作文件。”，Claude 回答“测试正常。”并显示完成。回复完成后截图 `independent/claude-finished.png`：侧栏该行和标题栏的状态值均为“未知”，标题栏另显示“正在输入”；直到约三分钟后的观察仍未看到空闲。没有连续采样，无法给出各自变为空闲的秒数；也未验证后台状态。随后通过 `/exit` 退出 Claude。
- 从应用菜单退出隔离应用，结束命令行明确属于隔离包的剩余后台/core/holder；最终 `independent/process-after-cleanup.txt` 为空。没有操作用户 Herdr、其他 core 或 `/Applications/Enchanted.app`。CLI 信任框可能自行写入 Claude 的用户配置；未人工写入全局配置，也未核对 CLI 自行写入的具体条目。

## 范围和复现

所有独立测试命令的完整参数、输出和退出码分别保存在同名 `.log`。复跑时先设置缓存环境变量，并改用新的证据输出目录，避免覆盖本次证据。`independent/final-status.txt` 记录地图检查 `Problems (0)`、`Stale living docs (0)`；不以地图状态替代测试或验收结果。

结论：NO_GO
