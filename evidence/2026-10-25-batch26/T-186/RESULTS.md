# T-186 结果：发 0.1.4 Release 并更新产品页

## 状态：PASS（Release、产品页、Chrome 复看、替换 /Applications、真实应用复看全部完成）

## 依据

ticket T-186（ready_rev 1）。用户 2026-10-25 原话：“1. 查明一下 3.装上钩子  5.发新 release,产品页也更新  新票:增加 antigravity,opencode 的支持吧,按理说应该不限 cli 的,但应该还要实测一下,”。替换 /Applications：用户选 A，“A 同意停后台并替换 (Recommended)”（inbox 20261025T135441Z-ideation-answer-001）。

## 已完成

| 项 | 状态 | 依据 |
| --- | --- | --- |
| 版本号 | 0.1.4 | `workbench/package.json` 与 `package-lock.json` 顶部两处 |
| 发行说明与产品页 | PASS | `release-notes.md`；`docs/index.html` 的“0.1.3 更新”换成“0.1.4 更新”。按构思主控的要求，两处都写了：Codex 用户第一次启动新版会弹一次钩子信任框，需要本人确认 |
| 安装包 | PASS | `build.py r2`：在内置盘 `/private/tmp` 浅克隆 main 的 `071fafb35`，然后 `npm ci` + `npm run package:mac`。`CFBundleShortVersionString` 0.1.4；`codesign --verify --deep --strict` 通过（ad-hoc）；`spctl` 拒绝，因为没有经过 Apple 公证，与之前各版相同。包里有 T-184 的 `processArgs.py`、`terminalClis.ts`，Codex 包装脚本带 `session-context`。r1 失败：脚本从 worktree 运行，取到的是合并前的提交，main 的浅克隆里没有它；失败记录 `build-r1.json` 在外置盘。改从主 checkout 运行 |
| 推送 | PASS | 推送前扫描 `credential-scan-01.json`（origin/main..071fafb35，25 个提交、85 个 blob，0 处命中，没有凭据文件名）；提交里没有用户邮箱；没有大于 1 MB 的文件。`a5f8c86d1..b0ecd83ce`，没有 force push |
| Release v0.1.4 | PASS | 目标 `071fafb35`（安装包的源码版本）；正文为 `release-notes.md`；附件 `Enchanted-0.1.4-macos-arm64.zip` 147,467,849 字节，下载回来逐字节相同；标为 Latest，v0.1.0～v0.1.3 保留 |
| Pages | PASS | 构建 `built b0ecd83ce`；`https://a1024053774.github.io/Enchanted/` 返回 200，含“0.1.4 更新” |
| 页面检查 | PASS | 用 T-182 的 `check.mjs`（原样复制）：本地 `local-01` 43/43，线上 `live-01` 43/43。截图在外置盘，见 `shots-*.archive.json` |

## 没做

- lcu 在 Chrome 里复看线上产品页：lcu 报 `Sky Computer Use native pipe startup failed`，重置后仍然不可用。
- 替换 /Applications，从 Dock 启动后做真实应用复看（T-184 的第三条验收也在这一步核对）：同样要用 lcu 操作界面，还没做。0.1.3 后台（pid 61281）还没有停。

## 独立审查

agy 审查候选（版本号、页面、发行说明）：`T-186 REVIEW PASS`。一项 P3：产品页的“已知限制”没写“没接入检测只认程序名 claude/codex”。发行说明的已知限制里已经写了，产品页保持简短，不改。全文 `review-agy-01.md`。审查期间 agy 反复猜 ticket 文件名、读不到文件，后来把准确文件名发给了它。

## 2026-10-25 晚：lcu 复看与替换（用户已选 A）

- Chrome 复看产品页：PASS。“0.1.4 更新”一节显示正常（`page-chrome-0.1.4.jpg`）。
- 0.1.3 后台（pid 61281）复看时已不在运行。从 Release 下载 0.1.4 安装包，替换 `/Applications/Enchanted.app`（CFBundleShortVersionString 0.1.4），解除隔离。0.1.3 包暂存在执行主控 scratchpad，复看通过后删除。
- 第一次启动：lcu 选不到 Dock（超时），我用 `open -a` 启动。结果应用和后台继承了我这个会话的环境变量（`HERDR_PANE_ID`、`AI_AGENT` 等），不等于从 Dock 启动，作废。随后用 SIGTERM 停掉这个后台，再用 `env -i open -a` 重新启动；核对应用与后台进程都不带上述变量。
- 在测试项目 a2a-lcu-demo（原目录已清理，重建为空仓库）新建终端，输入 `claude --model claude-haiku-5-5`：claude 一直没有任何输出，窗格提示“启动后还没有任何输出。它可能在等 macOS 的权限弹窗”。
- 排查（都没有发出真实提示）：
  - `claude --version` 在窗格里正常。
  - 同一份环境在我自己的 PTY 里能正常画出界面；在窗格里套一层新 PTY 仍然 0 字节。说明原因在“进程由 Enchanted 启动”，不在窗格的 PTY。
  - 钥匙串读取正常（0.02 秒，退出码 0）。
  - `claude --debug` 停在 “Loading skills from … user=~/.claude/skills”。用户的多个 skill 是指向 `~/Documents/SKILLS` 的符号链接。
- 结论：读取“文稿”文件夹需要 macOS 的文件与文件夹授权，按启动它的应用（Enchanted）计算。0.1.4 是新的二进制，0.1.3 时的授权不沿用，claude 停在等授权。按用户规则，隐私授权交用户，不代批；lcu 也不允许读系统弹窗。
- 发现：每次发版换二进制都会让这项授权重新弹一次，窗格提示已能说明原因。要让授权跨版本保留，需要稳定的代码签名身份（目前是 ad-hoc 签名）。这一点只记录，不在 T-186 范围内改。
- T-184 第三条验收的部分证据：用绝对路径启动 claude 时，窗格显示“这个会话没接入 Enchanted……”，侧栏状态为“未知”。

## 用户授权后的复看（2026-10-25 21:22）

- 用户在系统里允许了 Enchanted 访问“文稿”（用户原话：“可以了,我已同意”）。等待中的 claude 随即画出界面。
- 普通终端：发 1 条 Haiku 提示“只回复两个字：收到”，回复“收到”。
- 第 2 条 Haiku 提示让它申请执行主控：它加载 a2a skill，运行 `a2a whoami`、`a2a request executor`；界面出现申请，写明“a2a-lcu-demo 的第 2 个窗格里的 claude 申请成为执行主控”。我在测试项目里点了批准；它回复“已就绪”，侧栏与窗格头都是“执行主控 … 空闲”。
- 第 3 条 Haiku 提示“只回复：好”：侧栏与窗格头同时由“空闲”变为“运行中”，再回到“空闲”。后台事件：`terminal_turn` UserPromptSubmit → running（seq 30977），Stop → idle（seq 30978）。
- 真实提示共 3 条，模型都是 claude-haiku-5-5。0.1.3 安装包备份已删除。测试 claude 已 /exit。
