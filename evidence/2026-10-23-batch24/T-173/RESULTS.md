# T-173 产品页：交互动画与整体统一（2026-10-24）

用户原话：“更新产品页的交互动画，还有整体页面，整体页面感觉有点割裂，不和谐，这些修复一下……产品页让执行主控去修，给他 lcu 了，可以亲自打开 Chrome 看看”。

## 修前问题与结论

修前截图是线上 `https://a1024053774.github.io/Enchanted/`（0.1.3 发布后的 `54dd554ce`），用 Playwright 在 1440×900（浅色、深色）与 390×844 截取；关键几张在 `key/`，全套在外置盘（`shots-before.archive.json`）。

| # | 位置 | 割裂在哪 | 原因 | 结论 |
| --- | --- | --- | --- | --- |
| 1 | 全页 | 页头、首屏、导览说明、下载区左边线分别在 116、200、20、116px（`key/before-hero.jpg`、`before-step4.jpg`） | 首屏 `.intro` 是纵向 flex，`.wrap` 带 `margin: auto` 后收缩成内容宽度再居中；导览用另一套 `max(16px, (100vw - 1400px)/2)` 边距 | 已修：统一 `--page-max: 1360px` 与 `--gutter`，`.wrap` 设 `width: 100%`，导览按同一容器算边距；1440 宽下四处都在 64px（检查项 `t173 … share one left edge`） |
| 2 | 全页对演示窗口 | 页面是暖灰底 #f6f6f4、强调色 #0169cc、深色 #111；演示窗口用的是真实应用的 #1d1d1f／#0a66d8／#1c1c1f 和偏紫的侧栏渐变，两套颜色放在一起像两家产品 | `site.css` 的配色注释还写着旧版工作台配色，应用改样式后页面没跟上 | 已修：页面 token 改取 `workbench/app/style.css`（墨色、灰、线、强调、琥珀、深色底），底色取侧栏那层偏冷的灰；主按钮改成与应用“新建终端”“批准”同样的墨色；演示侧栏渐变去掉偏紫 |
| 3 | 第二屏 | 说明贴左边、窗口贴右边，两侧留白不对称（`before-step4.jpg`） | 同 1 | 已修：同一容器，窗口两侧留白一致（`after-step4-grid.jpg`） |
| 4 | 第 2～10 步 | “等待用户回答”通知一直盖在窗格底部和泳道上（`before-step4.jpg`、`before-flow-dark.jpg`） | 通知按问题记，切步不清 | 已修：只在讲它的第 1、3 步出现，其余步骤当作已经看过；问题本身仍是等你回答（侧栏“1 个等你”不变） |
| 5 | 首屏与第二屏、第二屏与下载区之间 | 通栏细线把页面切成三块 | `section.block`、`.tour` 的 `border-top` | 已修：去掉分割线，靠留白分段；页脚线保留 |
| 6 | 首屏大标题 | 字距 -.045em、字重 650，比应用里的系统字体收得更紧 | — | 已修：-.035em、600 |
| 7 | 演示动画 | 换步时只有左边说明淡入，窗口整块瞬切；演示里没有 0.1.3 的项目任务分屏、任务内普通终端；流程页看不到“集成” | 演示停在 0.1.2 | 已修：换步时主区域淡入、窗格与任务格依次出现（只动 opacity 与 transform）；第 4 步改为“项目、任务、agent 三层”：先停在 inkwell 的任务分屏（每张票一格，取自 `renderer.tsx` 的 `project-task-grid`），1.6 秒后像点了 T-11 一样进入它的分屏：worker、独立审查、普通终端并排，底部门禁状态（T-139/T-143/T-159）；第 5 步泳道先往右带一眼独立审查与集成，停一会儿再回到开头（真实应用的泳道同样左右滚动） |
| 8 | 手机宽 390 | 演示缩成缩略图，看不清 | 演示按桌面尺寸缩放 | 未改：页面已写“完整操作请用电脑打开”，手机宽无横向滚动；列为已知限制 |
| 9 | 流程页 | 泳道右侧被截断 | 真实应用 `flow.css` 同样是 5×230px、左右滚动 | 不改布局，用第 7 条的平移展示 |

## 减弱动效

`prefers-reduced-motion: reduce` 下：不播换场景与窗格出现动画、不平移泳道、第 4 步直接显示 T-11 的分屏（静态替代）。检查项 `t173 reduced motion shows the settled views state at once` 与 `t173 reduced motion leaves nothing animating`。

## 检查

`page-check/check.mjs` 复制自 T-172，原 44 项不变，只把第 4 步右键菜单检查改为等窗格出现后再点（第 4 步现在先显示任务格）；新增 7 项 T-173 检查，期望来自本票与上表。

| 运行 | 对象 | 结果 |
| --- | --- | --- |
| `red-live-01` | 线上修前页 | INCOMPLETE 45/51：T-173 的 6 项失败（左边线 116/200/20/116、通知盖住流程步、没有任务格与普通终端、减弱动效下仍是旧分屏）；原 44 项全过 |
| `local-01` | 本地修后 | PASS 51/51 |
| `mutant-calm-01` | 删掉减弱动效下直接显示终态的分支 | 被拒：`t173 reduced motion shows the settled views state at once` |
| `mutant-notice-01` | 删掉切步清通知 | 被拒：两项 `notification does not cover the flow step` |

截图（Playwright）：`key/after-hero.jpg`、`after-step4-grid.jpg`（任务格阶段）、`after-step4-dark.jpg`（T-11 分屏阶段，深色）、`after-flow-pan.jpg`（泳道平移到独立审查与集成）、`after-phone.jpg`。

## lcu

票要求用 lcu 在 Chrome 里亲眼看。lcu 只把 Chrome 当作桌面应用，挂到的是用户自己的 Chrome（停在用户的个人资料选择页），这不在我能操作的范围内，已立即停手；改用 Playwright 自带的 “Google Chrome for Testing”（独立 bundle id、临时资料目录）开线上页，lcu 挂接时停在等待应用授权，授权要由用户批准，我没有代批。lcu 复看待补；以上截图均来自 Playwright。

## 复现

```sh
python3 -m http.server 8766 --bind 127.0.0.1 -d docs &
(cd workbench && PAGE_CHECK_URL=http://127.0.0.1:8766/ node ../evidence/2026-10-23-batch24/T-173/page-check/check.mjs <目录>)
(cd workbench && node ../evidence/2026-10-23-batch24/T-173/shoot.mjs <url> <目录>)   # shoot2、shoot3 同
```

## 独立审查

`review-agy-01.md`：PASS。P3 两条：任务格计数排除主控（演示数据的差别，审查后补了代码注释，未再审查）；`wb-spot` 动的是 outline-color，减弱动效下不播。

## 上线

推送前扫描 `credential-scan-01.json` 0 处命中，无用户邮箱、无大文件；`3688e2ec2..275b792db`，无 force push。Pages 构建于 `275b792db`，返回 200；线上 `live-01` 51/51 通过（Playwright 自带 Chromium，无头）。

## 状态：INCOMPLETE（只差 lcu 亲眼复看）

lcu 挂接 “Google Chrome for Testing” 两次都没有返回：第一次 30 分钟无响应后超时，第二次我手动停止。推测在等应用授权，授权要用户批准，我没有代批。票上“用 lcu 打开 Chrome 看、修后在 Chrome 里复看本地与线上”这一条未完成；其余验收项有上面的 Playwright 证据。用户批准 lcu 控制 Chrome for Testing（或指定可以用的 Chrome 窗口）后可补。
