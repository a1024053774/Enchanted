# T-172 发 0.1.3 Release 并更新 Pages（2026-10-24）

用户原话：“发新 Release 并更新页面”；“做完继续更新 github 以及 pages”。

## 结论：PASS

| 项 | 状态 | 依据 |
| --- | --- | --- |
| 版本号 | 0.1.3 | `workbench/package.json`、`package-lock.json` 顶部两处 |
| 产品页 | PASS（本地 `local-02` 与线上 `live-01` 各 44 项） | `page-check/check.mjs`，复制自 0.1.2，只加了浏览器路径 `PAGE_CHECK_CHROME` 与页面地址 `PAGE_CHECK_URL` 两个可选参数，检查项不变。红态 `local-01` 40/44：第一版“0.1.3 更新”一节过长，下载区高出一屏 40px，越过最后一步后滚不到页底；精简后通过 |
| 安装包 | PASS | `build.py r2`，在内置盘 `/private/tmp` 浅克隆 main 的 `f7b176e88` 后 `npm ci` + `npm run package:mac`；`CFBundleShortVersionString` 0.1.3，`codesign --verify --deep --strict` 通过。r1 失败：脚本只克隆 main，构建时候选还在分支上（`build-r1.json` 在外置盘），合并后重跑 |
| 推送 | PASS | 推送前扫描 `credential-scan-01.json`（origin/main..f7b176e88，10 个提交、35 个 blob，0 处命中、无凭据文件名）；diff 与提交说明里没有用户邮箱；无大文件。`15a444674..54dd554ce`，无 force push。扫描结果文件本身随后单独提交 |
| Release v0.1.3 | PASS | 目标 `f7b176e88`（安装包的源码版本），正文为 `release-notes.md`，附件 `Enchanted-0.1.3-macos-arm64.zip` 147,633,492 字节，下载回来逐字节相同；标为 Latest，v0.1.0～v0.1.2 保留 |
| Pages | PASS | 构建 `built 54dd554ce`，`https://a1024053774.github.io/Enchanted/` 返回 200，含“0.1.3 更新”；线上 44 项通过 |
| 清理 | PASS | 构建源码副本、应用副本、下载核对副本、T-171 测试夹具已删；安装包留在 `~/Downloads/Enchanted-0.1.3-macos-arm64.zip`。`~/Library/Caches/a2a-workbench`（electron-gyp 头文件）是构建前就有的共享缓存，保留 |

## 未做

- 没有替换 `/Applications/Enchanted.app`，也没有启动新包核对窗口：本票没有要求安装，新包与正在用的应用共用数据目录。
- 没有在手机真机上看页面；触摸只是 Chromium 模拟。

## 已知限制（写进发行说明与页面）

- T-163 的 M02 残余：应用内主控写的完成条件仍可能偏弱或写错。
- T-170 的“启动即失败可回收”只在模拟启动失败上验证过。

## 独立审查

`review-agy-01.md`（agy，gemini-3.8-flash-high，只读副本 `5d9917f85`）：PASS，逐条核对了发行说明与合并提交的对应关系。审查之后对 `check.mjs` 只加了 `PAGE_CHECK_URL`，未再审查。

## 复现

```sh
python3 evidence/2026-10-23-batch24/T-172/build.py <新标签>
python3 evidence/2026-10-23-batch21/release-0.1.2/credential_delta_scan.py <新输出路径>
python3 -m http.server 8765 --bind 127.0.0.1 -d docs &   # 本地
(cd workbench && node ../evidence/2026-10-23-batch24/T-172/page-check/check.mjs <目录>)
(cd workbench && PAGE_CHECK_URL=https://a1024053774.github.io/Enchanted/ node ../evidence/2026-10-23-batch24/T-172/page-check/check.mjs <目录>)
```

截图在外置盘，见 `shots-*.archive.json`。
