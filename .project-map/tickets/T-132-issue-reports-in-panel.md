---
id: T-132
title: 面板显示问题上报：列表、状态、答复与处置
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## What to build

来源：用户 2026-10-22 逐字：“107 吧多 worker 做出来，早期的调研票关掉，然后还缺的都做”。 切换条件里的“问题面板”：门禁已能记下 worker、reviewer、monitor 的问题上报（`raise_issue`、`issues`、`answer_issue`、处置），状态有待判断、等你决定、已转交、稍后、已答复、已送达、已关闭；但界面没有问题列表，用户看不到也答不了。语义见 controller-split spec 第 4 节与 native-cli spec 第 7 节。

- 面板里列出所选项目各任务的问题上报：标题、正文、上报会话（角色、任务）、是否 blocking、状态、时间、答复与处置记录。
- 用户可以答复（逐个或打包，沿用门禁现有的发送格式与 `answer` 用户输入记录）、关闭、标“稍后”；blocking 只有用户能关（门禁已有规则）。
- 读取只读、不改库；新上报出现时在面板与项目行提示（应用内，不调用系统通知，沿用 T-110）。

## Acceptance

- [ ] 真实 Electron：夹具里 worker 经门禁上报两条问题（一条 blocking），面板列出，状态与门禁 `issues` 读回一致；用户在界面答复一条，答复写进上报方窗格并记为 `answer` 用户输入；关闭另一条后状态为已关闭，记录不删除。修前界面上没有问题列表。
- [ ] 反例：读取失败时面板显示读取失败而不是空列表。
- [ ] 截图与复现命令入证据。

## 不做

不改门禁的问题语义与处置规则；不做系统通知。
