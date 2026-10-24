# T-163-1 / a1

状态：INCOMPLETE。当前仅提交修前复跑脚本，等待执行主控运行 RUN-OUTSIDE-01；未改产品说明，未取得本候选的真实模型红态或绿态。

## 范围与入口

- 工作分支 `exec/t163`，产品基线 `e83a8a04e`；完整版本写入运行摘要的 `product_revision`。
- 应用内主控说明位于 `workbench/terminal/plugin/enchanted-a2a/skills/a2a/SKILL.md`，命令帮助位于 `workbench/src/terminalCli.ts`。后续最小修改只涉及这两个说明入口；不做策略引擎。
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

两场景各预留 2 个真实根提示，本轮合计预留 4/16；共享追加式 `model-budget.jsonl`，失败预留不自动释放。根提示数从各自原生 JSONL 读回，技能展开与工具结果不另算。摘要保留实际 assistant model；仅启动 argv 不算供应商模型事实。

模型行为有随机性。如果修前未复现，不能把过去 T-155 的失败冒充同场景红态；交回主控决定下一步，不改提示诱导失败、不自动重试。

## 当前验证与限制

- PASS：Python 编译、`--help` 与 diff 空白检查（未启动后台、Electron 或模型）。首次 py_compile 默认缓存目录被沙箱拒绝；改用允许的 `/private/tmp/t163-pycache` 后通过，这不是产品红态。
- PASS：将 T-155 历史弱验收原样交给本票输入探针，正确输入被接受，错数字、反向语义和分组四个坏样本揭露弱验收。结果见 `probe-oracle-known-bad.json`（首次内联运行）与 `probe-oracle-known-bad-replay.json`（下面命令重放）。这只证明测试可抓住已知坏检查器，不是本票真实模型修前红态。
- INCOMPLETE：真实 C5、真实验收脚本场景、修前红态、修后绿态、提示词变异、独立行为验收。
- 后续相关回归：`test_t158_revise_retry_e2e.py --check instructions`，确认两个说明入口保留 T-158 的修订顺序；放入修后 RUN-OUTSIDE 一起运行，不启动真实供应商模型。
- M04 的三种状态与无新事实停点将加入同一主控说明；本卡指定的两个场景不会完整证明未知状态长轮询已消除，不能宣称可靠性或收益已改善。
- 会话开始 project-map status：既存 `T-158 closed without a Resolution`，stale living docs 为 0。该 ticket 在修改边界外，已向主控报告，未改地图或他人 ticket。

当前不声明 DELIVERED；这是按派发要求提交 RUN-OUTSIDE 后的暂停点。

历史弱验收探针的重放命令：

```zsh
PYTHONPYCACHEPREFIX=/private/tmp/t163-pycache python3 evidence/2026-10-23-batch24/T-163/probe_oracle_known_bad.py --summary evidence/2026-10-23-batch24/T-163/probe-oracle-known-bad-replay.json
```

再次运行时必须换新的摘要路径；原始 case 目录保留在摘要的 `fixture` 路径，交主控按 T-088 归档。
