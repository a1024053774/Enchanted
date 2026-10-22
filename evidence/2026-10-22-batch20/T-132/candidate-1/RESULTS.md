# T-132 候选 1 结果

- **候选**：`dc4d2e257`；测试夹具修正 `07dc957c3`；README `ea68df9d9`。
- **修前版本**：`85b212a60`。
- **结论**：**PASS**（待独立审查）。

## 改了什么

- **`workbench/app/IssuesPage.tsx`、`records.css`**：新增“问题”页，列出所选项目各任务的问题上报，每三秒读一次。
  - 每条显示：任务与编号、标题、状态、是否阻塞、上报者与时间、正文、答复与处置记录。
  - 可做的操作：答复、稍后再看、关闭（关闭时要填原因与依据）。
  - 读取失败时显示“问题列表读取失败”，不显示为空列表。
- **`workbench/app/main.ts`、`preload.ts`**：新增 `a2a:issues`、`a2a:issue-answer`、`a2a:issue-dispose` 三个入口，都经桌面应用的操作员凭据调用门禁已有的 `issues`、`answer_issue`、`disposition`。任一任务读取失败，整份列表就报失败。
- **`workbench/app/renderer.tsx`**：页签里加“问题”，项目行和页签提示“等你决定”的问题数。
- **`workbench/src/daemon.ts`**：改了两处。
  - 侧栏快照给每个项目带上 `issues_waiting`，即门禁状态为“等你决定”的问题数。
  - 操作员发出的 `disposition` 记为 `user`。理由：T-126 之后，只有桌面应用持有操作员凭据。门禁规定阻塞问题只有用户能关，原来记为 executor，界面关不掉阻塞问题，试跑时被拒（`blocking_requires_user`）。其他命令仍按 executor 记。
- **测试夹具**：`tests/scripted_claude.py`、`cdp.mjs`、`cdp_launch.cjs`，从 T-132 起共用。夹具包括真实后台、经批准的终端主控、真实 Claude Code worker（模型是本地脚本化接口）、从被测源码构建的 Electron 窗口，测试经 DevTools 协议操作这个窗口。

## 端到端（`e2e/commands.sh`）

场景如下：

1. worker 经门禁上报两条问题，一条非阻塞，一条阻塞；
2. 打开窗口，选中项目；
3. 核对提示与列表；
4. 在界面里答复非阻塞的那条；
5. 填写原因与依据，关闭阻塞的那条；
6. 停掉后台，看页面怎么显示。

期望值来自 ticket 与门禁既有规则。

| 运行 | 结果 | 失败于 |
| --- | --- | --- |
| green | PASS，5 项 | — |
| red-parent（`--revision 85b212a60`） | 失败 | 项目行提示超时：修前没有问题提示与问题页 |
| mutant-error-shown-as-empty（读取失败时清空列表） | 失败 | 读取失败提示超时 |
| mutant-disposition-as-executor（处置仍记为 executor） | 失败 | 关闭记入门禁超时 |
| t122-green（T-122 正常流程回归，后台有改动） | PASS，23 项 | — |

第一次跑上表中三个“从源码副本构建”的运行时，副本里缺 `LICENSE.synara`，三次都在构建阶段失败，现场保留在 `e2e/harness-failure-01/`。夹具修正后重跑，结果如上表。

green 的读回：

- **提示**：项目行和页签都显示 1。门禁状态：阻塞的那条为“等你决定”，非阻塞的为“待判断”（新报的非阻塞问题 15 分钟内是这个状态）。
- **答复**：答复送到 worker 会话（脚本化接口收到含答复原文的新一轮请求）；门禁记下一条 `answer` 用户输入，`channel` 为 `issue-panel`，指向 worker 会话。
- **关闭**：处置为 `close`，`from` 为 `user`，原因与依据和界面填写的一致；两条记录都还在；项目行和页签的提示随之消失。
- **读取失败**：停掉后台后，页面显示“问题列表读取失败”，没有出现“还没有问题上报”。

截图（01 列表、02 答复与关闭后、03 读取失败）在各夹具的 `out/` 目录里，已归档到外置盘，见 `fixtures.archive.json`。

## 未覆盖

- “稍后再看”没有单独跑端到端，它与关闭走同一入口。
- 打包后的应用（/Applications）没有在本票重装。
