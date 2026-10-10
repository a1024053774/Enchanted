---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: ""
refs: ["ticket:T-059", "file:evidence/2026-10-09-batch11/T-059/needs-decision-04.md", "file:evidence/2026-10-09-batch11/T-059/controller-decision-01.md"]
created_at: "2026-10-10T14:58:48.479235Z"
schema: 1
title: "T-059 需要用户决定：Claude 认证方式、模型、额度"
id: "20261010T145848Z-executor-needs-decision-001"
---

两个主控是真实 Claude 会话，第一次调用前需要用户定三件事（详情见 needs-decision-04.md）：
1. 认证方式，二选一：
   (A) 用户提供一个独立的 Anthropic API key，或指定一个已授权的 API 网关。key 只放进隔离进程的环境变量，配置目录全部在 /tmp，不碰 ~/.claude。请用户把 key 放在一个私有位置（例如自己建、权限 0600 的文件），只告诉我们路径，不要贴进聊天或条目。
   (B) 用户亲自在一个 /tmp 临时目录里登录 Claude CLI。worker 先备好目录和命令，然后停下；登录由用户操作。
   不采用的做法：从 ~/.claude 或 Keychain 读用户现有登录。
2. 两个 Claude 会话用的模型和 effort。执行主控建议用 claude-opus-5-5，与现在两个主控一致。
3. 额度：最多 16 个 Claude 原生 turn、6 个 Codex 原生 turn，是否批准？另外，Claude 要不要设金额上限？要的话给出美元数，会通过 --max-budget-usd 传入。
其余口径执行主控已定，见 T-059/controller-decision-01.md：两题打包按“一个答复加一个关闭告知”处理。