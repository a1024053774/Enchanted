# T-198 独立只读审查（第 2 轮）

STATUS: PASS

TARGET: `/private/tmp/t198-cand2`，`SNAPSHOT.txt` 指定的 HEAD `4a5e1f3fcd674254d184316a00cc2edead2b0f4a` 加 `T-198.diff`。结论限于 T-198 冻结候选及本轮复审范围，不代表整个产品的发布验收。

依据：T-198 任务卡、T-196 Resolution 第 2 条及其硬门禁约束。只读取冻结源码；活动仓库仅用于读取任务卡、指定版本的 `git show` 和 brief 指定的证据摘要。未修改候选、仓库或既有证据，未提交。所有新增产物均在本审查目录。

## FINDINGS

没有确认的新发现。上一轮 P1、P2 均关闭。

### P1：放行生命周期已在根因层修复

位置：`workbench/src/gates/core.ts:1555`、`:4013`、`:4264`；集成检查在 `:4287`。

三个入口分别结束旧放行：`invalidate` 撤销当前执行尝试时清除；主控 `out_of_card reject` 在走现有打回前清除；`submit` 真正记录一份新交付时清除。放行没有仅靠候选 SHA 相同而重新生效的存储来源。

这里按 **Ubiquitous language** 区分“新交付”和“同一交付的重验”：工作分支前进触发 `revalidateForIntegration`，没有新的 submit，原候选和已放行文件范围仍受原判断覆盖；新候选、打回后重交、撤销或改卡后重派，则必须重新判断。`outOfCardJudged` 仍允许重验清单为已放行清单的子集；出现新增卡外文件时不会匹配。未发现这项包含关系形成可达绕过。

独立复验结果：

| 场景 | 结果 |
| --- | --- |
| C1 放行后打回 → C2 打回 → 重交 C1 | 最后一次集成返回 `out_of_card_unjudged`，`extra.txt` 未进入 main。 |
| 放行后 revoke／revise，再回收、重派、重交同一 SHA | 旧判断已清除；实际走到卡外门禁后仍返回 `out_of_card_unjudged`。重新明确放行后可集成。 |
| 放行后工作分支前进，同候选重验 | 验证记录更新，原判断保留并正常集成；没有把 verification ID 不同误判为新交付。 |
| 放行后发生真实 Git 合并冲突，原 worker 返工 | 冲突返回 `merge_conflict`；新交付清除旧判断，重验后集成须重新放行。 |
| 放行后发生冲突，原 worker 已停止，门禁更换 worker | 新 attempt 不继承旧判断；新交付仍须判断，明确放行后集成成功。 |

按 **Deep modules** 的审查尺度，本次修复保留 `A2AGates` 作为状态变更的唯一所有者，直接在现有生命周期入口清除授权，没有新增平行权限通道、兼容分支或兜底集成路径。

### P2：自动 run 暂停说明与代码一致

位置：`workbench/terminal/plugin/enchanted-a2a/skills/a2a/SKILL.md:27`、`workbench/src/terminalCli.ts:38`、`workbench/README.md:221`、`:454`。

这些说明都已明确：主控身份结束或额度用完后的自动集成仍经过卡外判断门禁；没有有效放行时返回 `out_of_card_unjudged` 并暂停。skill 与 README 还写明 `outcome: paused`、任务保持 `verified`、worker 不回收，以及主控回来判断、集成的后续操作。README 同时明确了新交付与撤销／改卡后的重新判断规则。

本轮实际运行生产 `run`，以受控的 ended 主控状态触发自动集成，得到上述暂停结果；main 没有卡外文件。代码中 ended 与 quota_exhausted 共用 `follow` 的非 active 分支，调用相同 `integrate`（`core.ts:3093`、`:3102`），再由 `runFailed` 记录暂停。未发现说明与这段分支不一致。

## EVIDENCE

### 本轮执行的检查

以下命令的工作目录均为 `/private/tmp/t198-review2`；两份探针各只运行一次，退出码均为 0。脚本以 `wx` 保存结果，复跑须使用新的输出文件名，保留原结果。

```sh
node lifecycle-probe.mjs /private/tmp/t198-review2/lifecycle-01.json > lifecycle-01.log 2>&1
node lifecycle-extra.mjs /private/tmp/t198-review2/extra-01.json > extra-01.log 2>&1
node /private/tmp/t198-cand2/workbench/src/terminalCli.ts help > terminal-help.txt 2> terminal-help.stderr
python3 verify-snapshot.py > snapshot-rebuild.log 2>&1
```

- [lifecycle-01.json](lifecycle-01.json)：8 个场景记录通过，包括 C1→C2→C1、同候选重验、验收文件硬拒、Git 元数据硬拒、自动 run 暂停和新旧历史事件投影。原 revoke／revise 场景在集成前被 `git_metadata_changed` 阻止；它们只能证明旧判断已清除及硬拒未失效，不能单独证明卡外门禁被执行。
- [extra-01.json](extra-01.json)：补充的 8 个场景记录通过。revoke／revise 两例在夹具仓库中删除已回收旧 worker 的分支引用，保留 `refs/a2a/attempts` 证据引用，然后重交同一 SHA，从而实际到达 `out_of_card_unjudged`。没有修改或替换生产门禁。另覆盖原 attempt 冲突返工、更换 attempt 冲突返工、三种 worker 调用身份均不能自行放行，以及纯卡内交付无需新增判断即可集成。
- [terminal-help.txt](terminal-help.txt)：运行真实帮助入口，输出包含卡外判断示例和自动 run 暂停条件；stderr 为空。
- [snapshot-rebuild.json](snapshot-rebuild.json)：用指定 HEAD 的 `git show` 重建原文件，在本目录副本应用冻结补丁，8 个变更文件均与冻结候选逐字节一致。新增测试在 HEAD 不存在，`git show` 的退出码 128 是预期的新文件情况，补丁应用成功。
- [snapshot-stability.json](snapshot-stability.json)：开始与结束共 647 个候选文件的路径、大小、`mtime_ns` 清单一致，未发现候选变化；未计算摘要值。该检查不把依赖软链接内的内容视为冻结源码。

探针作为 **Tracer bullet** 穿过生产 `A2AGates.call`、真实 Git 合并／引用更新、SQLite 存储和评分历史；worker 原生运行观察及独立审查通过结果由夹具控制。它证明的是这些状态与授权逻辑，不证明原生 CLI 沙箱或模型判断能力。运行使用的临时仓库及数据库均保留在 JSON 记录的 `root` 目录。

### 提供的端到端证据与反例

已检查冻结测试 `workbench/tests/test_t198_out_of_card_e2e.py`。它从真实后台 socket、经批准的终端主控、实际 Claude Code 和 hook 提交链路观察结果；模型响应由本地脚本化接口提供。预期来自任务卡：待判断、无理由拒绝、有理由集成、打回反馈、验收文件硬拒和审查输入清单，没有调用生产判断函数来生成答案。集成成功还读取 main 文件树，不能只凭 `ok:true` 通过。

brief 指定的摘要已原样复制至 [supplied-evidence](supplied-evidence)：

| 文件 | 实际观察与用途 |
| --- | --- |
| `frozen2-green.json` | 8 项检查通过，含 `withdrawn_accept_does_not_return`；最终重现的 C1 被 `out_of_card_unjudged` 拒绝，main 没有 T-2 的卡外文件。 |
| `red-withdrawn-prefix-02.json` | 修前的同一业务断言失败；旧 C1 被集成，`notes/extra-2.txt` 进入 main。证明旧放行重现是可达问题，测试会拒绝该已知坏实现。 |
| `frozen2-mutant-boundary-still-fails.json` | 恢复“卡外直接验收失败”后，失败于 `out_of_card_waits_for_judgement` 业务断言。 |
| `frozen2-mutant-integrate-unjudged.json` | 绕过判断门禁后，失败于 `integrate_refused_before_judgement`，实际无判断集成成功。 |
| `red-withdrawn-prefix.json`、`green-02-withdrawn.json`、`green-03-withdrawn.json` | 保留此前被审查收尾或夹具操作问题阻断的结果，不把它们作为修复通过证据。 |

上述反例／变异摘要的顶层状态写为 `INCOMPLETE`，但保留的错误字段明确显示目标业务断言失败；本报告将其作为“坏实现被测试识别”的证据，没有把这些运行称为 PASS。

既有 e2e 的重放命令是：

```sh
python3 /private/tmp/t198-cand2/workbench/tests/test_t198_out_of_card_e2e.py --summary /private/tmp/t198-review2/e2e-rerun.json
```

本轮未执行该命令。原运行的 argv、夹具位置和逐项结果见所提供摘要。

## LIMITATIONS

- 按 brief 的环境限制，本轮没有重跑完整原生 worker e2e；当前沙箱的 `sandbox-exec` 会阻断 worker submit。后台与原生 CLI 边界采用提供的冻结候选端到端记录，并以本轮独立隔离复验补强。本轮探针不能替代该边界的重新执行。
- revoke／revise 重交同 SHA 的补测包含夹具引用调整，用于排除更早的元数据拒绝，直接检验授权失效；它不声称正常产品回收流程会删除未集成的旧 worker 分支。
- 冲突确由真实 Git 产生；后续 worker 停止／更换的原生状态、反馈接收以及审查“通过”由夹具提供。没有重新验证真实模型是否能解决冲突或正确判断改动范围。
- 本轮自动 run 动态覆盖 ended；quota_exhausted 仅核对共用代码分支，未单独运行。任务页清单与理由核对到 `task_history` 投影及现有展示链路，没有打开桌面界面做视觉验收。
- 未做无关全套回归、生产网络调用或发布检查。以上限制不扩大为整个 Agent 产品的能力或上线结论。
