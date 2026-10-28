# 真实用户式试用 第 3 轮（2026-10-28）

用户：“然后你在用 terra 操作一下,特别是我们产品页宣称的功能最起码都要能正常使用吧”。

状态：BLOCKED。第一次运行（3a）没能建立主控：终端里的 CLI 都停在 macOS 的“文稿”授权上，这个授权要用户本人在系统弹窗里点。产品页的说法只核到不依赖 agent 的部分。

## 做法

- 被测：`main` `d4f68e349`（含 T-203、T-206）。打包命令 `node app/package.mjs --slot uat03 --variant test`。
- 隔离目录：状态 `/private/tmp/uat3/state`，界面数据 `/private/tmp/uat3/ui`。
- 夹具：`todo-cli`、`word-count` 两个新仓库，都有写在 README 里的已知问题。
- 试用者：Codex `gpt-6.1-terra` high，用 Computer Use 按 `BRIEF.md` 操作。BRIEF 末尾摘了产品页（`docs/index.html`）的每条说法，要求逐条核对。
- 报告原文 `REPORT-3a.md`；截图在外置盘，清单见 `ui-check-3a.archive.json`。
- 开始前停掉了第 2 轮留下的 Enchanted Test（uat01 包）、它的 agent 进程和第 2 轮的 terra 会话，免得两个同 bundle id 的应用混在一起。

## 3a 的结果

| 说法 | 结果 |
| --- | --- |
| 设置里按角色改模型、思考强度、Fast；浅色深色切换 | 保存与切换都能用；新会话是否用上没验证（没派出会话） |
| 项目普通终端：分屏、放大、还原；在里面打字不记人工介入 | 能用（记录页仍为空） |
| 侧栏项目、分支 | 显示 `main · 无上游`；夹具没有上游，领先/落后数没验证；没有主控树，折叠汇总没验证 |
| 流程、问题、记录、指标、回看页 | 都能打开，空状态说明看得懂；没有数据，泳道、回线、问题卡、筛选、unknown 行都没验证 |
| 主控申请、建卡、派发、人工介入（整句记录、Esc 不记）、原生提问、审查（`review_submit`）、集成、门禁 Git 元数据检查 | 没试成：没有 CLI 能当上主控 |

## CLI 停住的原因

- Claude：三次启动都没有输出。应用显示了 T-202 的提示（“可能在等 macOS 的权限弹窗（例如‘想访问“文稿”文件夹’）……”）。
- Codex：界面画出来了，但请求停在 `Queued follow-up inputs`。
- 用户的 `~/.claude/skills`、`~/.agents/skills` 里有链接指向 `~/Documents/SKILLS`。第 1 轮已用 tccd 日志证实：Claude 以 Enchanted Test 为责任进程请求“文稿”授权（`UAT-01/RESULTS.md`）。uat03 是新的 ad-hoc 签名身份，旧授权不继承，所以又要授权一次。
- 本轮没能读到 tccd 日志（`log show` 没有返回 TCC 条目），Codex、opencode 停住是否同因，是推断，没有核实。
- 另两项不是缺陷：
  - Codex 的 “Hooks need review”：试用者选了不信任。README 写明这是 Enchanted 给项目终端里的 Codex 挂的钩子，要选 “Trust all and continue”，否则状态报不上来。BRIEF 没写清楚，下次补上。
  - agy 的信任框：试用者按 BRIEF 选了退出。项目终端里由用户自己启动的 agy 要用户自己选信任；只有 worker 的信任由后台处理。BRIEF 写得有歧义。
- opencode 提示 `Connect an integration to send prompts`、`No integrations available`：原因没查清，可能同样是读不到用户目录下的配置，也可能是别的问题。第 2 次运行再看。

## 没有新开缺陷票

3a 没观察到能确认的产品缺陷；上面的停住都指向系统授权或 BRIEF 的写法。

## 继续的条件

用户在系统弹窗里（或“系统设置 → 隐私与安全性 → 文件与文件夹”）允许 Enchanted Test 访问“文稿”后，用同一个包（uat03）跑 3b：
- BRIEF 补上 Codex 钩子选 “Trust all and continue”、项目终端里的 agy 可以选信任（只限夹具目录）；
- 先走主路径，再补 3a 没验证的说法。
