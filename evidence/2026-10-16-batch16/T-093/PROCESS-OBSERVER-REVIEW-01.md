STATUS: FAIL
TARGET: 3fca92984443d0954f1fda8fbe0ba68230c66dcc（基线 6f6e2820b58012e6d247f648ae073993fb5a4bd2）
EVIDENCE:
- 独立重跑 process_observer、process_snapshot、daemon_rejection、chain_publication：11＋23＋3＋5 项通过。原件位于 `/private/tmp/t093-review12-omya_bc3/{observer,snapshot,rejection,publication}.json`。
- L0：同一 daemon 继承 C；profile、claudeLoginSession.py、claudeLaunch.ts、门禁未改。查询错误向上传播；未发现权限拒绝被当成空树的路径。
- L1：权限拒绝、短数据、截断、身份变化、错误树和 leader 替换均被拒绝；SDK ABI 编译通过。
- 旧 `comm` 读取 argv[0]：[Apple keyword.c:96](https://raw.githubusercontent.com/apple-oss-distributions/adv_cmds/main/ps/keyword.c)、[Apple print.c:190–237、390–391](https://raw.githubusercontent.com/apple-oss-distributions/adv_cmds/main/ps/print.c)。新查询读取内核可执行路径。
- 能力轴：编排/状态、异步执行、身份/范围、CLI 交互、故障处理适用；检索/记忆、业务文件媒体、外部业务写入为 N/A。
- 开始及结束 project-map status：0 problems、0 stale living docs；HEAD 未变。
FINDINGS:
- [P1] workbench/src/panes.ts:413 — 查询结果已从 argv[0] 改成内核可执行路径，但仍直接比较 launch.argv[0]。假 API `claudeLaunch.ts:57、68` 接受绝对符号链接且原样启动、记录，合法 alias 因而得到 leader=null，release 拒绝。正常登录和 Codex 已处理规范路径。应在实际 Claude 启动边界确定规范可执行身份，并用它比较，保留实际启动 argv；增加 alias 正例及不同目标反例。
COUNTEREXAMPLE:
- 合法绝对链接 `/private/tmp/.../claude-alias` → `/private/tmp/.../claude-real`：启动入口接受 alias；内核观察返回 real；当前比较拒绝此前允许的启动。这是可达的静态契约回归，现有绿测没有覆盖。
- 既有 `process-snapshot-mutant-01.json` 中“权限拒绝返回空 children”的坏实现被明确业务断言拒绝；本次权限拒绝合成场景亦通过。
LIMITATIONS:
- 完整链路及 C 权限边界：INCOMPLETE；真实 libproc、same-C primary/green、正式六场均 NOT_RUN。
- 未运行任何真实 PID 查询、sandbox-exec、供应商 CLI、认证、网络或模型。42 项通过只支持 L1；不能关闭真实 spawn EPERM 缺陷。
- 本次未执行真实符号链接进程；该 finding 依据允许的启动输入、确定的数据流及 Apple 原始实现语义。
RULE:
- N/A：本次未确认该 finding 属于重复失败类别。
