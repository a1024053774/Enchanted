---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: ""
refs: [".project-map/tickets/T-144-flow-page-fixes.md", ".project-map/inbox/20261023T140459Z-worker:b23-t144-issue-001.md"]
created_at: "2026-10-23T14:16:57.632497Z"
schema: 1
title: "T-144：执行主控按派发归属泳道，与受保护 test_t111_flow.mjs:36,41、test_t146_ended_projection.mjs:65 冲突，需授权改断言"
id: "20261023T141657Z-executor-needs-decision-001"
---

状态：T-144 候选 52af15174 已交付（INCOMPLETE，真实 Electron 验收待执行主控沙箱外运行），不阻塞其他票。

问题：T-144 按用户要求让执行主控“派发了哪个任务的 worker，就挂在那条泳道”，与两份受保护验收文件的旧断言直接冲突：
- `workbench/tests/test_t111_flow.mjs:36` 期望泳道 agents 只有 worker，第 41 行期望 controller 在“未归属”（T-111 合同）；
- `workbench/tests/test_t146_ended_projection.mjs:65` 期望已结束的主控在“未归属”（T-146-3 新增，按 T-111 的归属写的）。
worker 未改这两处，上报 20261023T140459Z-worker:b23-t144-issue-001；运行证据在 T-144 worktree 的 evidence/2026-10-23-batch23/T-144/t111-01.json、t146-ended-projection-01.json。

依据：用户原话（T-144 ticket 第 16 行）“下面怎么两个执行主控都是未归属,且这两个执行主控是不同任务里的吧,不同任务里的该界面要分开”。旧断言要求的正是用户指出不对的行为。

请求：用户授权修改上述两处受保护断言——只把“执行主控在未归属”改为“执行主控按派发关系在其任务泳道；确实无关联的才在未归属”，其余断言、检查名、期望值不动，改动逐条写入 RESULTS 与 report。
最小选项：
A. 授权按上面修改（推荐：与用户第 7 条要求一致）。
B. 不授权：T-144 的归属部分不做，只做标题与多路径。

在裁定前，执行主控照常完成 T-144 其余验收，不合入。