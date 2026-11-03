# T-236 / T-238 关闭审查请求（只读）

你是独立审查员，只读：不改任何文件，不运行会改动仓库或用户环境的命令，不启动 Enchanted 或任何 CLI，不 push。结论作为你的最后一条回复（会被保存为 `T-236/reviews/REVIEW-01.md`），中文。

## 要审的结论

主控准备以“不是 Enchanted 代码缺陷，附依据关闭”关闭两张票：
- `.project-map/tickets/T-236-claude-fullscreen-renderer-hangs-in-terminal.md`：项目终端里 Claude Code 没有任何输出。
- `.project-map/tickets/T-238-codex-agy-first-prompt-never-runs.md`：项目终端里 Codex 输入排队、agy 一直 working。

主控的结论：Enchanted 应用（`org.a2a.workbench`，ad-hoc 签名）没有 macOS“文稿”文件夹授权，它的一个授权请求一直没人回答；挂着时，需要 TCC 判定的进程打开 `~/Documents` 下的文件都停在内核 `open` 上（Claude 加载 `~/Documents/SKILLS` 下的 skill、Codex/agy 读目录都卡在这里）。用户回答授权框后全部恢复。唯一的仓库改动是 `workbench/README.md` 加一段说明（`T-236/reviews/readme.diff`）。

## 证据

- 第 3 轮结果：`evidence/2026-11-02-batch30/T-236/r3/RESULTS.md`（11-02 的观察、11-03 更正，以及授权后的复测）与同目录的探针脚本、`cache-probe-*.json`、`lprobe*.out`、`tcc-stream-1.summary.txt`。
- 更早的记录：`T-236/RESULTS.md`（第 1、2 版，含被否定的推测）、`T-238/REPORT-02.md`（Codex 第 2 轮）。
- 授权前 Computer Use：`cu-t239/REPORT.md` 场景 B（三家都不回复）。授权后 Computer Use：`cu-cli-r2/REPORT.md`（三家都回复“测试正常。”）。

## 请重点看

1. 证据能否支持“卡在 TCC 授权请求、不是 Enchanted 代码缺陷”；有没有别的解释同样符合所有观察（例如 11:26–11:29 那段正常、按目录区分的 `com.apple.macl`、launchd 独立进程授权前卡住授权后立即 EPERM）。
2. 两张票的验收条目是否可以按“附依据关闭”处理；T-236 原验收建立在已被否定的“全屏渲染器”推测上，T-238 要求“是 Enchanted 问题就修，不是就附依据关闭”。
3. 有没有 Enchanted 应该做而没做的事（例如声明 `NSDocumentsFolderUsageDescription`、在界面上提示、检测卡住），以及不做的理由是否站得住。README 新段落是否准确。
4. 证据里的措辞是否把推断写成了事实。

每条意见标明：阻塞 / 非阻塞，给出文件与行号。最后给结论：PASS（可以关闭，无阻塞意见）或 NO_GO。
