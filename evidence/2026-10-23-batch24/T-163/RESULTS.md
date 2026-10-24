# T-163-1 / a1

状态：INCOMPLETE。RUN-OUTSIDE-01 的真实 Haiku oracle 红态成立；C5 漏项未复现，派发被夹具权限阻断。已修改两个产品说明入口并调整本票夹具，等待执行主控运行 RUN-OUTSIDE-02，尚无修后绿态。

## 范围与入口

- 工作分支 `exec/t163`，产品基线 `e83a8a04e`；完整版本写入运行摘要的 `product_revision`。
- 应用内主控说明位于 `workbench/terminal/plugin/enchanted-a2a/skills/a2a/SKILL.md`，命令帮助位于 `workbench/src/terminalCli.ts`。产品修改只涉及这两个说明入口及对应 README 说明；不做策略引擎。
- 使用项目的 Ubiquitous language：执行主控、任务卡、attempt、门禁入口。沿用已有 Fixture/Electron 驱动，不新建生产包装层（Deep modules）。本票是提示词修复，不跨生产层增加功能，不另建 Tracer bullet。

## 修前复跑

主控命令：

```zsh
zsh evidence/2026-10-23-batch24/T-163/RUN-OUTSIDE-01.sh
```

`test_t163_controller_e2e.py` 支持 `--summary <新路径>`、`--revision <提交>`、`--mutant parent-instructions`。同一场景提示用于修前与修后，变异把两个产品说明入口恢复为本票基线，不改变输入或 oracle。

1. C5：真实 Haiku 执行主控经界面批准后，按原场景派两个受管任务。A 首版应故意漏总计、等真实验收打回后再补；B 必须先上报分组问题，等回答后才写文件与交付。两 worker 启动后执行主控结束回合。脚本保存实际采用卡的版本、后台状态、原生工具记录与截图，交主控独立做语义核对。不会用几段字串匹配把“已自检”判成通过；C5 自动摘要保持 INCOMPLETE。
2. 验收脚本：另一个干净的真实 Haiku 执行主控根据原始 pantry 数据和明确的文档要求生成两个 Python 检查程序。测试用未提供给模型的输入执行它们，覆盖正确文档、另一种正确排版、错数字、漏总计、反向语义、非零库存、分组、原始数据变化后的旧答案与新正确答案。退出码、标准输出和错误保存到各 case/run.json。业务失败才是红态，环境失败不算。

真实供应商模型仅用于项目终端主控，指定 `claude-haiku-5-5`；C5 的受管 worker 使用真实 CLI 加本地脚本化 Messages 接口，只结束观察回合，不写候选，不形成验收证据。本次不运行真实 reviewer 或集成，不把本票的派发检查宣称为完整交付旅程。

两场景各预留 2 个真实根提示，RUN-OUTSIDE-01 实际合计 4/16；共享追加式 `model-budget.jsonl`，失败预留不自动释放。根提示数从各自原生 JSONL 读回，技能展开与工具结果不另算。摘要保留实际 assistant model；仅启动 argv 不算供应商模型事实。

模型行为有随机性。如果修前未复现，不能把过去 T-155 的失败冒充同场景红态；交回主控决定下一步，不改提示诱导失败、不自动重试。

## 修前结论与本次修改

主控 #47 的独立结论与 worker 读回见 `controller-baseline-01.md`。oracle 的错误来自验收脚本自加未要求的明细条件、忽略反向语义；没有环境错误，构成本次红态。C5 要求均已写入草稿卡，但无显式逐项自检，且未派发；不把这次运行写成遗漏复现。执行主控已明确要求据此继续修提示词。

两个说明入口补了三项判断要求：

- 派发前把每条用户要求对应到任务卡并列核对结果，尤其是顺序、等待和演练首版；漏项先改，首版演练不替代最终完成条件。
- 验收从原始数据推导，保存卡前实际运行正确、明显错误的样本；核对数字与含义的对应，拒绝错数字、反向语义与缺项，接受未限定排版的正确内容；保留样本、命令和退出码，不擅加条件，不以文件存在或关键词出现代替验收。
- 区分暂时未完成、明确拒绝与结果未知；报告原始错误、最后确定事实、具体停点和缺少的事实，无新事实停止轮询，未知写入不自动重发。

夹具权限根因在本票生成的临时 settings，不在产品启动器。修正为仅对隔离测试主控允许 Bash，保留 dontAsk 和子 agent 禁用；产品与受管 worker 的权限未改。RUN-OUTSIDE-02 中绿态与旧说明变异使用相同夹具设置，场景输入与业务 oracle 未改。

RUN-OUTSIDE-02 依次运行 C5、oracle 绿态；只有 oracle 绿态后才运行恢复旧说明的 oracle 变异（预先声明的反事实，不是重试）；最后跑 T-158 说明回归。最多新增 6 个真实根提示，累计预留 10/16。C5 仍由主控独立语义判断，不自动报 PASS。

```zsh
zsh evidence/2026-10-23-batch24/T-163/RUN-OUTSIDE-02.sh
```

## 当前验证与限制

- PASS：Python 编译、`--help` 与 diff 空白检查（未启动后台、Electron 或模型）。首次 py_compile 默认缓存目录被沙箱拒绝；改用允许的 `/private/tmp/t163-pycache` 后通过，这不是产品红态。
- PASS：本次修改后的 Python 编译、RUN-OUTSIDE-02 shell 语法、真实 `a2a help` 入口和 UTF-8/空白检查，见 `local-checks-02.json`。收尾 project-map status 仍仅有 T-158 缺 Resolution，stale living docs 为 0，见 `project-map-status-02.json`。
- PASS：将 T-155 历史弱验收原样交给本票输入探针，正确输入被接受，错数字、反向语义和分组四个坏样本揭露弱验收。结果见 `probe-oracle-known-bad.json`（首次内联运行）与 `probe-oracle-known-bad-replay.json`（下面命令重放）。这只证明测试可抓住已知坏检查器，不是本票真实模型修前红态。
- PASS：修前真实 Haiku oracle 检出误拒和反向语义误收；两个摘要无环境错误，实际模型与 4 个根提示已核对。这是有效失败证据，不是产品通过。
- INCOMPLETE：C5 漏项未复现；修后两场景、提示词变异、独立行为验收均等待 RUN-OUTSIDE-02。
- 相关回归：`test_t158_revise_retry_e2e.py --check instructions` 已放入 RUN-OUTSIDE-02，确认两个说明入口保留 T-158 的修订顺序，不启动真实供应商模型。
- M04 的三种状态与无新事实停点已加入同一主控说明；本卡指定的两个场景不会完整证明未知状态长轮询已消除，不能宣称可靠性或收益已改善。
- 会话开始 project-map status：既存 `T-158 closed without a Resolution`，stale living docs 为 0。该 ticket 在修改边界外，已向主控报告，未改地图或他人 ticket。

当前不声明 DELIVERED；这是按派发要求提交 RUN-OUTSIDE-02 后的暂停点。独立行为审查留在真实绿态与候选冻结之后，不以作者自检替代。

历史弱验收探针的重放命令：

```zsh
PYTHONPYCACHEPREFIX=/private/tmp/t163-pycache python3 evidence/2026-10-23-batch24/T-163/probe_oracle_known_bad.py --summary evidence/2026-10-23-batch24/T-163/probe-oracle-known-bad-replay.json
```

再次运行时必须换新的摘要路径；原始 case 目录保留在摘要的 `fixture` 路径，交主控按 T-088 归档。
