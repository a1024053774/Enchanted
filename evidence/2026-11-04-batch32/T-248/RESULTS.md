# T-248 结果：发 0.1.6

日期：2026-11-04。用户原话：“构建并打包发布新版本,更新 release,也更新产品页 a1024053774.github.io/enchanted”。总体：**PASS**。

| 项 | 结果 | 证据 |
| --- | --- | --- |
| 版本号 | PASS | 提交 `4ec534bed`：`workbench/package.json` 与 `package-lock.json` 改为 0.1.6 |
| 构建 | PASS | `build.py r1`：从 `4ec534bed` 的干净浅克隆用 `npm ci` 与 `npm run package:mac` 构建；摘要 `build-r1.json`（Electron 43.4.1，arm64，ad-hoc，内带 hc 0.1.15） |
| 安装包核对 | PASS | `verify-r1.txt`：Info.plist 版本 0.1.6，包内 revision 为 `4ec534bed`；`codesign --verify --deep --strict` 通过；`spctl` 按预期拒绝（未公证）；内带 `hc --version` 为 0.1.15。zip 解压后重新 codesign 核对通过 |
| 安装包冒烟 | PASS | `smoke.mjs`，记录 `smoke-r8.json`：经 LaunchServices 以隔离的状态目录启动安装包，开项目、经渲染进程的“新终端”接口开项目终端，键入 `echo T248-$((6*7))-$PWD`，读回 `T248-42-<项目目录>`（42 由 shell 计算，不是键入的字面值）；ps 显示终端由包内 `Contents/Resources/app/hc/herdr-core` 托管。结束后停掉本次后台与私有 core，没有残留进程 |
| Release v0.1.6 | PASS | 目标 `4ec534bed`，正文 `release-notes.md`，附件 `Enchanted-0.1.6-macos-arm64.zip` 150,136,456 字节，下载回来逐字节相同；标为 Latest，v0.1.0～v0.1.5 保留 |
| push | PASS | 推送前扫描 `cfcfd520d..HEAD` 的新增行（204,663 行）：用户邮箱、agy 账号邮箱、另一个受保护的账号名、各类密钥格式 0 命中，大于 1 MB 的文件 0 个；以 HTTPS 推送 `cfcfd520d..1374ba589`，不是 force push |
| 产品页 | PASS | Pages 构建 `1374ba589` 为 built；`https://a1024053774.github.io/Enchanted/` 200，显示“0.1.6 更新”与 v0.1.6 链接；页面检查本地 `page-check/local-01` 43/43、线上 `page-check/live-01` 43/43，无控制台错误 |

## 与字面不同的地方

- 用户写的小写网址 `https://a1024053774.github.io/enchanted/` 返回 404：GitHub Pages 的项目路径区分大小写，仓库名是 `Enchanted`。小写网址上的检查记录保留在 `page-check/live-lowercase-01`（23 项里 2 项通过，整页 404）。之后用户回复“加跳转”，见下文“小写网址跳转”一节。
- 页面检查脚本从 T-188 复制，只改了浏览器启动方式。本机已经没有 playwright 的 Chrome for Testing；Chrome 156 正式版在无头模式下启动 31 秒后会自己退出（退出码 0，5 次探针都复现：经 playwright、经 CDP 连接、直接启动，沙箱内外结果相同）。所以改为有界面运行，窗口放在屏幕外。检查项没有改。
- 冒烟 r1～r7 失败，都是脚本本身的错误，记录保留：窗格还没接上就输入、输出上限超出、读错字段名、取错 project id。r8 修正后通过。
- 没有替换 /Applications，用户这次没有要求。

## 清理

已删除临时目录：构建槽 `/private/tmp/a2a-build-release016-r1`（412 MB）、源码与 npm 缓存 `/private/tmp/release016-build-r1`（1.3 GB）、zip 和下载副本（共 289 MB）。安装包只保留在 Release 里。页面截图只留在会话的临时目录里，没有放进仓库。

## 小写网址跳转（用户 2026-11-04：“加跳转”）

- 做法：在个人站仓库 `a1024053774/a1024053774.github.io` 加了静态页 `enchanted/index.html`，提交为 `ade73f2`。小写路径 `/enchanted/` 不属于任何项目站，由个人站提供。这个页面用 `location.replace` 跳转到 `/Enchanted/`，并保留 `#` 后的锚点；关掉 JS 时由 meta refresh 跳转。页面还设了 canonical 和 noindex。
- 本地核对：Jekyll 构建后页面原样复制到 `_site/enchanted/index.html`。个人站 CI 的五项 Python 检查各跑一次，全部 PASS。从本地服务器打开 `/enchanted/#download`，开 JS 时落到 `https://a1024053774.github.io/Enchanted/#download`，关 JS 时落到 `/Enchanted/`。
- 没在本机跑：CI 的 `test:reading`（Playwright 的 WebKit 与 Chromium 阅读检查），因为本机没有这两个浏览器。这次改动也不涉及阅读页面；该检查由推送后的 CI 运行。
- 线上：个人站 CI run 41855244681 的 build（含 `test:reading`）与 deploy 都是 success。`https://a1024053774.github.io/enchanted/` 返回 200，浏览器打开 `/enchanted/#download` 落到 `/Enchanted/#download`。
