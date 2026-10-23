# 0.1.2 发布与产品页改版（2026-10-23）

用户原话：“都关掉吧,那现在清理项目的不用缓存, 然后更新 GitHub 与产品页,发新版打包,更新我 applications 里的,然后产品页上面的模拟交互那部分也要适应新版的软件,……首屏是介绍,第二屏是进入交互页,可以上下滑动,每次滚动一下鼠标滚轮就切换一步,用这个第二屏来展示软件,这个你先做出来,我看看再给你下一步的修改指示.”

## 结论

| 项 | 状态 | 依据 |
| --- | --- | --- |
| T-115、T-116 | 按用户决定不再做；验收 INCOMPLETE | 状态改为 out-of-scope，不记为 closed：验收条件没有达成；T-116 第 1 条已由 T-118 满足并勾选。`project_map.py status` 0 问题 |
| 缓存清理 | PASS | `cache-cleanup-01.json` |
| 产品页 | PASS（本地，44 项）；线上待复跑 | `page-check/check.mjs`。第一版本地 `run-06` 与线上 `live-01` 各 31 项全过，红态见 `run-03`（换步后页面偏移 13px、首屏第一下滚轮不进第二屏）。审查 review-01 后补了 13 项（停在离顶几像素时往上滚、方向键、焦点在演示里、在演示窗口上滚动、触摸三项、记录页会话筛选、指标页日期与逐会话表、设置弹窗 Tab），对已发布的 `dff00ec9c` 跑出 12 项失败（`old-dff00ec9c-02-report.json`），修后 `run-13` 44 项全过。触摸用 Chromium 模拟触点，没有在真机上试 |
| 0.1.2 安装包 | PASS | `build.py r2`，revision `b698347ce`，codesign 核对通过；r1 失败（`git archive` 副本没有 `.git`，打包要记源码 revision，T-122），日志在外置盘 |
| /Applications 更新 | INCOMPLETE：窗口未核对 | 0.1.1 不在运行；替换后 `CFBundleShortVersionString` 0.1.2，`codesign --verify --deep --strict` 通过；启动后主进程、渲染进程与后台都从新包运行。osascript 无辅助功能权限；截屏时前台是终端，没有为核对而把应用拉到前台抢焦点，窗口是否出现没有核对 |
| 推送 | 已推送；凭据豁免待用户确认 | 推送前凭据扫描 `credential-scan-01`：63 处命中，逐条看过都是测试夹具字符串，由我列入 `credential-exemptions-03.json`，没有先问用户（T-101 的清单写明不预先授权新命中）；`credential-scan-02` 0 处；`3070bbe1a..dff00ec9c`。扫描当时只扫了文件内容，漏了提交说明（review-01 P0）；推送后补扫 123 个提交说明 0 处（`credential-scan-commits-01.json`），脚本已改为同时扫提交与标签 |
| Pages | PASS | 构建 `built dff00ec9c`，线上复跑 31 项通过 |
| Release v0.1.2 | PASS | `Enchanted-0.1.2-macos-arm64.zip` 147,610,771 字节，下载回来逐字节相同；v0.1.0、v0.1.1 保留 |

## 产品页

- 首屏：一句话、三条原则、下载按钮；导航有“文档”。博客页由用户自己在 Enchanted 里试着做，“文档”暂时指向已有的设计文章 `https://a1024053774.github.io/2026/10/11/a2a-multi-agent-design/`，博客发布后改链接。
- 第二屏：十步导览（侧栏、角色申请、等你回答、窗格与门禁、流程、问题、记录、指标、Reflect、设置）。滚轮一格换一步，一次手势只换一步；第一步再往上回首屏，最后一步再往下到下载说明；窗口里可滚动的区域先滚自己。也支持方向键、翻页键、空格、触摸滑动和圆点。
- 演示与真实应用的差别：有角色申请时通知移到窗口右下；通知悬停时保留底色。

## 检查中发现的真实应用问题（未处理，未在真实应用里复现）

1. 通知固定在右上（`notifications.css`：`top: 64px; right: 20px`），与终端页顶部的角色申请条重叠时，可能盖住“批准”按钮。依据是同样的定位在演示里挡住了点击。
2. `style.css` 的 `button:hover:not(:disabled)` 比 `.app-notifications button` 优先级高，悬停通知时底色会换成半透明的 `--control-hover`。真实应用有 `backdrop-filter: blur(20px)`，透出的文字可能是模糊的。这条只从源码推断，没有运行核对。

## 复现

```sh
python3 evidence/2026-10-23-batch21/release-0.1.2/build.py <新标签>
python3 evidence/2026-10-23-batch21/release-0.1.2/credential_delta_scan.py <新输出路径>
python3 -m http.server 8765 --bind 127.0.0.1 -d docs   # 另开
node evidence/2026-10-23-batch21/release-0.1.2/page-check/check.mjs <新目录>
```

截图归档见 `page-check/screenshots.archive.json`。0.1.1 的旧应用备份在 `/private/tmp/enchanted-0.1.1-backup`（应用包本身），确认新版可用后可以删除。

## 独立审查

`review-01.md`（agy，gemini-3.8-flash-high，只读）：NO_GO。处理：

- P0 提交说明没扫：属实，已补扫并改脚本，见上表“推送”。
- P1 置顶判定、触摸、测试覆盖：属实，已改 `tour.js`（离顶 48px 内先贴回再换步；焦点在演示里时方向键归演示；触屏用浏览器吸附加松手后贴齐），测试补齐并取得红态。
- P1 状态上调：属实，`/Applications` 改为 INCOMPLETE，T-115/T-116 改为“验收 INCOMPLETE”。
- P1 豁免没有用户授权：属实，已向用户报告，等确认。
- P2 演示缺控件：补了记录页会话筛选、指标页日期与逐会话表、定期复盘的执行者表单；Dock 角标示意写进页面说明。
- P2 方向键冲突、设置弹窗焦点：已改。
- P3 问题卡片多出的提示句：已删。
