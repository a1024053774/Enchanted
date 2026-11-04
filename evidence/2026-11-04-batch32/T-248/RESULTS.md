# T-248 结果：发 0.1.6

日期：2026-11-04。用户原话：“构建并打包发布新版本,更新 release,也更新产品页 a1024053774.github.io/enchanted”。总体：**PASS**。

| 项 | 结果 | 证据 |
| --- | --- | --- |
| 版本号 | PASS | 提交 `4ec534bed`：`workbench/package.json` 与 `package-lock.json` 改为 0.1.6 |
| 构建 | PASS | `build.py r1`：从 `4ec534bed` 的干净浅克隆用 `npm ci` 与 `npm run package:mac` 构建；摘要 `build-r1.json`（Electron 43.4.1，arm64，ad-hoc，内带 hc 0.1.15） |
| 安装包核对 | PASS | `verify-r1.txt`：Info.plist 版本 0.1.6，包内 revision 为 `4ec534bed`；`codesign --verify --deep --strict` 通过；`spctl` 按预期拒绝（未公证）；内带 `hc --version` 为 0.1.15。zip 解压后重新 codesign 核对通过 |
| 安装包冒烟 | PASS | `smoke.mjs`，记录 `smoke-r8.json`：经 LaunchServices 以隔离的状态目录启动安装包，开项目、经渲染进程的“新终端”接口开项目终端，键入 `echo T248-$((6*7))-$PWD`，读回 `T248-42-<项目目录>`（42 由 shell 计算，不是键入的字面值）；ps 显示终端由包内 `Contents/Resources/app/hc/herdr-core` 托管。结束后停掉本次后台与私有 core，没有残留进程 |
| Release v0.1.6 | PASS | 目标 `4ec534bed`，正文 `release-notes.md`，附件 `Enchanted-0.1.6-macos-arm64.zip` 150,136,456 字节，下载回来逐字节相同；标为 Latest，v0.1.0～v0.1.5 保留 |
| push | PASS | 推送前扫描 `cfcfd520d..HEAD` 的新增行（204,663 行）：用户邮箱、agy 账号邮箱、zoeyyan49、各类密钥格式 0 命中，大于 1 MB 的文件 0 个；以 HTTPS 推送 `cfcfd520d..1374ba589`，不是 force push |
| 产品页 | PASS | Pages 构建 `1374ba589` 为 built；`https://a1024053774.github.io/Enchanted/` 200，显示“0.1.6 更新”与 v0.1.6 链接；页面检查本地 `page-check/local-01` 43/43、线上 `page-check/live-01` 43/43，无控制台错误 |

## 与字面不同的地方

- 用户写的小写网址 `https://a1024053774.github.io/enchanted/` 返回 404：GitHub Pages 的项目路径区分大小写，仓库名是 `Enchanted`。小写网址上的检查记录保留在 `page-check/live-lowercase-01`（23 项里 2 项通过，整页 404）。这次没有加小写跳转。
- 页面检查脚本从 T-188 复制，只改了浏览器启动方式。本机已经没有 playwright 的 Chrome for Testing；Chrome 156 正式版在无头模式下启动 31 秒后会自己退出（退出码 0，5 次探针都复现：经 playwright、经 CDP 连接、直接启动，沙箱内外结果相同）。所以改为有界面运行，窗口放在屏幕外。检查项没有改。
- 冒烟 r1～r7 失败，都是脚本本身的错误，记录保留：窗格还没接上就输入、输出上限超出、读错字段名、取错 project id。r8 修正后通过。
- 没有替换 /Applications，用户这次没有要求。

## 清理

已删除临时目录：构建槽 `/private/tmp/a2a-build-release016-r1`（412 MB）、源码与 npm 缓存 `/private/tmp/release016-build-r1`（1.3 GB）、zip 和下载副本（共 289 MB）。安装包只保留在 Release 里。页面截图只留在会话的临时目录里，没有放进仓库。
