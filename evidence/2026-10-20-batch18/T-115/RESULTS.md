# T-115 断连重连后前台 Dock 角标失败：重复取证

2026-10-21，worker s18-t115，task T-115 / attempt a1。起点 `main`（稀疏 worktree
`exec/t115`）。本轮不调用模型、不运行 Electron、不 push、不改 T-110 的提醒语义或断言。

## 目标与非目标

- 目标：在事先固定的 CPU 负载和重复次数下运行 T-110 真实入口，取得
  `Foreground after reconnect clears badge` 失败时的完整 `native_focus_timeline`；或按固定次数
  如实记录未复现。
- 非目标：不判断自然负载是唯一根因；不先加产品重试、不延长 T-110 等待期限、不放宽任何断言。
- 当前未知：历史失败原件没有焦点时间线；现有成功例从 `foreground` 命令返回到焦点事件约 19ms，
  不能据此认定失败只是超时。

## 固定运行条件

以下条件由 `RUN-OUTSIDE-REPEAT-01.sh` 写死，运行前不得按结果调整：

- 负载：在 10 核机器上启动 10 个 `/usr/bin/python3 -B -c 'while True: pass'` 忙循环。每个子进程
  用 `start_new_session=True` 启动，稳定 15 秒后开始测试；脚本结束时对每个自有进程组先
  `SIGTERM`、必要时 `SIGKILL`，并记录 PID、PGID 和回收状态。
- 次数：完整入口最多运行 10 次；一旦某次 `green` 命中
  `Foreground after reconnect clears badge` 且不是 PASS，立即停止，失败后不继续增加次数。
- 单次时限：1800 秒。超时记为该次 INCOMPLETE，不冒充目标失败。
- 每次输出：`/private/tmp/<fresh-run>/attempt-01.json` 到 `attempt-10.json`，每次使用新路径；
  对应 stdout/stderr 是同编号 `.log`。
- Electron：固定使用内置盘的
  `/Users/luckye/Documents/Code/a2a/workbench/node_modules/electron/dist`，版本必须为 43.4.1。
- 入口：

```sh
/usr/bin/python3 -B workbench/tests/run_t110_notifications.py \
  --electron-dist /Users/luckye/Documents/Code/a2a/workbench/node_modules/electron/dist \
  --summary /private/tmp/<fresh-run>/attempt-NN.json
```

选择 10 个忙循环，是因为历史失败发生时机器自然负载约为 10，且本机为 10 核；选择最多 10 次，
是为了在相同量级负载下获得重复证据。它们是事先固定的采集参数，不构成失败率、可靠性或因果结论。

## 判定与归因规则

- 只有 `green` 的失败文本包含 `Foreground after reconnect clears badge`，才算目标现场；启动失败、
  依赖错误、其他红态异常和单次超时都不算复现。
- 汇总器提取该次 `green` 的完整 `native_focus_timeline`，以及最后一次 `foreground` 命令之后的
  时间线和 `failure_view.native_focus`。
- 最后一次前台动作后窗口保持 `focused=true`、`focused_window` 非空，但角标仍为 1：归入
  产品或原生事件路径；修复前必须保留这份红态，修复后用相同 10 个忙循环复跑取得绿态。
- 窗口没有取得焦点，或取得焦点后又失焦：归入测试动作完成条件；修测试动作，不加产品重试，
  不只延长等待。T-110 断言保持不变。
- 10 次都完成且没有目标失败：状态为 `NOT_REPRODUCED`，按票面验收只能报 INCOMPLETE；若混有
  超时或非目标入口失败，汇总状态为 `INCOMPLETE`，不能宣称“未复现”。

## 当前状态

**INCOMPLETE**。脚本和固定条件已写入，但 Electron 真实入口按任务书只能在沙箱外交给执行主控
运行；worker 尚未取得新的失败时间线，因此本轮没有归因结论，也没有修改产品或测试。

运行前安装本 worktree 自己的依赖：

```sh
cd /Users/luckye/Documents/Code/a2a-wt-t115
unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE
LC_ALL=C npm ci --ignore-scripts
```

运行重复取证（输出目录必须不存在）：

```sh
cd /Users/luckye/Documents/Code/a2a-wt-t115
zsh evidence/2026-10-20-batch18/T-115/RUN-OUTSIDE-REPEAT-01.sh \
  /private/tmp/t115-repeat-01
```

运行后先看：

```sh
python3 - <<'PY'
import json
from pathlib import Path
p = Path('/private/tmp/t115-repeat-01/summary.json')
d = json.loads(p.read_text())
print(json.dumps({
    'status': d['status'],
    'attempts_completed': len(d['attempts']),
    'load': d['load'],
    'target_failure': None if d['target_failure'] is None else {
        'attempt': d['target_failure']['attempt'],
        'classification': d['target_failure']['classification']['classification'],
        'timeline_entries': len(d['target_failure']['green'].get('native_focus_timeline', [])),
    },
}, ensure_ascii=False, indent=2))
PY
```

原始大文件和逐次日志保留在 `/private/tmp/t115-repeat-01`；只把失败摘要、完整时间线和最终
命令/环境摘要带入仓库，不复制 fixtures。

## 地图状态

`project_map.py status --root .` 当前报 8 个问题，均为该稀疏 worktree 已存在的未检出链接
（`findings/*` 与 `.grilling/a2a-gui-client.md`）；stale living docs 为 0。T-115 仍在 frontier。
本节不把这些已知稀疏缺口写成 0 问题，票面的最终 0 问题门禁仍需在完整 checkout 或 T-115
后续执行完成后核对。

## 执行主控运行结果（2026-10-21）

候选 691235cad，命令 `zsh evidence/2026-10-20-batch18/T-115/RUN-OUTSIDE-REPEAT-01.sh /private/tmp/t115-repeat-02`，在沙箱外运行。摘要见 `repeat-02-summary.json`。

- 前三次运行无效，原因都不在产品：
  - repeat-01 第一次：脚本的 TASK_ROOT 多上了一层目录，已在 9e996e020 修正；
  - repeat-01 第二次：工作区有未提交改动，脚本拒绝运行，已在 f084fca56 提交；
  - repeat-01 第三次：10 次全部报 controller_version_mismatch。Claude CLI 已自动升级到 2.1.306，夹具却写死了 2.1.304。691235cad 改为运行时读取已安装的版本，门禁的版本一致性检查不变。
- repeat-02：10 个 CPU 忙循环；启动后负载约 9.6，结束时约 45。
  - 目标失败“Foreground after reconnect clears badge”：0/10，没有复现。
  - 7 次完整 PASS：四个红态都被拒，green 和 disabled 都 PASS。
  - 3 次因为别的原因中止，都与目标无关：
    - attempt-01：一个红态运行结束时，Electron 窗口清理在 10 秒内没有完成（window_cleanup_error），整次中止；
    - attempt-05、attempt-06：t110_notifications_scenario.py:37 读 `before_highlight['agents'][agent_id]` 抛 KeyError。高负载下，这个 agent 在“高亮前快照”之后才出现在侧栏里，这是测试的快照时机问题。
- 失败时间线：所有记录到的前台事件都是先 did-become-active（badge=1），约 5 ms 后 browser-window-focus 让 badge=0，与 T-112 审查 02 记录的成功路径一致。没有观察到“持续 focused=true 而 badge=1”。

结论：INCOMPLETE。在约 10～45 的负载下跑 10 次，目标失败没有复现，所以没有归因，也没有改产品或断言。另外记下两类高负载下的测试夹具不稳定（窗口清理超时、高亮前快照缺少 agent），作为后续测试改进项。
