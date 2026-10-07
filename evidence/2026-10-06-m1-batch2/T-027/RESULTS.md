# T-027：Muster 引擎独立命名空间（2026-10-06）

状态：**INCOMPLETE：代码与自带测试已准备好，最终候选的真实 Codex 复验和独立审查尚未完成。** 本记录只对应 T-027，不代表 M1 或运行时切换通过。

## 当前验收

| 条目 | 当前结论 | 命令、观察和证据 |
| --- | --- | --- |
| 源码构建、外置盘、缺盘拒绝 | PASS | `MUSTER_BUILD_SLOT=worker-t027 ./scripts/build build --locked --manifest-path muster/Cargo.toml`；[build-muster-frozen.log](build-muster-frozen.log)、[build-layout.json](build-layout.json)。缺盘调用退出 2，见 [missing-volume-result.json](missing-volume-result.json)。 |
| 独立 server、项目/任务/pane、shell、断开后持续 | 最终候选待复验 | run-03 已通过真实 CLI 与 generation 1 endpoint 连接、shell nonce 输出、客户端断开后的延迟输出；[run-03/result.json](run-03/result.json)。其后修正了 wire 值，不复用旧候选的 PASS。 |
| Codex working/idle、Muster hook 原生会话 ID | 最终候选待复验 | run-03 观察到 working→settled，来源为 `muster:codex`。下一轮会明确观察 idle，并与 Codex 自己的会话 metadata 对照 ID。 |
| Herdr 与 Muster 共存、socket/config/hook 隔离 | 最终候选待复验 | run-03 核对 Herdr 0.9.1 server 的 PID/启动时间，以及主控的 shell PID/前台进程组未变；用户 hook 原始字节未变。原始记录保留在该运行目录。这个检查不等于核对默认会话全部业务状态。 |
| 不访问 herdr.dev | 静态 PASS；最终运行待复验 | [source-final.txt](source-final.txt) 检索源码、构建脚本与 package metadata，无 `HERDR_*`、在线产品站点地址或 curl transport。运行时 wrapper 记录和 server TCP 观察见 run-03；最终候选需重新观察。 |
| 来源、LICENSE、相关自带测试 | PASS | [import.txt](import.txt)、引擎 [NOTICE](../../../muster/engine/NOTICE)、原始 LICENSE 字节保留；[unit-summary-authoritative.json](unit-summary-authoritative.json) 核对完整 3470 项列表：3459 通过、11 为上游已有 ignored 项，50 个进程均退出 0。冻结 endpoint oracle 原始字节保留，见 [frozen-fixture-preserved.json](frozen-fixture-preserved.json)。 |

## 范围、身份和实施方向

主控：Claude Code（`wF:pM`）；worker：Codex（`wF:pS`）。任务书实际为 `brief-T-027.md`；用户输入中的 `brief-T-0027.md` 不存在，启动记录和 ticket 均指向 T-027。

固定上游为 `https://github.com/herdrdev/herdr` 的 `c4653a4f10502601ac110b12b2c45a5f7134082b`。通过 `git archive` 导入已提交源码，保持目录结构；共享工作区有其他 session 的文件，不能使用要求干净工作区的 subtree。上游克隆未修改。模型、CLI、启动参数、构建槽与 skill 快照见 [metadata.json](metadata.json)、[skills/](skills/)。请求为 `gpt-6.1-sol`、xhigh、Fast；供应商实际 tier 未验证。

Reality gate 为 PASS：固定源码、外置盘入口与隔离命名会话均已 observed；源码 observed 支持独立 CODEX_HOME。真实状态识别和 hook 行为由真实 CLI 探针验证，不用静态推断代替。目标为本 ticket 六项验收；不做 GUI、coop 接线或运行时切换。

**Tracer bullet** 是真实 CLI→server→pane→shell 读写；**Deep modules** 沿用现有控制协议，没有另造一套 API；**Ubiquitous language** 中项目/任务暂对应保留的 workspace/tab。generation 1 已发布的 right-click wire 值 `herdr` 保留为单一协议标识；Rust variant、CLI 参数和显示使用 Muster，不增加 alias 或平行 API。以后只在新协商的协议 generation 中更换 wire 值。

源码移除了在线版本/公告/发布说明获取、检测清单获取和远程发布包下载；即使配置将两种 check 设置为 true，也不能开启它们。已有本地数据解析和显示仍保留；没有把禁用网络当成禁用模型供应商连接。

## 红态、失败与反事实

- 改名前：同一名称 oracle 拒绝已安装上游 CLI 和从固定源码构建的基线，分别见 [red-installed-upstream](red-installed-upstream/)、[red-source-baseline](red-source-baseline/)。这是新合同的预期红态，不宣称上游有缺陷。[source-red.txt](source-red.txt) 保存原在线 transport 检索。
- 工具/编译错误：Python 3.9 不支持 tar extraction 的 filter 参数；首次提取未写出文件。第一次候选编译把 Windows installer 文本错误限定在 Windows，macOS 的远程代码也需要它。原日志 `build-before.log`、`build-muster-01.log` 均保留；这些不计入合同红态。
- run-01：启动 idle 时还没有原生会话；隔离 Codex 数据库 threads 数为 0，说明需要先发起首轮任务，再检查会话上报。未降级 session ID 条件。
- run-02：实际出现 17 项 hook 的 trust UI，没有批准，也没有运行已有用户 hook。界面见 [hook-approval-dialog-from-run.txt](hook-approval-dialog-from-run.txt)，原运行与失败保留。
- run-03：获得主控明确批准后，只加载/信任四个 Muster hook；32 项运行检查通过。旧的私有 home 与本轮 home 都删除，见 [prior-private-homes-cleanup.json](prior-private-homes-cleanup.json) 和该运行 events。复制的 auth/config 未进入证据或 Git。此结果是其当时候选的证据。
- 自带测试：首轮整体 harness 被 SIGPIPE 中断；长外置盘 TMPDIR 加上 socket 文件名超过 macOS SUN_LEN。分组进程、短运行时目录和 Cargo package cwd 的修正见 [test-isolation.md](test-isolation.md)。旧错误、runner 错误与诊断全部保留。
- Letta 捕获夹具：真实异常为新写的假 CLI 首次执行超出已有 hook 的一秒预算，继而 poison 共享测试 mutex。仅提前验证假 CLI 并删除预备输出，再要求 hook 产生新捕获；产品 timeout 与 retry 未改。
- wire 机械改名：原冻结 oracle 拒绝 `pane.input.set` 与 `pane.split` 的 shape 改变。恢复单一 wire 值后原 oracle 通过，没有重写它的答案。
- 更新提示反事实：恢复旧在线更新指令的 mutant 使六个相关断言失败；[offline-mutant/result.json](offline-mutant/result.json) 同时确认源码完整恢复。正确候选的这些测试通过。checksum/CJK 截断的固定示例恢复原字节，没有重算答案。
- 汇总器首版漏计输出中带 ANSI 和空格的测试结果；原汇总及错误保留。`summarize_tests.py` 只解析已有原始输出，现已逐个核对完整列表；不靠计数来替代测试断言。

## 复现

```sh
MUSTER_BUILD_SLOT=worker-t027 ./scripts/build build --locked --manifest-path muster/Cargo.toml
MUSTER_BUILD_SLOT=worker-t027 ./scripts/build test --locked --manifest-path muster/Cargo.toml --bin muster --no-run
python3 evidence/2026-10-06-m1-batch2/T-027/run_unit_tests.py --binary TEST_BINARY_FROM_BUILD_LOG --output NEW_DIRECTORY
python3 evidence/2026-10-06-m1-batch2/T-027/probe.py --binary /Volumes/WD-Elements/dev-cache/a2a/target/worker-t027/debug/muster --codex --output NEW_DIRECTORY
```

真实运行每次新建目录与含 t027 名称的会话；剥离继承的 HERDR/MUSTER 变量与 CODEX_THREAD_ID。Rust/Cargo/Zig 构建及编译临时目录仍在外置盘；`/tmp` 只用于短路径的运行时夹具。Codex 的 trust 必须得到对应新 home 的明确许可，不能自动复用已消耗的“下一次”批准。只停止自己创建的 server，保留运行时状态和失败记录；私有 Codex home 按许可删除。

## 主控收尾与局限

任务书禁止 worker 改根 README、MAP、AGENTS、CONTEXT。Muster 源码加入后，根 README 的“未实现”描述需要主控更新；当前地图结构问题为 0，README 为 stale。未验证 Windows/Linux、GUI/IME/复制、三套 coop 验收或真正运行时切换。没有吞吐、可靠性或成本收益结论。

新 Codex hook trust UI 在上游检测规则下可能仍显示 idle；本探针根据实际文本保护权限边界，不将该场景当成 blocked 检测通过。该兼容性发现交给主控安排后续范围。
