# T-109 / a1：INCOMPLETE

2026-10-20 执行主控 #7 后续：首次提交为 `681fc0da5`；真实入口首轮在键盘展开驱动处失败。层级归属与折叠计数已通过，诊断、驱动修复和新编号命令见 [FOLLOWUP-02.md](FOLLOWUP-02.md)。以下保留首次交付时的状态记录。

已完成父 launch 记录与可折叠的竖向缩进树，本地合同和回归通过。真实 Electron／PTY 验证、正式独立审查、Git 提交与完整 checkout 的地图检查尚待执行主控完成，不能据此关闭本票。

## 范围与实现

按执行主控 #3 转述的用户原话：“我们做缩进列表,然后在侧栏的话,竖着展示,然后这个横着的流程视图做一个单独的展示页面,展示现在系统流程.” 本轮只实现侧栏竖向树；不实现横向流程页，也不再采用“每列为派发批次”的展示假设。

- Herdr 启动／派发记录追加 `parent_launch`。可传 `--parent-launch`；未传时采用调用环境明确提供的 `A2A_LAUNCH`，没有则保存 null。旧记录不改写；启动阶段之间不能更换父 launch。
- 工作台原生主控经已认证 relay 发起派发时，后台以请求内的 AsyncLocalStorage 绑定实际调用者 launch；新 worker／审查员启动和派发记录带父 launch。操作员在现有 CLI 上可显式提供同名元数据，`controller_start` manifest 同样可提供，用于构思主控 → 执行主控关系。
- 侧栏使用启动字段与原有成功 assign 事实；只接受同项目的构思主控 → 执行主控 → worker／审查员／监视器关系。无记录、缺失父项、角色不符、跨项目、冲突、循环均不猜测归属。
- 竖向缩进、连接线、折叠按钮和全部后代状态计数；汇总沿用原状态优先级，等待用户回答时高亮。点击会话仍走原聚焦入口。
- 门禁请求的父字段在编排层摘除后再交原门禁；不改权限、操作锁、fence、CAS、attempt、派发文本标记、重放或恢复规则。侧栏继续只读。

Ubiquitous language 使用“父 launch”。Tracer bullet 覆盖记录 → 只读投影 → 侧栏；没有新增状态采集、策略引擎或平行门禁入口。Deep modules：沿用 Panes、OrchestrationStore 和原侧栏投影，不新增代理包装层。

## 已跑证据

详细命令、起点和结果见 [local-checks.json](local-checks.json) 与审查后的 [补测摘要](local-checks-02.json)，全部是摘要，没有截图或原始 run 目录。只读审查为 [INCOMPLETE](REVIEW-01.md)：未复现生产缺陷，缺少真实入口和最终版本绑定；后续补测没有复用该审查背书。

| 检查 | 结果 | 边界 |
| --- | --- | --- |
| 起点 `6411bdff8482ba47da207efa6a295a12666222aa` 反事实 | PASS | 同一新合同分别拒绝启动记录丢父字段、投影忽略父字段；不是环境失败 |
| 新层级合同 | PASS | 三级关系、三个子角色、旧记录、缺失父项、跨项目、自指、错角色、循环；全部后代计数；并发请求父字段不串用；显式父项与成功 assign 冲突、普通后续消息不改归属 |
| Python 启动／派发命令 | PASS | 真实命令进程，Herdr/Codex 为显式夹具；不连接真实 Herdr；每次只发送一次，历史启动字节不变 |
| 原 T-094 启动失败回归 | PASS | 9 项，54.141 秒；保留原错误、诊断、超时与启动单次调用检查 |
| 原 T-107 投影 | PASS | 12 组既有检查，保留原生根／辅助会话、未知状态、Git 与零写入约束 |
| main/preload IPC | PASS | 扩充父项与后代汇总穿透；原未知 key、外来窗口／frame、历史只读等拒绝检查保留 |
| 实际 daemon/socket/Panes/SQLite/trace | PASS | readonly、identity、filename、rollout 四模式；PTY 身份为受控输入，不证明模型行为 |
| 偷写事件变异 | PASS | 实际 sidebar 处理器的写入被全部表/schema/trace 比较拒绝，覆盖 F2/F3 |
| 忽略父项冲突变异 | PASS | 多个父项时仍采用第一个的变异被冲突反例拒绝 |
| 标准前端构建、diff 空白检查 | PASS | 内置盘临时槽；依赖是本 worktree 内 `npm ci --ignore-scripts` 的普通目录 |

真实模型根回合：0。运行时测试用的供应商行为不等同真实模型；未验证两种等待回答信号与 T-108 合并后的联动。

## 交给执行主控

1. Git 索引位于主仓库 `.git/worktrees/a2a-wt-t109/`，本沙箱无法创建 `index.lock`，`git add --sparse` 和 `git commit` 均退出 128；没有提交成功。先运行 [RUN-OUTSIDE-COMMIT.sh](RUN-OUTSIDE-COMMIT.sh) 在 `exec/t109` 代执行提交。脚本显式绑定本 worker 的既有 task／attempt／session／launch／native session，保留原钩子自动尾注；不是主控自己的角色绑定，不手写尾注，也不 push。
2. 再运行 [RUN-OUTSIDE-01.sh](RUN-OUTSIDE-01.sh)，将运行绑定到已提交代码版本；脚本记录 source HEAD 与相关源码改动，源码仍脏时不声称有完整候选版本。同一隔离库经原生派发入口与本地 C 接收器启动真实 PTY，再对比原版本红态与候选版真实 Electron 的三级缩进、折叠分类计数、构思主控汇总孙代、键盘展开、聚焦、窄窗和 sidebar IPC 零写入。脚本未运行，不能把这些断言当作通过证据。默认复用内置盘已有 Electron 43.4.1；可用 `T109_ELECTRON_DIST` 指定同版本目录。依赖仅从本 worktree 复制到私有夹具，不建链接；成功后自动清理它自己创建的构建槽和夹具。结果摘要需另行提交。
3. 合并时注意本票拥有 `sidebar.ts` 的树结构和 `renderer.tsx` 的侧栏树；T-108 仍由新状态模块接线。本票没有改变 `agentState` 的识别逻辑或问题面板。

地图 status 在开头与收尾均为 INCOMPLETE：8 条稀疏 checkout 缺失链接，0 条 stale living doc；原输出见 [project-map-status.txt](project-map-status.txt)。未改地图、术语表、票据或 AGENTS。须在完整 checkout 复核，不能写成 0 问题。

范围外发现：`workbench/src/panes.ts` 当前原生 worker 启动仍要求固定 `codex-cli 0.162.1` 与任务卡 `xhigh`。本轮沙箱外脚本仅对本地 C 接收器提供该既有字段，不会启动 Codex，也不据此声称符合用户新的真实 Codex `gpt-6.1-sol high` 运行口径；本票未改动这项既有约束。
