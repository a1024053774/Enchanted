# T-093 产品候选只读审查 01

STATUS: FAIL。候选 ff625c3718696cf31a7e9fd0d68e84bd2b0442b7；审查者为新只读会话 product_acceptance_review，使用 behavioral-acceptance-review。

P1：claudeLoginFacts.ts 的 safeTerminal 跳过 OSC/DCS 可见内容，却把控制负载原样返回；claudeLogin.ts 随后持久化到 pty.raw。独立随机凭据反例中，普通文本命中 0，OSC title、OSC8、DCS 各命中 1。未读取真实认证或运行供应商 CLI、ps、模型。

原有构造 4 项、合成文件 5 项、转发与事实 5 项仍通过，说明这些测试没有覆盖此缺陷。建议公开 trace 丢弃 OSC/DCS 负载，继续在内存处理原始终端协议，并对实际输出字节补充跨片段凭据扫描。

外部 daemon/PTY/sandbox 继承/hook/Stop/清理边界尚无本候选的全链结果，INCOMPLETE。preflight_observed=false 只能表示未识别到相应终端输出，不能证明没有官方地址访问尝试；事实范围不得外推为全部网络尝试。

实现者独立复现与审查一致。反例只保留类别与命中数，随机 sentinel 未持久化。失败候选和首次证据保留，后续修正另记，不上调本报告结论。
