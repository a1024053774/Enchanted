# 09B I1 bridge decision brief

当前 A-05 的 ideation fake API 70730 是阶段 A 夹具 `t078_09b_fake_api.py`：只提供 `/health`，业务 `/v1/messages` 返回 409。Claude 1228 的 `ANTHROPIC_BASE_URL` 已固定为 `http://127.0.0.1:57534`。A-05 readiness、70730 的 PID/lstart/argv、B1 screen 证据和 A-05 五进程仍保持原样。

## 选项影响

| 方案 | 做法 | readiness/身份绑定 | 预算与 B1 证据 | 清理与风险 |
|---|---|---|---|---|
| A 同端口替换 | 认证停止 70730，在 57534 启动最终应答 API | PID、lstart、argv 和 ready 文件都会改变；旧 readiness 不能继续作为当前绑定，必须生成新的绑定和签字 approval。Claude 1228 可继续使用端口，但现有复用门禁会拒绝旧 API 身份。 | B1 屏幕原件仍是历史证据；I1 不能直接绑定旧 A-05 attempt，至少要重新取 API/ready 读回。I1 消息预算仍可用 1/6，但过程身份需要另记。 | 先停止并归档旧 API，保留 root；新 API 失败会留下半替换状态。不能把同端口当成身份不变。 |
| B 新建 A-06 | 用最终 protocol API 从阶段 A 开始新 root、new daemon、new target claim，再复用同一 B1 逐屏驱动 | 获得全新的 root、attempt、session、fence、thread、API PID/lstart/ready；所有复用检查自然成立。旧 A-05 readiness 与 B1 屏幕仍只作历史证据。 | A-06 阶段 A 供应商模型 0；B1 逐屏证据需重取；I1 预算按 I=4 roots/6 Messages，首个 I1 使用 1 root/1 Messages。原 A-05 B1 预算不迁移。 | A-05、A-06 各自认证 daemon_stop、核对 target/API/Claude 身份、逐成员归档和读回。成本最高但边界最清晰。 |
| C 端口代理/热切换 | 在 57534 前放代理，或让 70730 热加载协议模式 | 代理/热加载会改变 A-05 的实际 API 路径与未记录的进程行为；PID/lstart 不能证明最终业务处理者。需要新增协议与身份契约，属于平行入口。 | 既有 B1 证据无法证明 I1 应答者；预算可以机械保持，但独立 oracle 不能把请求归属到已登记 API。 | 代理、旧 API、端口和 root 的清理边界不唯一；不满足门禁优先和不增平行路径要求。 |

推荐 **B：新建 A-06**。它保留 A-05 的完整历史证据，最终 API 在 Claude 启动前就登记 `/v1/messages` 协议，避免 PID 替换或未登记代理。A-06 的阶段 A runner 应把最终 API 的 `api_url` 作为动态模板，ready 记录实际端口、PID、lstart、argv、role/stage；B1 复用核对这份新 readiness。审批前不启动。

## I1 计划

最终 API 对每条请求先按实际登记的 dispatch 正文、全局 `dispatch.seq`、request/stop ID、role、attempt/session/fence 核对，再返回确定性 SSE。I1 首根使用 1 root、1 Messages，响应顺序为 `message_start`、文本增量 `I1_ACK`、usage delta、`message_stop`；I2～I4 保留其余 3 roots/5 Messages。正文改写、seq 重置、request/stop ID 替换、角色越权和预算超限各保留独立反例。

真实 I1 的停止条件是：请求原文、response SSE、hook/Stop 收据、API 请求数和数据库事件全部落盘并经独立 oracle 核对；任何 409、未登记正文、身份漂移或额外 Messages 都停止并保留 root。executor 角色不与 ideation 并行启动。

当前离线 I1 red/green 与材料提交中的 RESULTS 追加尚未形成新的提交；#236 所述失败只因材料目录已存在时重复 `mkdir`，重跑提交脚本需允许既有材料目录并把 RESULTS 一并提交。
