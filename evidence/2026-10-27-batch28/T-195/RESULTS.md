# T-195 结果：右键复制会话的 CLI 名、原生会话号与记录路径

日期：2026-10-27。状态：PASS（独立审查的完整 e2e 在审查沙箱里停在终端 Claude 报号处，见“独立审查”）。

## 改动

- 侧栏会话行右键菜单加“复制深度链接”，复制“<CLI 名> 会话 <CLI 自己的会话号>，记录 <记录路径>”；拿不到时置灰，悬停与菜单下方写明原因（`app/renderer.tsx`、`main.ts`、`preload.ts`、`style.css`）。点复制时重新查一次，链接变了或不可用就更新菜单、不复制。
- 后台命令 `native_link`（`src/nativeLink.ts`、`daemon.ts`）按 CLI 取“现在这个会话”的号：
  - 受管 Claude Code：后台启动时指定、窗格绑定的会话号；钩子报过别的会话号（窗格里 `/clear` 等）就置灰；记录文件须存在。
  - 受管 Codex：窗格从 rollout 首行 `session_meta` 绑定的线程号；Codex 记录里这个工作区自启动以来出现别的根线程，或有 rollout、日期目录读不了（只有目录不存在才算那天没写），就置灰。
  - 受管 agy worker：按独占工作区找唯一的会话文件；受管 opencode worker：OSC 7501 报来的号（一个窗格一个进程）。
  - 项目终端：Claude Code、Codex 的号由 Enchanted 钩子连同 CLI 进程号报来，前台换了进程就不再用；终端里的 agy、opencode 一律置灰（agy 不报号；opencode 的报告不带进程号，分不出来自哪一次运行）。
  - a2a 自造的 `osc7501:<launch>` 不当会话号给出。
- 事实：`findings/2026-10-27-native-session-ids.zh-CN.md`（四家的会话号来源、记录位置、续上参数）。README“窗格菜单”一段同步。

## 证据

测试：`workbench/tests/test_t195_native_link_e2e.py`。真实后台、socket 与门禁；Claude Code worker 与终端里的 Claude 是真实 CLI（模型换成本地脚本化接口）；Codex worker 是真实 Codex 与真实模型，用 /tmp 下隔离 CODEX_HOME（只复制 auth.json，只信任夹具仓库，结束删除，不入证据）。opencode、agy 在终端里用最小替身，记录库按两家真实格式建。预期来自 CLI 自己写的记录（jsonl 的 sessionId 与 cwd、rollout 首行 session_meta）。

| 文件 | 版本 | 结果 |
| --- | --- | --- |
| `red-4a5e1f3fc.json` | 修前 | 失败于 `native_link_answers`：没有这个命令 |
| `green-01`、`-02`、`-05`、`-07.json` | 开发中 | 各自失败，错误写在各文件的 `error` 字段（`-05` 是记录文件还没写出时就给了链接，随后改为须存在）；保留 |
| `green-03`、`-04.json` | v1 | 6 项 PASS |
| `red-ac78313.json` | v1，第 1 轮修后测试 | 失败于终端 Claude 报号 |
| `green-06.json` | v2 | 12 项 PASS |
| `red-b6c2600.json` | v2，第 2 轮修后测试 | 失败于受管 Claude `/clear` 后仍可用 |
| `green-08`、`-09.json` | v3 | 15 项 PASS |
| `red-v3-87c30f0.json` | v3，第 3 轮修后测试 | 失败于终端 opencode 置灰 |
| `green-10.json` | v4（`ed5a63b`） | 15 项 PASS |
| `green-11-with-t194-cand3.json` | v4 + T-194 v3（`0586985`） | 15 项 PASS |
| `red-v4-ed5a63b.json` | v4，第 4 轮修后测试 | 失败于看不进去的日期目录置灰 |
| `green-12-v5.json` | v5（`bf16c21`） | 16 项 PASS |
| `green-13-with-t194.json` | v5 + T-194（`d1989e9`） | 16 项 PASS |
| `mutant-*.json`（第 1～3 轮） | 变异 | 各在目标检查失败；`mutant-report-outlives-command.json` 第一次存活，去掉冗余复位后 `-02` 失败，均保留；v4 删掉了它所测的命令边界 |
| `mutant-v4-*.json` | v4 的五个变异 | 各在目标检查失败：受管 Claude 换会话、Codex 第二个根线程、终端 agy、Codex 启动前的旧 rollout、Codex rollout 读不了 |
| `mutant-v5-codex-unsearchable-day-skipped.json` | v5 的变异：看不进去的日期目录当成没写 | 失败于该场景 |
| `regression-t118_shell_env.json` | 回归 | 2 项 PASS |
| `regression-t121_role_request-*.json` | T-193 补丁的回归 | 见 T-193 RESULTS 的补丁一节 |
| `regression-t104_shell-*.json` | 回归 | 未通过，与本票无关，见下 |

复跑（`workbench/` 下）：

```sh
python3 tests/test_t195_native_link_e2e.py --summary <新路径>
python3 tests/test_t195_native_link_e2e.py --mutant codex-read-error-escapes --summary <新路径>
python3 tests/test_t195_native_link_e2e.py --revision 87c30f0 --summary <新路径>
```

### T-104 回归的归因

`tests/test_t104_shell_e2e.py` 在本票修前（`c7f2a92`，即 main `6b6be4f01` 加 T-193）与 v4 上就地运行，都失败于第 213 行：它要求终端 zsh 里以 `A2A_` 开头的变量只有 `A2A_PROJECT`，实际还有 `A2A_NODE`、`A2A_TERMINAL*` 等终端身份变量（T-119 起）。该测试最后改动于 2026-10-19，早于这些变量，是测试的期望过期，不是 T-195 引起的。早先的 `regression-t104_shell-base.json` 用 `--revision` 跑，该模式只复制 `workbench/src`、不复制 `workbench/terminal`，所以停在第 211 行（登录 shell），不能和就地运行比较；保留。就地运行：`regression-t104_shell-base-inplace.json`、`regression-t104_shell-v4.json`，夹具归档在外置盘 `a2a-evidence/2026-10-27-batch28/T-195/t104-archive-*`。

## 未覆盖

- 复制前重新查链接（审查第 3 轮 F2）没有界面自动化测试，只有代码；未做 Electron 实机界面检查。
- 受管 agy worker 的记录库读不了时置灰：v2 有对应检查（`mutant-unread-is-mismatch.json`），v3 起终端 agy 一律置灰后该场景不在当前测试里；代码路径未变。
- 真实 opencode、agy 只在事实调查里实测（见 findings）；本测试里两家是替身。
- 续上（`--session`、`--conversation`、`--resume`）未实测。

## 独立审查（Codex gpt-6.1-sol high，只读）

- 第 1 轮 `review-1.md`：NO_GO。会话变了仍给旧号（终端 `/clear`、CLI 退出）；同一终端第二次启动 opencode 继承上一次的号；agy 记录库读不了当成不匹配。
- 第 2 轮 `review-2.md`：NO_GO。受管 Claude `/clear`、受管 Codex 第二个根线程仍给绑定的号；终端 opencode 退出前的报告记到下一次；终端 agy 按目录猜。
- 第 3 轮 `review-3.md`：NO_GO。OSC 133 命令边界不等于 CLI 实例；复制用打开菜单时缓存的链接；新解析器跨块丢报告；Codex 读取错误逃逸；扫描不按启动时间过滤；T-104 归因不完整。
- 第 4 轮 `review-4.md`：NO_GO。日期目录的祖先不可搜索时被当成“那天没写”，反而恢复旧链接（P2）；事实文档事件名（P3）。
- 第 5 轮 `review-5.md`：两项均在根因层关闭，没有新发现；同文件其余读取分支未见“读不了时恢复旧链接”的路径。状态写 INCOMPLETE，因为审查者在自己环境里跑候选的完整 e2e，前 8 项通过后等终端 Claude 报会话号超时（第 4 轮同样）。

审查环境的超时归因：审查者的同一脚本（`/private/tmp/t195-review5/run-frozen-e2e.py`，只把临时目录改到审查目录）在同一冻结候选上、审查沙箱外运行，16 项 PASS（`review5-script-outside-sandbox.json`）。另有 `green-10`～`-13` 四次完整运行通过。所以超时来自审查环境，不是候选的行为；沙箱里具体是哪一步挡住了终端 Claude 的钩子没有查明。
