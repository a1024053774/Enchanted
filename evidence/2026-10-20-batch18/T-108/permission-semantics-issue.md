# T-108：原生 AskUserQuestion 的 PermissionRequest 与第三轮阻断规则冲突

BLOCKED，需执行主控裁定；不提交当前修复为候选。分支 exec/t108，合并提交 d42e8b3fa7b174f052ef43c17a81e68230ee968e。第三轮实现与测试尚未提交。

看到的事实：主控运行的 `/private/tmp/t108-native-e2e-03.json` 是六项 PASS、model_calls=0、vendor_calls=0 的完整入口。它保存的真实 CLI hook 原件依次为 UserPromptSubmit、PreToolUse(AskUserQuestion)、PermissionRequest(AskUserQuestion)、PostToolUse(AskUserQuestion)、匹配 Stop。PermissionRequest 有完整 cwd、transcript_path、prompt_id、tool_name、tool_input；其 tool_input.questions 与之前的提问相同，没有 tool_use_id。它处于原来通过的正常界面答题路径中，不是本轮造出的异常输入。

第三轮 #26 要求“存在未知或权限等待时……问题不可作答”“权限等待的优先级高于旧问题”。当前实现按此对合法 PermissionRequest 一律阻断。用上述原件前三个事件回放实际 Panes.signal → SQLite → agentState/projectQuestions → answerQuestion，得到 running → waiting_user_answer → unknown；问题状态 unknown，作答被 current_turn_untrusted 拒绝，answer 新增 0，PTY 写入 0。复现摘要 `/private/tmp/t108-review03-permission-conflict-02.json`，命令：

```sh
LC_ALL=C node evidence/2026-10-20-batch18/T-108/replay_permission_conflict.mjs /private/tmp/t108-native-e2e-03.json /private/tmp/t108-permission-conflict-repeat.json
```

这证明一律阻断会挡住原来验收要求的正常界面作答。没有新启动 CLI、Electron、登录或真实模型回合；这也不是新的完整入口验收。首个观察脚本因漏写夹具 attempt:null 在 SQLite 初始化失败，修正后用新摘要路径运行；该初始化失败不算业务红态。

建议裁定：同一个原生 AskUserQuestion 自身发出的 PermissionRequest 是否仍归为这个提问；对其他工具（例如 Bash）的权限请求，保留优先阻断旧问题。如果仍要求一律阻断，需要同时明确原有“界面作答写回”验收路径如何满足。不能自行增加例外，也不能把旧正常原件继续当作当前候选 PASS。

公共字段缺失、解析错误和明确旧回合／异会话／子 agent 的结构性处理已保存在工作树，默认合同已扩为 373 项。修前 d42e8b3fa 上 271 项被业务断言拒绝；当前版本局部合同与相关只读／身份合同通过。完整验收与修复提交均停在上述裁定之前；没有把半成品提交成候选。
