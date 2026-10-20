---
id: T-114
title: Enchanted 打包发布：重新构建、清本地缓存、仓库改名公开、开 Pages、发 GitHub Release
type: build
status: open
blocked_by: [T-112, T-113]
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

来源：用户逐字（2026-10-20，会话"a2a-构思主控"）："这个做完后应该不差什么了吧，给我做个产品页，用 GitHub pages 就像，用户在产品页前端就能点击这个软件的一些内容来操作，当然这些都是我们预设好的，就是在前端就能点我们软件的不同按钮之类的看效果，以及里面展示一些我们预设的想要表达的内容，这个由 claude 模型来做，然后同时构建打包笨笨，清理本地缓存，更新固 GitHub 仓库页面"

AskUserQuestion 逐字选项：产品页放置——"把仓库改个名字公开吧，改名叫 Enchanted，我应该有个 Enchanted 了，把那个归档吧，规划成我们这个 a2a 仓库的未来 feature"；打包范围——"再发布到 GitHub Releases"；产品名——"Enchanted,a2a 是其编排内核 (Recommended)"。

核实（构思主控 2026-10-20）：GitHub 上 a1024053774 名下没有 `Enchanted` 仓库，本地 `~/Documents/Code/Enchanted` 无 remote，故名字可用；a2a 仓库现为 private，免费账号 private 仓库不能开 Pages。

用户已明确授权本票的外部动作：把仓库改名 `Enchanted`、改为 public、开 GitHub Pages、发 GitHub Release、push。授权范围仅限本票列出的这些；其余外部动作不在授权内。

顺序（任一步停下条件触发就停下上报，不继续往后）：

1. **前置**：T-112 与 T-113 都已合入 main，`project_map.py status` 0 问题。构思主控另行把 AGENTS.md 里固定写死模型的那条改成"默认见设置，可改"，并把"Enchanted 已冻结"改为新决定（见下"不做"），不由执行主控改。
2. **软件改名**：.app 显示名改为 Enchanted。**不改 bundle id 与数据目录**，避免丢用户现有项目/任务/窗格数据；若改显示名必须迁移数据才能运行，停下上报。
3. **构建打包**：按现有标准构建命令在内置盘临时目录构建（AGENTS 构建条款），产物安装到 `/Applications/Enchanted.app`（替换旧 `a2a.app`，旧的先确认已不在运行再删），codesign 校验，真实入口打开验证一次；产出发布用 `.zip`（ad-hoc 签名，未公证，Release 说明里写明首次打开需右键打开或解除隔离）。
4. **清理本地缓存**：构建完成后删除本次构建的临时目录、`node_modules` 之外的构建中间产物、已关闭票遗留的 `/private/tmp` 现场（逐目录，先列清单；不删正在运行的 worker 的夹具，不删 `.runtime/` 与用户数据目录，不删 `node_modules`——下次打包还要用，除非用户另说）；报告前后 `df`。
5. **公开前检查**：对 push 之后新增的全部提交与对象重跑凭据扫描（沿用 T-101 的豁免清单与扫描命令），0 未豁免才继续；确认 `git ls-files` 里没有 `.runtime/`、`auth.json`、用户邮箱以外的个人凭据；README 更新为 Enchanted 的中文首页（含产品页链接、下载说明、协议、已知限制），不夸大。命中则停下，不改名不公开。
6. **外部动作（顺序固定）**：① push main；② `gh repo rename Enchanted`（名字空闲已核实，重名则停下）；③ 把本地 `origin` 改成新地址并核对；④ 改为 public（`gh repo edit --visibility public --accept-visibility-change-consequences`）；⑤ 设置仓库描述、主页链接、topics；⑥ 开 Pages 并等首次部署成功，打开线上地址核对演示可点；⑦ 创建 Release（tag 用版本号，附 `.zip`，说明里写已知限制与未公证），下载一次核对字节数。每一步先读回上一步结果。
7. 本地目录名 `a2a` 不改；旧本地 `~/Documents/Code/Enchanted` 不动（已冻结快照，见 AGENTS）。

## Acceptance

- [ ] 凭据扫描输出摘要入证据，未豁免 0；push 前后 `git ls-remote` 对比。
- [ ] 红态：当前 private、无 Pages、无 Release。绿态：仓库 `a1024053774/Enchanted` public，Pages 线上地址可打开且演示可点（真实浏览器截图），Release 里 `.zip` 下载字节数与本地一致。
- [ ] `/Applications/Enchanted.app` 双击能开，原有项目/任务/窗格数据仍在（改名前后数据目录一致的证据）。
- [ ] 报告缓存清理前后 `df` 与删除清单；没有误删运行中夹具。
- [ ] 反例：重名时停下；扫描有未豁免命中时不改名不公开；Release 说明含"未公证"。
- [ ] `project_map.py status` 0 问题。

## 不做

不做公证、自动更新、Homebrew 等其他分发；不改 bundle id 与数据目录；不 force push；不动 Herdr；旧 Enchanted 的功能并入只做路线图条目（不在本票实现）。
