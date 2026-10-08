# T-039 修复验收计划（2026-10-08）

授权来源为上一层 controller-decision-01.md。目标是原生观察接缝分类与受控中断回收；非目标为修改门禁核心、合同、provider 实现或 T-038。已有 run-01、BLOCKED 和独立审查 FAIL 保留不变。

observed：原生投影查询属于 SQLite transaction；ProviderService.listSessions 汇合各 adapter 内存快照和绑定查询。当前两个接口没有共同原子快照，不能仅将它们放入 Promise.all 就声称一致。

选择：仅在现有观察转换处识别 shell 没有 turn 的输入，保留 turn=null，报告仍在运行，沿原 run deadline 再观察；submit 仍要求实际 turn 相等，所以尚未投影时不能交付。interrupted 且 provider 已退出时可以报告停止；有活跃 provider 的矛盾中断状态保持未知并拒绝。后续 stop/archive 仍由原受锁路径执行并读回。

测试预期来自主控决定，而不是实现。受控替身只给 shell/provider 外部输入，门禁、SQLite、Git 操作和调用入口均为真实代码。单独测试前列出的失败方式：

- 尚无投影 turn 时误判 identity_conflict；擅自绑定 provider turn；交付或推进 oracle/CAS；持续尚未投影却绕过原 deadline。
- 中断后无法回收；未 stop 就 archive；回收未确认就写 reclaimed；原 run 把中断当成功。
- 两侧 turn 不同、thread/cwd/provider 不同或多个 provider session 时未拒绝，或拒绝后仍停止、归档、变更门禁事实。
- error、缺少活跃 provider 的 running 投影、仍有 active turn 的 interrupted 状态被当成已停止。

先在 fa3fc33 上运行新增服务测试，保留缺陷特定红态；最小修改后运行同一测试，再重跑 T-037 的18项与T-036的17项及规定检查。冻结新候选后使用本目录下全新 real-01 证据与 /tmp 根做真实闭环。前后只读记录用户 config/rules 元数据、Synara 顶层数据与 herdr status；不复制凭据。最终新的 fresh-context 独立审查同时核对行为与结构风险。
