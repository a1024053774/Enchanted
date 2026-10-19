STATUS: INCOMPLETE
TARGET: e5b8329e4f7d0c8104b7e666c346531357612372（base: 7bba61000d8ae5b643135b58111768a403a5d04c；仅 controller #126）
EVIDENCE:
- L0/L1 局部 PASS。独立输入为新端口 39524、nonce 3e2291a15529ef；未运行作者新测例作为验收 oracle。生产 main 的实际解析器拒绝 --upstream-port，并显式向 prepare 传 443；同一 policies 函数仅改变 F 的出站端口，C/D 与其余 F 规则相同。实际 Bash wrapper 的默认 18443 与自定义端口，均传给编译、链路和核对器。
- python3 -I -S -B /private/tmp/t093-independent-18-dtl3h7qr/probe-v2.py：exit 0；源生成、生产解析器、wrapper、实际 U listen/finally 共 13 项记录。证据：/private/tmp/t093-independent-18-dtl3h7qr/python-result-v2.json。U 零监听、部分监听、正常关闭及关闭错误继续遍历均通过；绑定主错误与关闭错误分开保留。关闭收据发布失败的注入仍留下原 startup-failed 收据，不产生关闭确认。
- /opt/homebrew/bin/node /private/tmp/t093-independent-18-dtl3h7qr/cleanup-probe-v2.mjs：exit 0，12 项 PASS。实际 C upstream callback 与 finishChain 使用 supplied PID 查询，拒绝缺收据、all_closed=false、关闭计数不符、错误 PID/组、非法监听数量、持续 EPERM/alive；EPERM→alive→ESRCH 只在 ESRCH 后确认，所有 checkpoint 保留原业务失败。证据：cleanup-result-v2.json、node-run-0.json（均在同目录）。
- /opt/homebrew/bin/node --experimental-vm-modules /private/tmp/t093-independent-18-dtl3h7qr/host-probe.mjs：exit 0，4 项 PASS。实际 forwarder handler 使用全新 configured/other 主机名；输入 Host 不改变目标，非配置目标和 lookup 主机均无连接启动并记 upstream_host_mismatch。证据：host-result.json、node-run-1.json（均在同目录）；journalRoot 记录于 host-result.json。
- 已逐项检查 diff：原 HOME、Security、fork、CLI bypass、app-host、重试/计数、凭据断言保留；端口反例改为另一个已配置 live listener，后续真实 OS 运行仍须证明拒绝该端口。生产事实字段为 [443]，测试事实字段为实际测试端口；os_host_filter=false 的表述准确。
- 结束 HEAD 仍为目标 SHA，tracked diff exit 0，原 12 个未跟踪文件列表未变；project_map.py status exit 0，Problems 0 / Stale living docs 0。原始命令与输出：/private/tmp/t093-independent-18-dtl3h7qr/state-final.json。
FINDINGS:
- 本限定范围内未复现候选缺陷；局部 PASS 只覆盖 L0/L1，不能批准真实 OS 或整票验收。
COUNTEREXAMPLE:
- base 7bba61000 的 F 硬编码 443 被新端口业务断言拒绝；跳过实际 server_close 但保留计数的 mutant 被端点关闭断言拒绝；EPERM→已退出 mutant 被关闭确认断言拒绝；移除应用主机两道检查的 mutant 被“非配置目标不得启动 transport”断言拒绝。均为业务断言失败，不以依赖缺失或崩溃冒充检出。
LIMITATIONS:
- 本轮不执行 OS profile 编译、真实网络/端口拒绝、真实 CLI/鉴权/Keychain/模型、daemon/service、kernel PID/libproc/ps 或旧夹具操作。OS 编译、新端口完整无模型链、native7 均为 INCOMPLETE；V 的真实 guarded 入口未运行，静态检查不能代替它。
- 能力轴：编排状态、异步结束、身份/作用域、CLI、文件证据、外部鉴权与运行清理适用，以上仅测限定纯逻辑；检索/记忆 N/A（本范围无检索）。supplied server/transport/PID 查询不能证明 OS 沙箱、真实内核进程退出或供应商 CLI 行为。
- 首轮独立探针误把 F 的 deny file-read* 预期为 deny file-read-data；保留 probe.py 与 python-result.json（exit 2），修正为实际需求后另存 probe-v2.py/python-result-v2.json。cleanup-probe.mjs 首轮因工具对顶层 return 的解析限制在执行候选前失败，另存 v2。两项均属审查工具错误，未作为候选缺陷或反例。
RULE:
- 不适用：本轮未发现需要新增治理规则的重复候选缺陷。
