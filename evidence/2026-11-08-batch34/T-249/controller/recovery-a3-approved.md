# T-249 第四次派发的运行时恢复

2026-11-08。此记录由执行主控写入，不替代用户原话。

用户对本轮问题“T-249 的候选与测试证据已保存，但新发现的启动超时状态使交付和回收都被门禁拒绝。是否批准正常重启 Enchanted 后台，再经门禁回收这次 attempt、用 astra xhigh 重派接回候选继续审查？”明确回答：

> 批准重启并经门禁恢复（推荐）

候选 9f96a9121ba6ed8d77a514a0a78c9341ceaacb86 与三份原请求已经保存，原 worktree 干净。新缺陷登记 T-258，未修改产品代码。先退出正式 UI；第一次 daemon_stop 未加载桌面生命周期凭据，被 caller_identity_required 拒绝，保留原收据；随后通过标准桌面凭据加载函数正常停止后台 36212。确认旧后台、shell 40370、CLI 40372 均退出且 socket 消失，再启动同一正式安装包；新后台 81233，UI 显示“后台已连接”。executor 角色仍是用户此前批准的原角色，没有重新签发或自行批准角色。

旧 attempt 27481daa-4502-44a9-873e-c00a7b1cab4a 此时 stopped=true、active=null、queued=[]，恢复拒绝为 restore_managed_attempt_requires_reclaim；经唯一门禁 reclaim 成功，任务 ready。原失败证据和未处理请求不重放；新 v5 卡接回完整卡内 diff，以新身份提交并重新验收。

派发前逐项核对：顺序仍为 T-257 完成后 T-249，再 T-250；worker 和 reviewer 均 gpt-6-astra xhigh、普通速度；显式 dispatch、submitted 后 verify、敏感证据用户批准后 integrate；不使用 run、不启动 Claude、不 push。真实窗口层必须用新打包的隔离 Enchanted Test，no-panel/parents/order 业务变异均判红，再由 gpt-6.1-terra Computer Use 加常规测试验收；正式后台前后 PID/启动时间应一致，构建缓存与夹具及时清理。新卡不扩大路径、权限或验收条件。

恢复操作 PASS；T-249 交付及整票验收 INCOMPLETE。重启没有证明 T-258 已修复。
