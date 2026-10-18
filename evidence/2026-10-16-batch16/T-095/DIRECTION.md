# T-095-1 方向说明（2026-10-17，待执行主控确认）

**INCOMPLETE：建议以 Herdr 期的只读状态命令为准。** 仅完成读回与探针准备，尚未实现或启动模型。绑定 T-095 / a1 / s16-t095 / `launch-4b1abba18e87460da9cbacec04905c78`；基线 `3c9016d0230223945f0e16543b230a047c2ad032`，ready_rev 1。

## 决定及依据

目标是显示“等待主控回答”及 worker、launch、pane 身份，覆盖折叠、展开与退出。非目标沿用任务卡：不改 Herdr server、不猜意图、不自动答题、不维护两份状态。

| 性质 | 读回事实与含义 |
| --- | --- |
| observed | `intent.md` 的切换条件尚保留 Herdr 日常派发。`scripts/dispatch:65` 调用 `herdr agent prompt`，本身没有状态读取或监视循环。 |
| observed | `workbench/src/panes.ts:722` 的 unknown / idle / busy 来自自身 pane 的 host_events；`daemon.ts:237` 将它投影进工作台，没有读取 Herdr pane 的路径。因此只改工作台不能覆盖当前执行主控。T-071 / spec 第 6 节的工作台结构化信号契约保持原样。 |
| observed | 指定 issue 和最新 assign 未进入此 worktree；已只读主 checkout 原件（`20261017T172907Z-executor-issue-001`、`20261018T015728Z-ideation-assign-001`）。临时 `+QUESTION` 监视只是现象来源。 |
| measured | Codex 0.163.0、Herdr client/server 0.9.4；当前 pane `wF:p68` 与主 checkout 的启动记录相符。status 为 0 problems、0 stale living docs。 |
| unknown | 两种布局的完整机械结构、退出后的读数，以及隔离配置能否触发同类面板，尚无本次真实原件。 |

## 确认后的最小实现

新增 `scripts/agent-status`，复用 `launch_records.py` 从 launch 定位 worker / pane，读取前后核对 live 身份；输出一份 JSON，包含 task / attempt、worker / launch / pane、状态、时间、原始 Herdr 状态及读数来源，不回写状态。

按 **Ubiquitous language**，显示名统一为“等待主控回答”，内部值拟为 `waiting_controller_answer`。只认真实面板的 UI 结构组合，不凭正文、单个关键词或历史输出推断。身份错配、读数不可用或布局无法区分时输出 `unknown`；普通 working 也须有机械依据，不能由“没匹配到面板”推出。每次重读，退出后不沿用旧等待状态。

**Tracer bullet** 是“launch → 真实 Herdr 读数 → 带身份的 JSON”，再扩展两种形态及反例。按 **Deep modules**，读取和判定由这一个入口承担。`dispatch` 保持现有派发语义；新入口不发送文本或按键。

## 最小探针与停止条件

同目录 `controlled-panel-probe.py` 交主控审核。**单次最多 1 个根提示回合；红、绿各一次合计最多 2 个根回合，每次由主控决定。0 次自动答题、重投或 resume。此限额不约束工具链内 API 请求数或费用。**

脚本仅复制 auth.json 到 `/tmp` 隔离 CODEX_HOME，固定模型/CLI/参数，关闭命令工具及外部工具入口，使用 read-only 沙箱。操作者确认新 pane 已到真实 shell 提示符后才启动 Codex；固定提示只请求面板。操作者切换折叠、展开并取消，脚本保存原始读数；结束关闭自建 pane，原生记录存外置盘，删除整个隔离 CODEX_HOME。

零模型调用预览：`python3 evidence/2026-10-16-batch16/T-095/controlled-panel-probe.py`。批准后由主控在沙箱外运行同一命令并加 `--approve-one-root-turn --phase red`。命令工具开关依据 [OpenAI Docs 配置参考](https://learn.chatgpt.com/docs/config-file/config-reference)；本地离线检查另存，尚不证明实际面板启动成功。

红态须为两种形态的原件与同期 working；未复现就报 INCOMPLETE 并停。随后用同一原件经入口回放，并另取真实绿态；覆盖普通活动、正文引用标记、退出、错身份和不可读反例。命令活动原件另取已有可核对来源，本探针不授权模型运行命令。

**下一步 / owner：执行主控确认脚本方向与探针预算；worker 在收到确认及有效红态后实现。**
