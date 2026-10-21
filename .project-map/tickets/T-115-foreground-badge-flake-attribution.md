---
id: T-115
title: 断连重连后回到前台 Dock 角标偶发未清零：取得失败现场的焦点证据并归因
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

来源：T-112 合并回归和第二轮独立审查（evidence/2026-10-20-batch18/T-112/independent-review-02.md 的“前台角标失败：归因 INCOMPLETE”一节）。缺陷级票，由执行主控在已批准范围内自建（T-004）。

现象：
- T-110 的真实入口 green 场景里，“Foreground after reconnect clears badge”一步失败过一次，最后 badge=1。原件是 T-112 证据目录下的 outside-merge-t110-native-03-executor-rerun.json，source_head 为 22783a1ee，当时负载约 10。
- 同一产品代码在负载约 5 时通过，原件是 outside-merge-t110-native-03.json。
- 第二轮审查在代码里没有找到“侧栏晚返回覆盖前台清零”的路径（main.ts 每次重算都同步读当前焦点）。失败原件没有焦点信息，所以既不能归为测试等待问题，也不能定为产品缺陷。

要做：
1. 用 5f19062f5 已加的焦点与角标时间线观测（hidden、focused、focused_window、badge，以及 focus/blur 事件），在有负载的条件下重复跑 T-110 真实入口，直到取得一次失败现场，或在约定次数内始终不复现；次数与负载条件事先写明。
2. 按现场归因：
   - 失败时窗口一直是 focused=true，badge 却是 1：按产品或原生事件路径修，修前取得红态；
   - 窗口没有取得焦点，或随后失焦：修测试动作的完成条件，不加产品重试，也不只是延长超时。
3. 不放宽 T-110 的任何断言。

## Acceptance

- [ ] 失败现场的完整时间线入证据；或者写明在既定次数和负载下没有复现，作为 INCOMPLETE 如实上报。
- [ ] 若是产品缺陷：修前红态、修后绿态，真实入口 PASS。
- [ ] `project_map.py status` 0 问题。

## 不做

不改 T-110 的提醒语义；不加自动重试；不为了让测试通过而修改等待期限。

## 进展（2026-10-21，执行主控）

状态 INCOMPLETE，票保持 open。attempt a1 合入 main 77d8559cc。

- 模型：用户指定 Codex 接入的 DeepSeek V4.1 Flash Free（OpenCode Zen Free），强度 high（构思主控 answer 20261021T041452Z）。worker 是 s18-t115，reviewer 是 s18-t115-r1。这个模型多次没交付就结束回合，或者申请升级；执行主控拒绝了所有升级，代为在沙箱外运行，提交也由主控补做。
- repeat-02：10 个 CPU 忙循环，负载约 10～45，外层跑 10 次。目标断言实际执行了 7 次，0 次失败；另外 3 次在到达目标检查前就因为测试夹具的不稳定而中止（窗口清理超过 10 秒；高亮前快照缺少 agent 导致 KeyError）。所有前台事件都是 did-become-active 时 badge=1，约 3～23 ms 后 browser-window-focus 把它清零。没有复现，所以没有归因，也没有改产品或断言。
- 为了让真实入口能跑，修了夹具：Claude CLI 已自动升级到 2.1.306，原生夹具改为运行时读取已安装的版本（691235cad）。门禁 controller_version_mismatch 的检查不变。
- 独立审查 01：INCOMPLETE。没有发现削弱版本门禁或清理身份核对的地方。指出一个 P2：重复脚本只要错误文本命中目标断言，就判为 REPRODUCED，不检查时间线分类是否完整。另有措辞修正：应写成“目标断言执行 7 次、0 失败”，以及“约 3～23 ms”。
- 再做时：先修 T-116 里的测试夹具不稳定和脚本的 P2，然后在负载下加大次数重跑。
