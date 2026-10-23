# T-133 Codex 一侧（方案 A）与 T-107 #3 候选 4 结果

- **来源**：用户 2026-10-22 逐字：“1. A 2. 一二都要.”。
- **候选**：代码与测试 `d0c006ee1`。修前版本 `d0f89b48a`。
- **结论**：**PASS**。独立审查 `review-01.md`（agy gemini-3.8-flash-high）PASS：1 条 P2、3 条 P3，没有 P0/P1，处理见下。

## 相对候选 3 的改动（`../candidate-3/RESULTS.md`）

- **后台**：删掉“Codex 的 PostToolUse 不算答复”的判断。包装脚本不给 Codex 传 PostToolUse，这条判断走不到；候选 3 的变异因此存活。包装脚本里注明不传 PostToolUse 的原因：Codex 的提问工具在用户答复之前就返回，答复作为一次提交到达。
- **Codex 测试**：
  - 变异改为 `post-hook-passed`，即包装脚本像 Claude 插件那样多传一个 PostToolUse。
  - “提示信任”要求屏幕是复数的 “hooks are new or changed”：Enchanted 的钩子加用户自己的。只有用户自己的钩子时，Codex 写的是 “1 hook is new or changed”。
- **Claude 测试**：修好“答复之后不再等待主控回答”那段 JS 的大括号。

## 端到端（`e2e/commands.sh`）

| 运行 | 结果 | 失败于 |
| --- | --- | --- |
| codex-green | PASS，14 项 | — |
| codex-red-parent（`d0f89b48a`） | 失败 | `codex_asks_to_trust_the_hooks`：屏幕是 “1 hook is new or changed”，只有用户自己的钩子 |
| codex-mutant-hooks-not-passed | 失败 | 同上 |
| codex-mutant-post-hook-passed | 失败 | 超时：问用户时侧栏没出现“等待用户回答”。PostToolUse 紧跟 PreToolUse 到达，状态立刻回到“运行中” |
| codex-mutant-reply-as-message | 失败 | `only_approved_prompts_recorded`：答复记成了消息 |
| claude-green | PASS，13 项（含 T-107 #3 的两项） | — |
| claude-mutant-issue-not-waiting | 失败 | 超时：上报未答复时不是“等待主控回答” |
| claude-red-parent（`d0f89b48a`） | 失败 | 同上 |
| t107-live-green | PASS，7 项 | — |
| t133-t134-green | PASS，14 项 | — |

- **没有重跑**：t132 与 t124（Codex 主控）。两者在候选 3 上都 PASS，它们走到的代码（侧栏、门禁）在那之后没有改动。
- **Codex green 核对了什么**：
  - 用户点信任之前，配置里没有 hooks 条目；点了之后 Codex 自己写下三个 `<session-flags>` 信任条目；第二个终端不再要求信任。
  - 用户自己 `hooks.json` 的钩子照常收到每次提交。
  - 记下的只有批准后的两句和“先做哪一个？：T-1 先做”。
  - 提问工具返回 accepted、模型进入等待后 4 秒仍是“等待用户回答”；答复后是“运行中”，回合结束后是“空闲”。
  - 执行主控挂在构思主控下。
- **截图**：在归档夹具的 `out/` 里。
- **夹具**：已归档，见 `e2e/fixtures.archive.json`。

## 未覆盖与已知边界

- **用户真实环境**：
  - 没有在用户自己的 `~/.codex` 里跑过：信任那一步要用户亲手点。测试用的是隔离 home、本地脚本化模型，Codex 是真的。
  - 用户真实启动 Codex 时用默认沙箱与审批，`a2a request` 在那种设置下是否被沙箱挡住没有验证；测试里夹具用户用的是 `--sandbox danger-full-access -a never`。
- **已知缺口**（README 与侧栏缺口说明里都写了）：
  - Plan 模式下的同步提问 `request_user_input` 不显示等待，答复也不记。
  - 被 Esc 中断后 Codex 不发 Stop，一直显示“运行中”，直到下一次提交（probe-06）。

## 独立审查的处理

| 发现 | 处理 |
| --- | --- |
| P2：Codex 普通提交的去重键是随机 id，钩子若被重放会重复记录 | 不改。Codex 的提交没有自己的 id，`turn_id` 与答复共用，没有可用的稳定键。探针里每次提交只触发一次钩子；Codex 会不会重放钩子没有验证。README 写明“每次钩子调用记一条” |
| P3：侧栏逐个任务串行读上报 | 不改。本地 SQLite 读取，量与任务数同级 |
| P3：“答复之后”只检查不再是“等待主控回答” | 不改。这条检查要证明的就是离开这个状态；实测是“空闲”（`claude-green.json`） |
| P3：`codexQuestionReply` 不核对每项字段的类型 | 不改，记为已知边界。实测 Codex 每项都带 `question`、`answer`（probe-05）。真缺字段时会记出 “undefined：…” 这样的答复；整体解析不了时，才整条记成原文消息 |
