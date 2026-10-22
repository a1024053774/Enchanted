# T-129 候选 1 结果

- **候选**：`b3bd8aa84`。README 随后在 `03965053` 补了一句。证据运行期间源码未改动。
- **修前版本**：`400db6611`（T-126 收尾）。
- **结论**：**PASS**（待独立审查）。

## 改了什么

`workbench/src/daemon.ts` 里，Claude reviewer 有两条失败路径：

- 最终消息不合审查协议；
- 结论合协议，但门禁拒收。

这两条路径向 `panes.caller` 取调用者身份时，原来只传 `native_session`，没有传 Claude 身份核对需要的 `prompt_id`。结果是：

1. 核对抛 `native_identity_required`；
2. 门禁没有记下审查失败，Stop 转交失败；
3. 任务停在 `reviewing`，直到超时。

现在两处都传入与正常路径相同的字段（`prompt_id: stop.prompt_id`）。Codex 的核对不看这个字段。

## 端到端，脚本化 Claude（`e2e/commands.sh`）

真实后台、真实安装的 Claude Code（node-pty 里的交互模式），模型换成本地脚本化的 Messages 接口，不调用供应商。

`tests/test_t122_claude_worker_e2e.py` 新增 `--review-result`：

- `malformed`：最终消息不是 JSON；
- `rejected`：结论格式合规，但 `candidate_commit` 是另一个合法 sha，门禁拒收。

期望值来自 ticket 与门禁既有规则（`failReviewProtocol`）：审查记为 `unknown`，任务记为 `paused`，写一条 `review_protocol_failed`。Stop 转交一旦失败，测试立刻报出原因，不等超时。

| 运行 | 结果 | 失败于 |
| --- | --- | --- |
| green-malformed | PASS，16 项；记下 `review_json`，任务 `paused`，审查 `unknown` | — |
| green-rejected | PASS，16 项；记下门禁拒收的回执，任务 `paused`，审查 `unknown` | — |
| red-parent-malformed（`--revision 400db6611`） | 失败 | `stop_transfer_failed: native_identity_required` |
| red-parent-rejected（`--revision 400db6611`） | 失败 | 同上 |
| red-protocol-failure-unbound（只去掉协议失败路径的修复） | 失败 | 同上 |
| red-rejection-unbound（只去掉拒收路径的修复） | 失败 | 同上 |

回归，均为 PASS：

| 运行 | 项数 |
| --- | --- |
| t122-green（正常流程） | 23 |
| t124-restart-verified（Codex worker 与 reviewer） | 26 |
| t127-green | 19 |

夹具已归档，清单见 `fixtures.archive.json`。

## 真实运行，sonnet 5.5 medium（`../real/`）

用户要求实测一次：“你用 sonnet5.5 medium 试一试看有这个问题吗”，“既然不是模型的问题那就修，然后实测一次”。

- **构建**：从 `b3bd8aa84` 打包的测试版（`a2a.revision` 与之对应）。
- **脚本**：`real/t129run.sh` 与 `real/t129drive.mjs`，复制自 T-122 的实测脚本。只改了三处：
  - 描述文件改从 `<数据目录>-credentials/` 读（T-126）；
  - 模型改为 `claude-sonnet-5-5`、medium；
  - readback 多收 `stop_transfer_failed` 与 `review_*` 事件。
- **流程**：驱动经 CDP 扮演用户：
  1. 在项目终端里用用户自己的 `claude --model claude-sonnet-5-5 --effort medium`，登录照常；
  2. 让它申请执行主控，在界面点“批准”；
  3. 让它派一个 Claude worker（同模型、同强度），走完交付、验收（含独立审查）、打分、集成到 main。

结果（`real/real-01/`），PASS：

- **驱动检查**：5 项全过（`role_request_approved`、`sidebar_worker_under_controller`、`sidebar_reviewer_shown`、`task_accepted`、`hello_on_main`）；没有催促，没有工具批准提示；用时约 2.5 分钟。
- **审查与任务**：审查 `passed`，结论“可合并”；任务 `accepted`，`hello.txt` 在 main 上。
- **实际模型**：worker 与 reviewer 的启动记录都是 `claude-sonnet-5-5 / medium`；三个回合的实际回复模型（`native_turn_facts`）也都是 `claude-sonnet-5-5 / medium`。
- **T-129 症状**：没有出现 `stop_transfer_failed` 或 `review_protocol_failed`。这次真实 reviewer 交回的结论合规，所以走的是正常路径。失败路径的证据是上面的脚本化运行。
- **用户配置**：`~/.claude/settings.json`、`settings.local.json`、`~/.codex/config.toml` 前后一致（`user-config-compare.txt`：same）。

截图在归档盘。夹具归档时去掉了凭据目录，清单见 `real/real-01.archive.json`。

## 观察到的、本 ticket 之外的问题

真实运行里 worker 提交的尾注 `A2A-Model`、`A2A-Effort` 是 `unknown`，而同一回合的实际模型记录是 `claude-sonnet-5-5 / medium`。这不是本次回归：

- T-122 的真实运行 `gui-07`（haiku）也是 `unknown`；
- T-075 把它记为已知缺口，T-076 要求写实际值；
- Codex worker 的尾注写的是实际值（T-127 `gui-02`：`gpt-6.1-sol / low`）。

门禁核对模型用的是原生会话记录，不读尾注。是否另开 ticket 由用户决定。
