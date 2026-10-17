# 主控 #357：09C 跨进程时钟修复

状态：**本机跨进程 C-I2 入口红绿 PASS；跳变拒绝与条件式 Enter 回归 PASS；完整链排练仍 INCOMPLETE，待主控沙箱外复验**。本次只改 workbench/tests 与本票证据，不改产品代码、protocol、预算、1000ms 跳变阈值或 >120/<150 秒边界。未启动 daemon/API、Electron、角色 CLI 或模型；只启动并等待退出了确定性的 Python 时钟测试子进程。

## 原现场能证明什么

[主控 real-chain-outside-02](../09c-fix-01/real-chain-outside-02/result.json) 原样保留：C-I1 许可识别、Enter、真实 queued→Stop/relay→delivered 与结算已通过；C-I2 在按键前 `check_early_C_permission` 报 `clock_discontinuity`，该命令总耗时0.369640167秒。cleanup PASS、root已删。原件有 ideation 3 POST（C-I1两条、C-I2首条均200/complete）；executor首条请求尚未完成，不能把本次排练判为通过。

[证据字段清单](clock-evidence.json) 区分实际记录和缺失值：

| 字段 | 保存下来的值与来源 |
| --- | --- |
| 原 stop | `35d2d003-9209-4d5d-843b-6d1e9165b59b`，created_at `2026-10-17T00:00:28.707Z`，C-I1 `execute-02/settlement.json` |
| C-I1结算末采样 wall_ms | `1792195229244.405`，同一原件的 observed_time |
| 同次 monotonic_ms | `3684.8457909999997` |
| 同次 observed_elapsed_ms | `192.9561249999997` |
| origin.mono_ms | 从上两项相减得到 `3491.889666`。这是推导值，不冒称保存的 clock-origin 原件 |
| origin.wall_ms / initial_age_ms / writer PID | **INCOMPLETE**。旧清理未复制根级 `clock-origin.json`，原件已随 scratch 删除 |
| C-I2失败瞬间 wall/mono | **INCOMPLETE**。旧异常只有错误名、没有保存采样；不能用这次本地复现值冒充旧场景读值 |

调用链明确是两个 Python 命令进程：C-I1 permission 主进程经 phase_driver 转交 C 的 `settle_stage`，调用 `origin(Clock())`；之后新启动的 C-I2 permission 主进程从文件读取 start，再调 `timing(start, Clock())`。wall 都来自 Python `time.time()*1000`，旧 mono 都来自 Python `time.monotonic()*1000`；没有序列化 Node `performance.now` 或 hrtime。

本机实际解释器是 `/Library/Developer/CommandLineTools/usr/bin/python3`，Python **3.9.6**。其 macOS `time.monotonic()` 实现会减去各进程自己的 `t0`；这点见 [CPython 3.9.6 源码](https://github.com/python/cpython/blob/v3.9.6/Python/pytime.c#L771-L821)。[Python 官方文档](https://docs.python.org/3/library/time.html#time.monotonic) 明确记录 macOS 到3.10才改为跨进程同一时钟。因此两个进程中的“启动后几秒”不能直接相减，旧 guard 把基准不同识别成了跳变。

## 红绿与拒绝语义

[clock-red-01](clock-red-01/result.json) 先在修复前实际运行。真实 writer 睡眠1.25秒后经 `origin(Clock())` 写文件，另一个新进程调用真实 `check_early_C_permission`；只有已单独覆盖的原 stop/请求查询替换为固定绑定，不模拟时钟、文件或进程边界。实际记录：

| 采样 | 值（ms） |
| --- | --- |
| writer origin wall / mono | `1792195415922.46` / `1344.262541` |
| reader C-I2 wall / mono | `1792195416050.155` / `97.785416` |
| wall耗时 / mono耗时 | `127.695068359375` / `-1246.4771250000001` |
| 差值 | `1374.1721933593751`，旧入口错误拒绝 |

最终测试器另外加载 Git `43d757413c393a858e4666a3c3a642fd0d618bfb` 的原始 driver，得到 [clock-known-bad-01](clock-known-bad-01/result.json)，同因拒绝；源码保留在该目录，没有回退工作树。

最小修复是 `Clock.mono()` 直接取系统 `time.clock_gettime_ns(time.CLOCK_MONOTONIC)/1000000`，不再经过 Python3.9 的进程局部偏移，不加旧时钟兼容或重置起点。origin 一次采样 wall/mono，记录实际observer PID和clock类；`timing` 的原条件 `elapsed>=0 && abs(wall_elapsed-elapsed)<=1000` 不变，异常增加原start、当次两读值/耗时/差值/PID，便于下一次原样核对。清理前额外逐字节保存 `clock-origin.json`，停机后仍不读活SQLite。

[最终 clock-green-03](clock-green-03/result.json) **PASS**：writer PID79957、reader PID79966；origin wall/mono=`1792195523594.989` / `234340654.37`，reader=`1792195523721.955` / `234340781.324`；两耗时只差约 **0.012ms**，真实 C-I2 检查通过。green-01/02也是实际PASS，均保留。辅助进程全部自行退出，零端口/业务按键/模型。

同一测试有8项独立边界检查：±1000ms仍允许，±1001ms拒绝，mono倒退拒绝，超过150秒拒绝，原stop不符先于采样拒绝；时间差反例明确是注入值，没有改本机系统时间。真实清理函数的无进程夹具也已实际执行，origin逐字节留存且自有scratch删除。

既有 [permission-regression-01](permission-regression-01/result.json) **32项 PASS**：条件式 Enter 遇时钟跳变零键；去掉时钟检查的已知坏变异会提前写键，被现有独立断言捕获。此组使用注入时钟/window spy，不算真实120秒证据。[recorded-regression-01](recorded-regression-01/result.json) **6项入口检查与6项绑定正反例 PASS**，含迟到C-I2零进程/窗口/键拒绝、重复输出原结果不变与原caller/request/stop核对。

## 重现与完整排练

```sh
python3 -B workbench/tests/test_t078_09c_cross_process_clock.py --known-bad-revision 43d757413c393a858e4666a3c3a642fd0d618bfb --output /private/tmp/t078-c357-clock-red-new
python3 -B workbench/tests/test_t078_09c_cross_process_clock.py --output /private/tmp/t078-c357-clock-green-new
```

本机3.9.6上第一条预期exit1/clock_discontinuity，第二条exit0/PASS；输出目录必须全新。scope是原生操作系统时钟跨Python进程证明，不是完整relay或角色CLI证明。

[REHEARSAL-03-COMMAND](REHEARSAL-03-COMMAND.txt) 输出到全新 `09c-fix-01/real-chain-outside-03`；[静态预检](real-chain-preflight-01/preflight.json) 已在worker会话实跑PASS，仅检查路径/AST，不起现场。主控沙箱外完整排练仍用真实daemon/inbox/Stop/relay/HTTP/Electron、确定性PTY角色，模型0，真实C-I3 >120秒、整场<150秒、外层420秒硬超时；任何不一致首败停止，不重试不确定键。未执行该命令，未冻结或启动09C第2场，未做新的独立审查，整票状态不上调。
