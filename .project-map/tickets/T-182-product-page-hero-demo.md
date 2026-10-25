---
id: T-182
title: 产品页改版二：演示放首屏、背景不单调、切换有引导、按钮参考 uiarc.dev
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

来源：用户 2026-10-25 在执行主控会话里逐字（转述见 inbox 20261025T035656Z-executor-report-001）：“我说说我的建议,现在背景纯色太单调,还是不把交互放第二屏幕了,就放在第一屏幕,不然太空,然后这个切换要有引导,然后去这个网站https://uiarc.dev/components/button找一些好看的样式”。

对象：`docs/`（GitHub Pages）。在 T-173 的基础上：
- 交互演示移到首屏，与标题、下载入口同屏，首屏不再空。
- 背景不再是单一纯色：加层次（渐变、纹理或分区底色等），深浅色都和谐，不喧宾夺主。
- 演示的步骤切换有引导：当前第几步、可点的下一步/上一步、首次进入的提示，键盘可操作。
- 按钮样式参考 https://uiarc.dev/components/button，用 lcu 在 Chrome 亲自看后挑选；只借鉴样式，许可证允许才搬代码并保留声明，否则自己实现同类效果。
- 读 `frontend-production`，保持同一视觉家族，文案中文为主、不夸大。

## Acceptance

- [ ] 修前/修后截图（桌面宽与 390px）对照：演示在首屏、背景有层次、切换引导清楚。
- [ ] reduced-motion 下有静态替代；390px 无横向滚动；T-173 的 51 项页面检查（加本票新增检查）全过。
- [ ] lcu 在 Chrome 复看线上页；agy 独立审查；push 后 Pages 返回 200。

## 不做

不改产品代码；不发新 Release。push 已获授权，不 force push，推前扫凭据与私有数据。
