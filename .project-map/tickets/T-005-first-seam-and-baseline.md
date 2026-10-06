---
id: T-005
title: First seam and baseline
type: research
status: closed
blocked_by: []
claimed_by: controller
supersedes:
---

## Question

Which current Herdr/Codex entry point and representative coding task provide the first
independent acceptance seam for the exploratory baseline?

## Resolution

PASS（研究入口已确定，不代表产品已通过验收），2026-10-06。
持久上游源码位于 `.upstream/herdr`，固定 c4653a4f10502601ac110b12b2c45a5f7134082b；
当前项目已有本地基线 9c812f3。真实入口为 Herdr agent start/prompt/get，显式绑定活跃 pane。
分页夹具 CONTRACT 及独立 subprocess oracle 已落盘：坏 starter 2/10、reference 10/10，
命令和结果见 [新证据](../../evidence/2026-10-06-t005/README.md)。
缺少产品代码是新项目起点，不再当作需要用户决策的阻塞；旧观察记录保留在下面。

### 2026-10-05 未完成记录

INCOMPLETE after the bounded baseline run. The current Herdr lifecycle surfaces are verified
(`agent start/list/get/read/prompt/wait`, plus the API wait implementation), and the upstream
source is available read-only at `/tmp/herdr-upstream.pniXIr` (`c4653a4f10502601ac110b12b2c45a5f7134082b`).
The a2a directory still has no product source, Git history, representative coding task, or
independent acceptance oracle. The worker timeout, missing report, monitor record, and
controller-side source research are preserved under
`evidence/2026-10-05-baseline-01/`. Choose a persistent target checkout, task fixture, and
independent oracle in the next Design / Spec step before creating an implementation ticket.
