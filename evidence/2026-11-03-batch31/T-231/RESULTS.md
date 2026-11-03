# T-231 结果（2026-11-03，HEAD `3aaeb41e0` 加工作区改动）

结论：**PASS**（GPT 审查与复审对本票无阻塞，见 `../cu-review/`）。判断为测试过时；产品里有一个没有证据的时序风险，记在文末。

## 从哪次提交开始失败

`at-revision.sh` 把某个提交的 `workbench/src` 与测试导出到临时目录运行（不检出仓库）。`bisect.txt`：

- `f3a4a54162`（T-108，“unify turn trust and bind question permission events”）：9 个场景中 8 个失败；
- 它的父提交：0 个失败。

原因：此前 `signal()` 先扫描原生日志再核对钩子的会话（`JSON.parse(raw); this.scan(pane); check(value.session_id === pane.native, …)`）。`f3a4a54162` 把扫描移到会话核对之后。Codex worker 的 `pane.native` 只由扫描设置，测试里的钩子在任何扫描之前到达，于是被拒（`hook_native_session_mismatch`）。之后 T-157（`d9e948bba`）只给 Claude Code 恢复了核对前的扫描。

测试还过时了三处：

- T-221 起扫描只读 `sessions/YYYY/MM/DD`，测试把会话文件直接放在 `sessions/` 下；
- T-108 起 Codex 钩子必须带 `cwd`、`transcript_path`、`prompt`，且 `transcript_path` 与启动记录的真实路径一致；
- 后台启动时注入的 `recordUserSubmission` 在这个离线测试里没有。

## 改动

只改 `workbench/tests/test_native_final_read.ts`，产品代码不变：

- 临时目录取真实路径；会话文件写进当天的 `sessions/YYYY/MM/DD`（“另一个会话”的干扰文件也放在那里）；
- 写好会话前缀后，调用模拟终端的 `onData` 回调一次，与产品一样由终端输出触发扫描并绑定会话；
- `UserPromptSubmit` 钩子带上 `cwd`、`transcript_path`、`prompt`；
- 接上空的 `recordUserSubmission`（与 `test_t157_turn_identity.ts` 相同）。

断言没有改动。

## 证据

| 文件 | 结果 |
| --- | --- |
| `red-head-results.json` | 修改前，HEAD：8/9 失败，`hook_native_session_mismatch` |
| `green-results.json` | 修改后：9/9 通过 |
| `mutant-no-final-read-results.json` | 去掉退出前的最后一次读取（`this.scan(pane, true)`）：9/9 失败，失败信息是“必须包含最后完整上下文”或“最后读取须有一个明确结果” |

同一时刻的相关离线测试（`test_t157_turn_identity.ts`、`test_t207_interrupted_turn_hooks.ts`、`test_t221_codex_scan_days.ts`、`test_t078_two_turn_profile.ts`）在 HEAD 上都通过；本票没有改产品代码，它们不受影响。

## 命令

```bash
node workbench/tests/test_native_final_read.ts <新目录>
evidence/2026-11-03-batch31/T-231/mutant-no-final-read.sh <新目录>
evidence/2026-11-03-batch31/T-231/at-revision.sh f3a4a54162
evidence/2026-11-03-batch31/T-231/at-revision.sh f3a4a54162^
```

## 产品里的时序（第 1 轮审查后补的真实 CLI 探针）

审查（`../cu-review/REPORT.md`）指出：若真实 Codex 钩子在会话绑定之前到达，产品会同样拒绝，现有证据没有说明这个顺序会不会发生。

`probe_codex_hook_order.py` 在终端里运行真实 Codex CLI（0.164.0），参数取 worker 的 `UserPromptSubmit` 钩子写法（`-c hooks.UserPromptSubmit=…`、`--dangerously-bypass-hook-trust`）。模型地址是本机关闭的端口，`CODEX_HOME` 是 `/private/tmp` 下没有凭据的新目录，用完删除，没有供应商调用。三次结果（`codex-hook-order-{1,2,3}.json`）：

| 次 | 会话文件出现 `session_meta` | 钩子触发 | 钩子触发时文件里已有 `session_meta` | 两者之间的终端输出 |
| --- | --- | --- | --- | --- |
| 1 | 8.357 s | 8.447 s | 是 | 3 段 |
| 2 | 8.350 s | 8.420 s | 是 | 3 段 |
| 3 | 8.375 s | 8.448 s | 是 | 3 段 |

（时间从启动起算，提示词在约 8.3 s 输入；文件每 20 ms 检查一次。）

结论（按复审收窄）：三次隔离探针里，Codex 在提交提示词时才写出会话文件；约 70–90 ms 后探针的钩子脚本开始执行，其间每次都观察到终端输出。产品在每段终端输出时扫描（`panes.ts` 的 `onData`），这个顺序有利于会话在钩子到达前绑定。探针的局限：钩子时间是探针脚本开始执行的时间，不是产品收到信号的时间；`session_meta` 的出现时间是每 20 ms 轮询一次得到的；探针没有运行产品的扫描，也没有记录 `pane.native`。所以它说明测试里“钩子先于任何扫描”的构造与观察到的 Codex 行为不符，不证明真实产品里不存在这个竞争。70–90 ms 是这三次观察到的间隔，不是产品保证的余量；竞争记为已知风险，不改产品代码。
