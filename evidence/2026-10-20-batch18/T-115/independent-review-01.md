# T-115 独立审查 01

- 审查对象：仓库 `/Users/luckye/Documents/Code/a2a-wt-t115`，分支 `exec/t115`，候选 `1796d1b79`，起点 `fc06fe80a`。
- 审查范围：只审 `git diff fc06fe80a 1796d1b79`，并核对 ticket、`RESULTS.md`、`repeat-02-summary.json` 及已有 `/private/tmp/t115-repeat-02` 原始结果。
- 审查方式：只读检查；本回合不修改候选、不提交、不推送、不调用模型。执行主控另行提供的 `test_t110_cleanup.py` 结果为 PASS、33 例；`test_t091_claude_version.mjs` 结果为 rc=1，因 `Unexpected module boundary: ./executionSettings.ts` 在候选和 `main` 上同样失败，按范围外既有问题处理。

## 总结

没有发现本票削弱 Claude 版本一致性门禁或清理身份核对；重复取证脚本也确实把中止运行归为 INCOMPLETE，而不是“未复现”。`RESULTS.md` 的主结论 `INCOMPLETE` 是诚实的：目标失败没有复现，没有归因，也没有修改产品或 T-110 断言。

但本票仍未达到完成条件：目标失败未取得现场，没有归因或修复；`project_map.py status` 仍有 8 个问题；重复取证脚本还有一个未被本次运行触发的判定边界。因此整体不能报 PASS。

## 必审 1：动态读取 Claude 版本与清理身份

结论：这一项的版本门禁和清理身份主路径没有被放宽，PASS。

- `run_t108_native_e2e.py` 先执行已安装的 `/Users/luckye/.local/bin/claude --version`，用完整正则只接受 `<semver> (Claude Code)`，再把解析出的版本写入 manifest 的 `version`。这确实只是去掉写死的 `2.1.304`，没有把任意输出直接当版本。
- manifest 的版本不是门禁的最终依据。`workbench/src/panes.ts` 在 `startController` 中仍会对同一 executable 再执行一次 `--version`，并把实际输出与 `${manifest.version} (Claude Code)` 严格比较；不一致仍抛 `controller_version_mismatch`。本次 diff 没有改这段检查。
- `t108_cleanup.py` 的 `pid`、`pgid`、启动时间仍逐项严格相等才允许发信号；仍只向核对后的精确 PID 发 `SIGTERM`/`SIGKILL`，没有改成向共享进程组发信号。Claude 进程标题变化的既有例外仍要求 PID、PGID、启动时间先一致。
- 清理命令前缀由固定的 Claude 版本改为 manifest 中经 semver 校验的版本，同时继续要求原始 `claude ` 别名或 `/Users/luckye/.local/share/claude/versions/<version> ` 前缀，并继续核对 session id 和 fixture 的 debug-file 路径。这里只替换版本来源，没有删掉其他身份条件。
- 残余边界是：单看 `t108_cleanup.py`，它信任本地 manifest 中的版本，不自行再探测 CLI 版本；但该脚本继续绑定固定 fixture root、固定 session 和固定 PID，集成流程里的 manifest 又来自实际探测并会再经 `panes.ts` 严格核对，因此这不是本次引入的可利用绕过。
- Claude 版本门禁的独立测试本轮没有取得新的绿态：`test_t091_claude_version.mjs` 在到达版本用例前就被 `./executionSettings.ts` 模块白名单问题阻断，且 `main` 同样失败。该问题范围外，不能据本次候选报新回归，但也意味着本票没有重新取得门禁变异测试的完整证据。

## 必审 2：重复取证脚本与运行汇总

结论：负载隔离、输出边界和中止判定主逻辑正确；发现一个条件边界的 P2 风险。当前运行结果与 `RESULTS.md` 的 7 PASS、3 中止一致。

- 输出目录先 `resolve()`，拒绝 `/private/tmp` 本身、拒绝其外路径，并拒绝已存在目录；随后才创建，满足了新目录的要求。
- 10 个 CPU 忙循环均以 `start_new_session=True` 启动，因此每个 PID 自带独立 PGID。清理时只向各自 PGID 发 `SIGTERM`，超时再发 `SIGKILL`，并记录 PID 与回收 return code。`repeat-02-summary.json` 中 10 个 PID 的 PGID 分别等于自身 PID，回收结果均为 `-15`，与脚本相符。
- 单次 T-110 入口也用独立 session 启动；1800 秒超时会终止自己的进程组并记录 `timed_out=true`，不会伪装成目标失败。
- 无目标失败时，只要有任一次 `top_status != PASS`、`green_status != PASS` 或超时，汇总就置为 `INCOMPLETE`；只有全部完整 PASS 才是 `NOT_REPRODUCED`。现有汇总为 `status=INCOMPLETE`、`target_failure=null`，没有把中止运行算成“没复现”。
- P2：一旦 `green` 的错误文本命中目标断言，脚本直接置 `REPRODUCED` 并停止，不检查 `classify(green)` 是否返回了可归因结果。若目标文本出现，但缺少 `foreground` 时间线、缺少焦点终态，或终态是 `INCOMPLETE_UNEXPECTED_FINAL_STATE`，仍可能把不完整现场写成 `REPRODUCED`。这不影响本次 `target_failure=null` 的结果，但与本票“取得完整时间线后归因”的验收合同不一致。修正应要求在分类为产品路径或测试动作路径时才置 `REPRODUCED`，分类不完整时保持 `INCOMPLETE`。
- `repeat-02-summary.json` 与原始 `/private/tmp/t115-repeat-02` 一致：attempt-02/03/04/07/08/09/10 为完整 PASS；attempt-01 是 `red-disconnected-badge` 的 Electron 窗口清理超过 10 秒；attempt-05 是 `red-disconnected-badge` 的 `before_highlight['agents'][agent_id]` KeyError；attempt-06 是 `green` 的同位置 KeyError。其余 7 次的四个红态均按预期失败，`green` 与 `disabled` 均 PASS。
- `RESULTS.md` 的“0/10 复现”措辞不够精确：真正到达目标前台断言的是 7 次，另外 3 次在到达前中止。更准确的写法是“10 次外层运行中，目标断言实际执行 7 次，0 次目标失败；3 次未执行到目标检查而为 INCOMPLETE”。后文已列出 7 PASS、3 中止且总状态为 INCOMPLETE，因此不是把未检查的 3 次算成功能通过。

## 必审 3：结论与夹具不稳定描述

结论：主结论诚实，两类夹具不稳定描述准确；有两处轻微措辞不精确，不改变 INCOMPLETE 结论。

- `RESULTS.md` 明确写明目标是未复现、没有归因、没有改产品或断言，并明确报 INCOMPLETE；没有把“没复现”写成已解决。
- 7 次完整通过中记录到的 28 个 `foreground` 事件都出现 `app:did-become-active` 时 `badge=1`，随后 `app:browser-window-focus` 将 badge 清零。由于这是短暂状态，不能直接说“从未出现 focused=true 且 badge=1”；原文使用“没有观察到持续 focused=true 而 badge=1”，表述正确。
- “约 5 ms”过度概括：按原始时间线，`did-become-active` 到 `browser-window-focus` 的间隔约为 3.1～22.6 ms，中位数约 6.6 ms，分位数并非都在 5 ms 附近。应写成“通常数个毫秒，样本约 3～23 ms”。这不影响未复现结论。
- attempt-01 的窗口清理超时和 attempt-05/06 的高亮前快照 KeyError 均与原件相符。KeyError 的原因是 `before_prompt` 记录快照时 agent 尚未出现在侧栏，之后高亮通知已引用该 agent；它属于测试夹具的快照时机问题，不是本次目标角标失败。
- `project_map.py status --root .` 仍报告 8 个稀疏 worktree 的未检出链接问题，stale living docs 为 0。`RESULTS.md` 已如实披露，但 ticket 的“0 问题”验收仍未满足。

## 审查限制与未核实项

- 本回合按执行主控指令没有继续运行命令，也没有给 reviewer 提供可写入的一次性副本，因此没有自行执行 2～5 个新变异。现有可用的独立证据是执行主控提供的 `test_t110_cleanup.py` PASS、33 例，以及候选和 `main` 同因 `./executionSettings.ts` 失败的 `test_t091_claude_version.mjs`。
- 上述 T-091 测试原本包含删除 `controller_version_mismatch` 检查的变异，但运行在到达该逻辑前即被既有模块边界错误阻断；所以本票没有新的门禁变异结论。该缺口不能补写为通过。
- 未重新运行 T-110 真实入口；本审查依据已保留的 `repeat-02` 原始结果和汇总核对运行事实。目标失败现场本身不存在，无法补做焦点归因。

T-115 REVIEW INCOMPLETE
