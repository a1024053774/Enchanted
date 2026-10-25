---
id: T-173
title: 产品页：更新交互动画，修整体页面割裂、不和谐
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

来源：用户 2026-10-24 逐字：“更新产品页的交互动画，还有整体页面，整体页面感觉有点割裂，不和谐，这些修复一下……产品页让执行主控去修，给他 lcu 了，可以亲自打开 Chrome 看看”。

对象：`docs/index.html` 与 `docs/assets/`（GitHub Pages，main:/docs）。
- 先用 lcu 亲自打开 Chrome 看线上页 https://a1024053774.github.io/Enchanted/ （桌面宽与手机宽），逐段记录“割裂/不和谐”的具体位置与原因（字体、色彩、间距、圆角、阴影、插图风格、区块节奏不一致等），截图入证据。
- 交互动画按当前产品（0.1.3：项目→任务→agent 分屏、多 agent 并行、审查打回、集成）更新，演示与真实界面一致，不演示不存在的功能。
- 整体统一成一个视觉家族：读 `frontend-production`（含同族、动效、去 AI 味），文案中文为主、不夸大。尊重 `prefers-reduced-motion`；手机宽无横向滚动。
- 修完用 lcu 在 Chrome 里复看本地与线上，前后截图对照。

## Acceptance

- [ ] 修前问题清单（带截图）与修后对照，每条有结论。
- [ ] 动画与 0.1.3 真实界面一致；reduced-motion 下有静态替代；手机宽 390px 无横向滚动。
- [ ] agy 独立审查；push main 后 Pages 返回 200 并在 Chrome 里复看线上。

## 不做

不改产品代码；不发新 Release（页面更新即可）。push 已获用户授权（“做完继续更新 github 以及 pages”），不 force push，推前扫凭据与私有数据。
