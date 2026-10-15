# T-084 尾注与启动记录核对

状态：PASS。工作树 `exec/t084`，基线 `fb5dd288721f105d0ca1e8732ca6c6e420aff78a`。本会话没有 commit、没有 push。ticket 仍 open。

门禁在受管 submit 之后，把本 attempt 的启动记录放在 `attempt.delivery` 上。核对用的就是这份值，不从尾注或其他提交反推。

| 尾注 | delivery 字段 | 启动记录字段 |
| --- | --- | --- |
| Launch | `launch_id` | `id`（同时等于 `runtime_identity.launch`） |
| Tool | `cli` | `cli_version` |
| Model | `model` | `model` |
| Effort | `effort` | `effort` |

真实窗格里，Tool 来自 `A2A_TOOL`，写入时等于 `cli_version`。Model、Effort 在提交时取 `sessionFacts` 的观察值（`panes.ts` 的 `launchInfo`）。钩子允许 Model、Effort 在读不到回合时写成 `unknown`；submit 拒绝观察值为 `unknown` 的交付（`delivery_facts_unknown`）。用户决定只保留尾注 Model 为字面量 `unknown` 的例外，Effort 不在此列。

本票跑的是受控宿主 `workbench/tests/daemon_acceptance_host.ts`。它在 dispatch 时把记录追加到 `worker-creations.jsonl`，`sessionFacts` 返回同一对象。记录里的 `cli_version` 固定为 `controlled-runtime fixture`，`model` / `effort` 抄任务卡（`gpt-6.1-sol` / `xhigh`）。每个案在 verify 之前先要求 delivery 与这条记录一致，不一致则以缺口退出。本次没有出现缺口。

没有 `attempt.delivery` 的 attempt（只 claim、未走受管 submit）拿不到这四项记录。新比较因此先看 delivery 是否存在；没有记录时仍只要求这四项非空。历史 claim 套件本票没有重跑。

伪造常量写在测试里，不从门禁输出读取：Launch `not-this-attempt-launch`，Tool `not-the-recorded-cli`，Model `not-the-recorded-model`，Effort `not-the-recorded-effort`。正例的四项从该案的 `launch-record.json` 取值。Model unknown 正例只把 Model 写成 `unknown`，其余三项仍等于记录。

入口是 `node workbench/src/gates/cli.ts`，经上述宿主连隔离的 `/tmp` 状态目录。没有调用真实模型 API。夹具仓库在 `/tmp` 下，不在证据目录里。

## 红态

在加入四行比较之前跑的。被放行的原始输出在 `red/`。汇总：`red/summary.json`，状态 PASS。宿主参数：`red/host-argv.json`（core 为工作树的 `workbench/src/gates/core.ts`，状态目录 `/tmp/t084-9c6ejtnw`）。

```sh
cd /Users/luckye/Documents/Code/a2a-wt-t084
python3 -B workbench/tests/test_t084_trailer_record.py --phase red --output evidence/2026-10-15-batch15/T-084
```

四种不符的 verify 均为 ok，`trailer_check.passed` 为 true，error 为空，人工介入 0。与记录一致的正例和 Model `unknown` 同样通过。完全无尾注：`red/none/events.json` 里 `human_intervention` 为 1 条，通道 `commit-trailer`，标签 `推断：缺尾注`；汇总里 `user_inputs` 为 1。

## 修复

`workbench/src/gates/core.ts` 的 `checkTrailers` 在原有 Attempt/Session/Role 比较之后增加四行，拒收码仍是 `trailer_identity_mismatch`。Model 先放行字面量 `unknown`，再与 `delivery.model` 比较。`workbench/README.md` 原句只写了 Task、Attempt、Session、Role 四项；`project_map.py status` 因此把该 living doc 标为 stale。已改成与现在的核对一致，没有改地图。

## 绿态

同一入口，对照已含上述四行的 core。进程退出码 0，标准输出 `{"status": "PASS", "phase": "green"}`，墙钟 13.19 秒。汇总另存于 `green/summary.json`（顶层 `summary.json` 后来被变异阶段覆盖）。宿主参数：`green/host-argv.json`，状态目录 `/tmp/t084-713w20a6`。命令日志：`green/commands.jsonl`。

```sh
cd /Users/luckye/Documents/Code/a2a-wt-t084
python3 -B workbench/tests/test_t084_trailer_record.py --phase green --output evidence/2026-10-15-batch15/T-084
```

| 案 | verify | 错误 | trailer_check | 人工介入 | 主分支 |
| --- | --- | --- | --- | --- | --- |
| launch | 拒 | `trailer_identity_mismatch` | passed false，error 同码 | 0 | 未动 |
| tool | 拒 | `trailer_identity_mismatch` | passed false，error 同码 | 0 | 未动 |
| model | 拒 | `trailer_identity_mismatch` | passed false，error 同码 | 0 | 未动 |
| effort | 拒 | `trailer_identity_mismatch` | passed false，error 同码 | 0 | 未动 |
| match | 过 | 无 | passed true | 0 | 未动 |
| unknown | 过 | 无 | passed true | 0 | 未动 |
| none | 过 | 无 | passed true | 1，标签 `推断：缺尾注` | 未动 |

Launch 案的 CLI 原始回执在 `green/launch/verify.json`：`ok` false，error `trailer_identity_mismatch`，尾注 Launch 为 `not-this-attempt-launch`，记录号 `160ff51d-6e00-42fd-a540-73c60fe0413e`。Tool / Model / Effort 三案的尾注只有对应一项是伪造值，另外三项等于该案记录。match 的四项等于记录 `f3115110-db5f-4880-8078-d2e8ac7427a5`（Tool 为 `controlled-runtime fixture`，不是任务卡上的 Codex）。unknown 的 Model 为 `unknown`，记录上的 model 仍是 `gpt-6.1-sol`。none 的提交说明没有 `A2A-` 行；`green/none/events.json` 中 `human_intervention` 为 1，标签 `推断：缺尾注`。

各案的 `verify.json`、`events.json`、`launch-record.json`、`delivery.json`、`commit-message.txt` 在 `green/<案>/`。

## 变异

一次性副本：把 `workbench/src` 拷到 `/tmp/t084m-*`，只删一行比较，`node_modules` 指向工作树的 `workbench/node_modules`，宿主改加载该副本的 `core.ts`。进程退出码 0，标准输出 `{"status": "PASS", "phase": "mutants"}`，墙钟 30.74 秒。汇总在顶层 `summary.json`。四个案的原始输出在 `launch/`、`tool/`、`model/`、`effort/`。删行后的 diff 在 `mutant-patches/`。副本已从 `/tmp` 删除。

```sh
cd /Users/luckye/Documents/Code/a2a-wt-t084
python3 -B workbench/tests/test_t084_trailer_record.py --phase mutants --output evidence/2026-10-15-batch15/T-084
```

针文本不含行首空白，删行后下一行多了一段缩进，比较语句本身不在。行为上只有被删的那一项变为放行，其余三项仍是 `trailer_identity_mismatch`。

| 删掉的比较 | 放行 | 仍拒 |
| --- | --- | --- |
| Launch | launch | tool、model、effort |
| Tool | tool | launch、model、effort |
| Model | model | launch、tool、effort |
| Effort | effort | launch、tool、model |

## 未覆盖

- 受控宿主的 model、effort 与任务卡相同。伪造值与记录不同，所以拒收成立；这项不能单独证明比较对象不是任务卡。Tool 可以：正例用的是记录里的 `controlled-runtime fixture`，任务卡写的是 Codex。
- 没有 delivery 的 claim 路径没有重跑。
- 没有启动真实 CLI 窗格，没有调用模型。
- 本机 `workbench/node_modules/node-pty/prebuilds/darwin-arm64/spawn-helper` 原为 644，按 README 的既有做法改为 755 后宿主才能启动。该文件在 gitignore 里，产品代码没有改权限。

只读复核读了已保存的 CLI 输出、启动记录和 delivery，没有重跑套件，结论 PASS。局限与上列相同。

## 地图

在工作树执行：

```sh
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
```

README 更新后：Problems 0，Stale living docs 0，退出码 0。T-084 仍在 frontier，状态 open。
