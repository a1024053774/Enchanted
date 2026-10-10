# T-074-1 探针边界（2026-10-10）

起点：`5d9f03c669c1ded777524adc76a3f3834ae785cb`；ticket `ready_rev: 1`。本会话身份按任务卡为 `s12-t074`；尚未收到受管门禁的 task/attempt/session/fence，交付按任务卡指定的本地提交执行，不编造身份。

REALITY GATE: INCOMPLETE

目标：核实固定版本原生交互 CLI 的 R6 状态信号与 R7 PTY 注入事实。非目标：产品实现、T-075、成功率门槛、读屏判断、hook 安装、Claude 真实启动。

决定：现有 spec 第 6 节能否直接支持编排；不成立时只交证据与 needs-decision。

- observed：任务卡明确先做 Codex，Claude 首次真实启动前停下；现有依赖 node-pty 1.1.0 已装在相邻 fork 的 server 依赖中，只读使用，不改 fork，不新增依赖。
- observed：本机 Codex 0.162.1、Claude Code 2.1.296；外置盘已挂载；项目 status 无 problems/stale。
- inferred：官方文档的 notify 只描述 agent-turn-complete，可能不足以报告等确认；文档不能代替本机版本实测。
- unknown：本机是否发出 approval-requested 终端通知、何时发出、rollout 是否保留批准事件；PTY 注入在三种状态的消息归属；Claude 认证与真实行为。

方法：node-pty 托管 `/bin/zsh` 登录交互 shell，内置盘 `/tmp` 夹具与隔离 CODEX_HOME；只复制 auth.json，只信任夹具根，只装 git add/commit 两条 allow 规则，无 hook。固定实际 Codex 二进制路径；`--no-daemon` 防止接入共享后台，`--no-alt-screen`，workspace-write/on-request，模型 gpt-6.1-sol/xhigh，Fast 请求，关闭启动更新。notify 只写外部 JSONL；TUI 配置只发送 approval-requested、OSC 9、always。终端协议解析只读控制序列，不判断屏幕文字含义。

R7 写入前 fsync 追加登记；核对值来自 native rollout 的用户消息，逐字比较，不从模型回答或屏幕抄录。计划最多 12 次注入，先 idle/running，最后 awaiting_approval；最多 12 个原生 turn。每次用新序号，失败不重投。若实际消息出现丢失、合并、批准代答或无法证明状态，保存现场并停下，不靠另一种输入包装修复。

R6 用一次仅作用于夹具的显式升级命令触发批准，外部记录 notify、OSC 与 rollout 的接收时间。批准弹窗里的 R7 文字不表达批准意图；测试副作用限夹具，遇到问题立即停自己创建的 CLI，不批准其他行为。

接受事实报告的条件来自任务卡和 ticket；10 次是覆盖数量要求，不是成功率门槛。未完成项保持 unchecked，总体不能 PASS。中文 RESULTS 逐项报告失败方式与重放命令；Claude 预计 turn 和认证选项单独 needs-decision，等待主控转达。

Deep modules：只写证据用宿主和记录器，不增加产品 API。Ubiquitous language：沿用“窗格、原生会话、派发记录”。Tracer bullet：本票是 T-075 前事实门，不开始生产路径的跨层实现。
