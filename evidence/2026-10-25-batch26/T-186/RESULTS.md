# T-186 结果：发 0.1.4 Release 并更新产品页

## 状态：INCOMPLETE（Release、产品页与线上检查已完成；lcu 在 Chrome 复看、替换 /Applications 后的真实应用复看还没做：lcu 当前不可用）

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
