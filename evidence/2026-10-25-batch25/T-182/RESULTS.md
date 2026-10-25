# T-182 结果：产品页首屏演示、分功能展示与紫色连线

## 状态：INCOMPLETE（待 agy 审查、push、线上 Pages 与 lcu 复看）

## 依据

用户原话见 ticket（rev 1、rev 2）；验收按 ready_rev 3：用户选 A，退役 T-173 里 35 项单一滚轮导览的检查（inbox `20261025T045006Z-ideation-answer-001`，用户原话“A 退役这 35 项 (Recommended)”）。

三份参考都用 lcu 在隔离的 Chrome for Testing（临时资料目录）里亲自看过，x.com 文章无需登录即可阅读：

- **uiarc.dev/components/button**：借鉴的是做法，不搬代码（自己实现）。圆角胶囊；一个界面只有一个主按钮（墨色），次按钮是白底细边加一层很浅的阴影，第三种是无底的 ghost；按下缩到约 0.97；悬停样式只在有精确指针的设备上生效，触屏点了不会卡在悬停态；不可用的次按钮保留边框、文字变淡，仍看得出是按钮；减弱动效时去掉按下缩放。
- **olavlj 的文章（How We Built a Next-Level Landing Page pt. 2）**：一条随滚动画出的贝塞尔曲线，线头不超过屏幕一半（文中“50% 规则”）；线加一层几乎看不见的光晕；装饰按线长的比例挂在线上，线画到时带一点回弹地出现。花和藤蔓按用户要求换掉：用 Enchanted 标志里本来就有的环绕轨道、轨道上的小珠和四角星，紫色。每个展示是一站，线走到哪一站就点亮哪颗星，沿途小珠依次出现。线的横向弯曲只放在两个展示之间的空白处，不压在说明文字上。
- **good-css.com**（MIT，`vojtaholik/good-css`）：读了首页与 foundations、layout、spacing-and-shape、interaction、motion、scroll-and-viewport 几份参考。本页采用：
  - 新颜色写成 `oklch()`，派生色（淡紫底、光晕）用 `color-mix(in oklch, …)`，不另写第二个色值；
  - 悬停全部放进 `@media (hover: hover) and (pointer: fine)`；可按的东西都有 `:active`（按钮缩到 0.97）；
  - 会移动或缩放的过渡放进 `prefers-reduced-motion: no-preference`，过渡写明属性、不用 `all`、不用 `ease-in`；动效 token `--ease-out: cubic-bezier(0.23, 1, 0.32, 1)`，按钮 160ms；
  - 新写的位置与间距用逻辑属性（`inset-inline-start`、`padding-block`、`margin-block-start` 等）；
  - 标题字号用 `clamp(rem + vw)`，上限不超过下限的 2.5 倍；
  - 焦点仍用全站已有的 `:focus-visible` 描边，不写 `outline: none`。
  - 与 good-css 不同、沿用本站已有约定的地方：深浅色仍按本站原来的 `prefers-color-scheme` 加 `data-theme` 重定义 token（主题切换按钮依赖它），没有改成 `light-dark()`，否则就是两套主题机制并存；旧的十六进制 token 没有全部改写成 oklch，只有本票新加的颜色用 oklch。

## 改动（只改 `docs/`）

- 首屏：左边标题、一句话、下载与“分功能看”，右边是第一个展示（项目 → 任务 → agent，三步）。窄屏顺序为标题、按钮、演示、三条原则，演示仍在首屏。首次进入时“下一步”按钮带一圈紫色提示，旁边写“从这里开始：点‘下一步’，或直接在窗口里点。”；点过一次后不再出现（存在本机浏览器里，读写失败时每次都提示）。
- 分功能展示共六个，每个只讲一件事，各自挂一份演示窗口、各自分步：三层视图；你说了才算（角色申请、回答提问）；一张票一条泳道；范围外的问题；只记你亲手做的（记录、指标）；回头看与设置。每个展示有“第 N / M 步”、上一步／下一步（最后一步变成“下一个功能”，滚到下一个展示），焦点在说明区时左右方向键换步，焦点在演示窗口里时方向键留给窗口。首屏以外的窗口滚到附近才挂上，先按 1040×760 占位，挂上时页面不跳。
- 页面不再劫持滚轮，也不再用触屏吸附；`tour.js` 删除，换成 `showcase.js`。`demo.js` 改为 `EnchantedDemo.mount(窗口)`，每个展示一份数据和计时器，互不影响；元素 id 加窗口前缀。新增 `grid`、`panes` 两个场景，把原来自动从任务格跳到分屏的一步拆成两步。
- 底色：首屏两团很淡的紫与蓝径向光，首屏下面一层随距离淡出的点阵；深浅色同一组 token。
- 按钮：见上面 uiarc 一节。

## 验收

页面检查：`page-check/check.mjs`（Playwright + 本机 Chrome for Testing，本地 `python3 -m http.server 8765` 服务 `docs/`）。第一部分是 T-173 检查里仍有对象的 16 项，移植到新结构；第二部分是本票新增。

| 运行 | 结果 |
| --- | --- |
| 修后 `local-05`、`local-06`、`local-07` | 三次都 PASS 43/43 |
| 修前 main 的 `docs/`（`red-main-01`） | 2/23：本票检查全部失败（首屏没有演示、底色单一、没有连线与步骤引导、只有一个演示窗口）；通过的 2 项是 390/820 无横滚 |
| 变异：收起首屏提示时收起它的位置，且任何窗口里按下都收起（`mutant-hint-shift-01`） | 被拒：“在展示里按下时页面不移动”与“批准角色”两项失败 |
| 变异：减弱动效时也按滚动画线（`mutant-calm-ignored-01`） | 被拒：“减弱动效下线一次画全、各站点亮”失败 |

本票新增的检查：首屏同时有演示、标题与下载（1440×900、390×844，浅深色）；底色至少两层径向渐变；连线描边是紫色；首次提示、第 1/3 步、上一步不可用；下一步到第 2 步且窗口显示任务格；方向键换步、窗口里的方向键不换步；最后一步变“下一个功能”并滚到第二个展示；刷新后提示不再出现；六个展示各有自己的窗口、互不影响；在展示里按下时页面不移动；线头始终不超过半屏、经过的站点亮、到底六站全亮；减弱动效时线一次画全、页面上没有在动的东西。

做的过程中这套检查抓到四个真缺陷，都已修，失败的运行保留在 `page-check/setup-error-01/`：
- 在任何一个演示窗口里按下鼠标都会收起首屏提示，提示的位置一收，下面整页上移 33px，松开时点到别的东西（批准角色点不上）。改为只有首屏展示收提示，收起时只隐藏、不让出位置。
- 演示外框同时有 `aspect-ratio` 和脚本写的高度时，宽度被高度反推，窗口跟着变宽、缩放又变大，820 宽时横向溢出 674px。外框宽度固定为 100%，窗口固定 1040px 宽再缩放。
- 窗口挂上之前也套了 1040px 宽，触屏 820 宽时溢出 236px。只在挂上后固定宽度。
- 线头按 6px 采样查找时取了“第一个不低于半屏的点”，会越过半屏几像素。改为取“最后一个不超过半屏的点”。
`local-02` 另有一次本地 `http.server` 断开连接（`ERR_CONNECTION_RESET`），检查全部通过，属于测试服务器，重跑未再出现。

截图（`shots/`）：修前/修后首屏 1440 浅深色、390 浅深色；整页（半尺寸）；修后滚到中段时的连线（浅、深）。检查运行的截图按 T-088 归档到 `/Volumes/WD-Elements/a2a-evidence/2026-10-25-batch25/T-182/page-check/`，各目录留 `screenshots.archive.json`。

### 随 rev 2 拆分退役的 35 项（用户选 A）

- light first wheel enters tour at step 1
- light one notch -> step 2
- light one notch -> step 3
- light one notch -> step 4
- light one notch -> step 5
- light one notch -> step 6
- light one notch -> step 7
- light one notch -> step 8
- light one notch -> step 9
- light one notch -> step 10
- light fast burst of 3 notches = one step back
- light past last step leaves tour downward to page end
- light wheel up from download returns to last step
- dark first wheel enters tour at step 1
- dark one notch -> step 2
- dark one notch -> step 3
- dark one notch -> step 4
- dark one notch -> step 5
- dark one notch -> step 6
- dark one notch -> step 7
- dark one notch -> step 8
- dark one notch -> step 9
- dark one notch -> step 10
- dark fast burst of 3 notches = one step back
- dark past last step leaves tour downward to page end
- dark wheel up from download returns to last step
- edge: at step 5 before drift
- edge: 5px drift then wheel up goes to step 4, not the last step
- edge: ArrowDown moves one step
- edge: ArrowUp moves one step back
- edge: arrow keys with focus inside the demo stay in the demo
- edge: wheel over the demo window header moves one step
- touch: one swipe up from the intro lands on the tour at step 1
- touch: swipe up on the tour moves one step
- touch: swipe down moves one step back

其中“焦点在演示里时方向键留在演示里”在新结构里有对应的新检查（窗口里的方向键不换步）。

## 没做 / 未验证

- 没在真机上看（手机只用 Chrome 的移动模拟）；线上页面与 lcu 复看在 push 之后做。
- 窄屏上演示窗口按桌面尺寸缩小，字很小，页面上写明“完整操作请用电脑打开”。
- 不改产品代码，不发 Release。
