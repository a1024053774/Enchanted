STATUS: INCOMPLETE
TARGET: 20aa73e83479392841c726781a9f61be77f62da7（对比 5d096caa2d690fe172ba8487226e8b16cf95950a）

EVIDENCE:
- 审查前后 HEAD 未变、工作树干净；diff 检查通过；project-map 为 0 problems、0 stale。
- `workbench/src/panes.ts:87` 在实际托管启动边界探测配置路径；`:94` 比较版本，之后才登记 launch、创建 PTY。`workbench/src/daemon.ts:225` 正确等待完成，再注册主控。
- 无文件写入的内存探针通过：缺路径、探测失败、错版本、配置版本变化、单次探测及并发唯一占用。额外计数确认缺路径与错版本没有 launch／PTY 副作用。
- `run_regression.py:54` 使用停机前导出的事件，收集所有 daemon 代次、shell、receiver、Electron；`:130` 确认登记 PID 消失后归档。对三份真实 -01 读回文件重放收集成功，包含 input-failures 的两代 daemon。
- 四份业务断言源码与冻结基线逐字节一致；历史配置夹具的相关差异仅补 version。window 驱动保留整页 text 的纯逻辑检查通过。
- 直接回读外置盘：五类 -01 顶层均为 INCOMPLETE；runtime／input-failures／worker-inbox 原测试分别 12／11／14 项 PASS。
- 三格脚本静态路径符合两个主控、串行 receiver、一个 Electron、真 Codex 新增 0、模型回合 0、loopback 假 API、无 auth 复制及限定输出预算。T-091 Resolution 保留 2.1.296／2.1.302 差异，ticket 仍 open。

FINDINGS:
- 未发现本范围内可确定复现或静态可达的违规。

COUNTEREXAMPLE:
- 删除生产版本比较后，在“Configured version mismatch must be rejected”业务断言失败。
- 旧固定路径实现拒绝外部指定路径；旧驱动未保留整页 text，被独立输入拒绝。
- 删除 daemon 代次收集的变异被独立 PID 集合拒绝；缺失 live readback 同样拒绝。

LIMITATIONS:
- green-02、真实缺路径／错版本拒绝及五类回归 -02 尚无实际边界证据，不能判 PASS。
- 本轮仅取得 L0／L1 与历史材料重放证据；未启动供应商 CLI、daemon、PTY、Electron 或 ps，未修改文件。
- 编排、异步、身份、交互、文件、副作用和运维均适用；当前候选的真实启动、窗口及归档收尾仍待主控实跑。检索／记忆为 N/A，本变更不涉及该能力。

来源：fresh 只读工具子会话 `/root/version_wrapper_acceptance_audit`，请求配置 gpt-6.1-sol／xhigh；未启动原生 reviewer CLI，不冒称实际供应商 tier，不能替代门禁的最终独立审查。审查结束后仅保存本报告及交接记录，没有更改被审查的产品或脚本。
