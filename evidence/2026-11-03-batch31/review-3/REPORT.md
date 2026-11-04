**NO_GO。** 本轮发现 T-243 的未确认退出路径仍可能留下后台和私有 core；T-242 的进程状态绑定也存在需要验证的异步时序风险。以下代码路径结论来自只读审查，没有运行故障注入；因此它们是待复现的缺陷声明，不冒称已有运行复现。

**阻塞意见**

1. **T-243：Electron 现场采集失败会跳过后台和 core 清理。** [test_electron_e2e.py:225](/Users/luckye/Documents/Code/a2a/workbench/tests/test_electron_e2e.py:225) 在进入停止后台及其 `finally` 之前调用 `capture_and_stop`。若 [electron_client.py:168](/Users/luckye/Documents/Code/a2a/workbench/tests/electron_client.py:168) 的目录创建、`ps`、现场写入或 `sample` 超时抛错，外层只记录 `cleanup_error`，不会执行后面的 `daemon_stop` 和 `stop_fixture_core`。这与 RESULTS 写明的“前面步骤失败也尝试停 core”不变式冲突。现有 [故障注入:20](/Users/luckye/Documents/Code/a2a/evidence/2026-11-03-batch31/T-243/forced_window_unconfirmed.py:20) 只让 `close()` 抛错，随后现场采集成功，未覆盖此反例。

2. **T-243：另一调用点在 `close()` 失败时不会执行新的未确认处理。** [test_t078_input_entry.py:239](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t078_input_entry.py:239) 将 `window.close()`、`capture_and_stop()` 和停止后台放在同一个 `try` 中。`close()` 抛错会直接跳到第 258 行的 `except`，既不记录窗口现场，也不结束 Electron 或后台；即使 `close()` 成功，后续 `capture_and_stop()` 抛错也有同样问题。该测试目前在夹具准备阶段失效，现有强制失败证据只针对 `test_electron_e2e.py`，不能证明这一调用点。RESULTS 中称两个调用点都会先记现场再清理，依据不足。

3. **T-242：异步前台检查可能清掉新进程刚报告的回合状态。** [panes.ts:596](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:596) 的 `foreground()` 跨异步调用读取进程；在它返回旧前台之后、执行第 599 行之前，新 CLI 的钩子可以通过 [panes.ts:502](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:502) 写入新 PID 的状态。随后旧检查以 PID 不同为由清掉该状态；如果后续没有新的钩子事件，界面会一直显示未知。现有测试在启动后刻意等待 8 秒才提交，未覆盖这一交错。另有短暂窗口：`status` 不提供 PID，侧栏仅比较 CLI 名称，旧进程的延迟事件可能短暂显示在同名新进程上。需要针对事件顺序取得反例或证明这些顺序不可能发生。

**非阻塞意见及证据限制**

- **T-244：安装目录不完整时，竞争处理会误认为已有成功安装。** [hcDistribution.mjs:53](/Users/luckye/Documents/Code/a2a/workbench/src/hcDistribution.mjs:53) 发现二进制不存在后解包；若目标目录已存在且非空、但缺少 `herdr-core`，第 60 行吞掉 `ENOTEMPTY` / `EEXIST`，第 64 行返回一个不存在的文件。调用方随后启动失败，而旧实现每次解包可重新放入文件。这是从代码推导的异常场景，尚未运行复现。
- **T-244 并发结论缺少直接证据。** [pin-change 测试:110](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t244_pin_change_e2e.py:110) 是先停后台再启动新固定值，证明了固定值切换时旧 core 的文件身份，并未并发首次安装，也未覆盖不同 `rename` 错误码。并发处理的正确性目前只能作代码判断；不应把现有绿态写成并发实测通过。旧 `hc/bin` 保留的设计从代码上可见，但这次固定值测试的绿态从新路径开始，未直接证明旧路径 core 的升级场景。
- **T-243 分类结论高于表中证据。** [RESULTS.md:60](/Users/luckye/Documents/Code/a2a/evidence/2026-11-03-batch31/T-243/RESULTS.md:60) 断言 26 个脚本没有一个能跑到验收检查，但表中包含“推断已失效、未运行”和需要授权、未运行的脚本；这些只能分类为未验证或推断，不能归为已证实不能运行。
- **T-244 有一份异常结果被删除。** [RESULTS.md:38](/Users/luckye/Documents/Code/a2a/evidence/2026-11-03-batch31/T-244/RESULTS.md:38) 明确记录了 `operator.json` 的 EEXIST 摘要已删除。这与保留异常结果的项目规则不符；当前无法独立核对当次失败。其余保留下来的固定值切换红、绿结果确实分别显示 `no holder` 和七项检查通过。
- **T-245 的反事实证据支持本次观察，但边界有限。** 保存的 t124 红态和反事实都检测到 marketplace 目录，绿态为 PASS；它们证明本机 Claude Code 2.1.317 及该夹具场景下的效果，不证明未来 CLI 版本仍识别这些内部字段。收尾目录检查也只能发现已创建的目录，不能单独证明一次失败的网络尝试从未发生。

T-242 的红态和清除状态变异体分别打到了所声称的“回合中未知”和“后续 CLI 沿用状态”；Codex 端到端仍未运行。有角色终端的既有回归记录为 PASS，普通终端提示词不进入状态库的检查有保存结果，但上述异步时序未被这些检查覆盖。T-243 的进程组结束前核对了 PID、启动时间和命令；本轮没有发现可据此断言它实际结束了非测试进程的证据。

T-244 新增的 `EEXIST` / `ENOTEMPTY` 捕获属于有条件的并发分支；T-243 新增了强制结束进程组的清理路径。未发现为产品行为保留第二套并行 API 的改动。

本轮未修改文件，也未运行测试、Electron 或项目后台。项目地图状态命令报告 **Problems 0、Stale living docs 0**，但运行时出现系统缓存写入受限提示；不影响上述代码审查结论。
