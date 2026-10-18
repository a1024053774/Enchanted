# T-093 去掉 setuid ps 的前台查询交接 12

**INCOMPLETE：方案 b 已实现，局部红绿／SDK ABI 通过；同 C profile 的 primary、green 和正式六场仍待主控运行。**
候选绑定最后一行 `T-093 FROZEN <完整 SHA>`。
最终实现冻结为 7a5adebfcda47b10f28b8c51ecfc49dd7a490720；限定复核 [PROCESS-OBSERVER-REVIEW-02.md](PROCESS-OBSERVER-REVIEW-02.md) 认定 alias 的 L1 缺口已关闭，无新增阻断项，但整链仍为 INCOMPLETE。最终冻结相对此实现只补审查原件和文字，实际命令使用最后 FROZEN 的 SHA。
task T-093 / attempt a1，worker s16-t093；受管 session 67f986cc-92e4-4089-9c22-802a1143b645，native session 01a14ae2-a3df-7731-a7b0-1b679b3bce95，launch launch-45148b6732394eccab3b21224b238513。
冻结不代替 submit、独立验收或集成。本票没有真实 CLI、auth、上游或模型回合。

## 具体失败调用与选择

主控 #105 的实际回复已确认 orchestration_failed／Error: spawn EPERM，before／after 的 unknown、无 active／queue／writing／draft 完全相同。
唯一直接调用是旧候选 6f6e2820b 的 Panes.release（workbench/src/panes.ts:688）→ processInfo（398 行）→
`execFile('/bin/ps', ['-axo','pid=,ppid=,pgid=,tpgid=,comm='])`。
worker 只读 stat 再次确认 /bin/ps 为 04755；结合本次真实 spawn EPERM、此前同受保护环境启动该二进制被拒，原因已定位到该查询启动，不再猜队列／草稿。
原始返回和状态在 rehearsal-02-primary-summary.json；原结果／日志保留在主控指定的 /private/tmp 路径。

按主控允许的方案 b，直接替换这一查询，不分离 daemon，不给 CLI 或其后代新增权限。
C/F/D/G/V、HOME、网络、Security、fork、auth 复制规则全部保持；claudeLoginSession.py、claudeLaunch.ts、门禁均未改。

## 查询实现与身份条件

Panes.processInfo 现在启动非 setuid 的 `/usr/bin/python3 -I -S -B processSnapshot.py PTY_PID`，5 秒／4 MiB 有界。
该 helper 属于同一 C 继承链，登记实际 PID；无子进程、无网络、无 Security 调用、无文件输出。
通过系统 `/usr/lib/libproc.dylib` 读取：PROC_PPID_ONLY 的子 PID、PROC_PIDTBSDINFO 的父子／进程组／TTY 前台组／出生时间，以及 proc_pidpath 的可执行路径。
只遍历本 PTY 的树，不全机枚举，不读 argv／环境／auth。API 和结构以本机公开 macOS SDK 27.0 头文件及
[Apple libproc 源码](https://github.com/apple-oss-distributions/xnu/blob/main/libsyscall/wrappers/libproc/libproc.c)核对，没有第三方依赖。

固定上限 4096 个进程；缓冲填满／短数据／非法字段／权限错误／循环或父子关系变化都失败，禁止自动重试、fallback 或无保护查询。
ESRCH、已知僵尸／退出态可标为已退出，不能伪装成权限拒绝后的空列表。
查询和返回前复核 PID、父 PID、组／前台组与出生时间；多次内核读取不是原子快照，不扩大成未来存活保证。
产品仍要求 leader 的 PID=PGID=TTY 前台组，内核可执行路径等于实际启动边界记录的规范 executable_path；实际启动 argv 保留原值。后续 hook／Stop 的原身份重查不变。
Node 还检查 helper 协议、root、行字段、唯一 PID 和连通树；错误仍经 daemon.error／details 留证后清理。

实际 release 的 executor_action.process_info 记录观察方法／root；完整链导出为 counterexamples.foreground_process_query。
演练和独立核对器都要求方法 macOS libproc、root 等于该 PTY，且 leader 的组／前台组和编译假 CLI 路径匹配。
没有通过写 idle、跳过 release 或抹去拒绝来让链路前进。

## 局部证据与限制

- process-observer-red-02：当前真实 Panes.release 检查跑旧源码，11 场均命中禁止执行 setuid ps 的业务断言。
- process-observer-green-04：11 场通过，包括随机 PID、拒绝／坏协议／错父／背景组／错路径／空树／缺 root／错 root／leader 被替换；exec 边界模拟，未实际查询 PID。
- process-snapshot-green-03：23 场合成 native 缓冲／进程树检查及 SDK 静态 ABI 编译；BSDInfo 大小 136、关键偏移与退出常量匹配公开头文件。没有执行 libproc 查询。
- process-snapshot-mutant-01：将权限拒绝当空 child 列表的坏实现被 `bad_native_observation_must_fail: denied_children` 拒绝。
- conflict-panes-green-02：四项旧 pane 生命周期／转交场景通过。其首轮 writes.then 缺字段在旧产品＋旧测试也重现（conflict-panes-parent-01）；本次只补现行写入队列字段并更新模拟查询协议，原业务断言未删改。
- daemon-rejection-green-04／chain-publication-green-06：返回原因留证和主失败先落盘仍通过。parser-red-03 保留测试提取范围误含 TypeScript 注解的失败；修正提取边界后再通过。

以上为 L1 及 SDK 编译，不能证明本机 C 下 libproc 的实际读权限或整链成功；worker 没有尝试嵌套 sandbox、ps／pgrep 或真实进程探测。

首轮实现冻结 3fca92984443d0954f1fda8fbe0ba68230c66dcc 的只读审查为 FAIL，原文 [PROCESS-OBSERVER-REVIEW-01.md](PROCESS-OBSERVER-REVIEW-01.md)。
它发现旧假 API 入口的合法绝对 alias 与新内核路径语义不同。现在真实 startController 在版本校验后、PTY 启动前保存 executable_path=realpathSync(input.executable)，Codex 继续使用其原本已规范化的路径；不改变实际 argv。
process-alias-red-02 在首轮冻结上复现合法 alias 被误拒，green-02 通过真实 start/release 的 alias 正例和启动后指向另一目标的拒绝；执行／PTY／内核返回都为模拟。
把“启动时捕获”改成“每次查询重新解析 alias”的变异会错误接管不同目标，被 process-alias-mutant-01 的业务断言拒绝。
version-boundary-green-01 保留原版本／并发检查，conflict-panes-green-03 保留旧生命周期／转交断言；仍没有实际 CLI 或内核查询。

## 沙箱外先跑新的 primary

旧残留已清理，本轮不再清理既有夹具。使用新输出，不覆盖前两场。

```sh
repo=/Users/luckye/Documents/Code/a2a-wt-t093
candidate=替换为本次完整冻结SHA
bash "$repo/evidence/2026-10-16-batch16/T-093/REHEARSE-CHAIN-01.sh" \
  "$repo" "$candidate" /private/tmp/t093-rehearsal-03-primary.json primary
```

期望 rc 2、INCOMPLETE，但 primary_failure 必须恰为 rehearsal_primary_probe、upstream_requests=2、cleanup_failures=[]、fixture_removed=true。
释放前台身份必须由 counterexamples.foreground_process_query 的实际观察支持，新的查询子进程须在 processes.C 登记。
若错误不同或缺任一收尾证明，立即停止后续场景；回传 error_summary.daemon_response／error_summary、counterexamples.pane_release 和 foreground_process_query。
不允许因此放宽 CLI profile、改用无保护查询或启动真实回合。

primary 达到预期后，再用同一脚本运行 `/private/tmp/t093-rehearsal-03-green.json green`，之后：

```sh
python3 -I -S -B workbench/tests/check_t093_chain_results.py --rehearsal --candidate "$candidate" \
  --output /private/tmp/t093-rehearsal-03-check.json \
  /private/tmp/t093-rehearsal-03-primary.json /private/tmp/t093-rehearsal-03-green.json
```

绿态和 V 核对都须 rc 0／PASS；通过后才继续请求 10 尚未执行的正式 chain-07 六场及独立核对。JSON 和同名 .events.jsonl 全部保留。
