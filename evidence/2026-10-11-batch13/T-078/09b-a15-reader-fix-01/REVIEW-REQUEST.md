# 完整只读 reader 候选的独立审查请求

候选为 `../09b-a15-reader-harness-01/manifest.json` 绑定的源码提交及新 reader harness，不是整场 09B 验收。业务加载源码仍为 dedd4f66bc424610183cbff2d7114e991483e1c6。

请在全新只读上下文检查：三个调用是否共用完整分页，缺页/total 变化/零进度/最终 EOF 变化是否拒绝；E4 恢复是否保留旧原件与实际 dispatch/permission_event，原前缀不符是否拒绝；新 source freeze 是否仅允许三条既有 reader 修改、其余原包逐字节相同；命令是否不会在签字前送键；本轮声明是否限于 reader/夹具证据。

本 worker 遵守“不要同时开额外 Codex/子代理”，没有自行启动独立 reviewer。[behavioral-acceptance-review](/Users/luckye/.agents/skills/behavioral-acceptance-review/SKILL.md) 要求 “Review one frozen candidate snapshot in a fresh, read-only context.”；此项独立审查状态为 INCOMPLETE，不能用 worker 自己的检查替代。请由主控安排；本文件不声称已获独立 PASS。

已有证据：真实 P1 screen 参数入口的原红/候选绿、只读一页坏实现；实际 permission CLI 的 check-only 入口和不完整捕获拒绝；phase execute 截图分支原红/绿；恢复前缀检查的坏实现。输出传输使用确定性夹具，身份在沙箱内用 spy；真实身份外侧复验命令另给。A-15 的恢复与后续许可未执行。
