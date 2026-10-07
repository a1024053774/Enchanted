# T-027：Muster 引擎独立命名空间（2026-10-06）

状态：**PASS：T-027 六项当前候选验收通过，独立只读审查通过。** 冻结候选为 `3316be04af56ed7b141e659ea26dd7ddc9e90887`，最终复验于 2026-10-07 完成。本记录只对应 T-027，不代表 M1 或运行时切换通过。

## 当前验收

| 条目 | 当前结论 | 命令、观察和证据 |
| --- | --- | --- |
| 源码构建、外置盘、缺盘拒绝 | PASS | `MUSTER_BUILD_SLOT=worker-t027 ./scripts/build build --locked --manifest-path muster/Cargo.toml`；新候选命令/退出码见 [frozen-build-checks-3316.json](frozen-build-checks-3316.json)、[build-frozen-3316.log](build-frozen-3316.log)。[package-cache-current.json](package-cache-current.json) 核对实际外置盘 symlink、设备与 Git cache 零条目；缺盘调用退出 2，见 [provenance-and-missing-mount-3316.json](provenance-and-missing-mount-3316.json)。 |
| 独立 server、项目/任务/pane、shell、断开后持续 | PASS | 新候选的 [run-04/result.json](run-04/result.json) 共 22 项通过；真实 CLI 创建对象、读写 shell nonce，generation 1 endpoint 实际连接并接收帧，客户端断开后延迟输出仍可读。完整 argv/输出见 [events](run-04/events.ndjson)。 |
| Codex working/idle、Muster hook 原生会话 ID | PASS | [run-05/result.json](run-05/result.json) 共 35 项通过；真实 Codex 0.160.1 观察到 working→显式 idle。来源 `muster:codex`、ID `01a11489-a605-7f70-a3e0-34ff691d82a7` 与 [原生 metadata](run-05/native-session-metadata.json) 一致；[原生最终回复](run-05/native-final-replies.json) 与 CLI 可见输出均匹配本次 nonce。 |
| Herdr 与 Muster 共存、socket/config/hook 隔离 | PASS | run-05 核对 Herdr 0.9.1 server 的 PID/启动时间，以及主控的 shell PID/前台进程组未变；用户 hook 原始字节未变。见 [before](run-05/herdr-before.json)、[after](run-05/herdr-after.json)、[四个隔离 hook](run-05/isolated-hooks.json)。这不等于核对默认会话全部业务状态。 |
| 不访问 herdr.dev | PASS | [source-current.json](source-current.json) 保存网络获取函数、调用者及源代码检索；`3316be0` 与检索版本 `cec8357` 的生产代码差异为空，见 [冻结记录](candidate-freeze-3316.json)。运行时开启两种 check 也不能触发网络；update/channel/manifest 命令明确拒绝，[网络调用记录](run-05/network-attempts.txt) 为空，server TCP 观察为空，见 [events](run-05/events.ndjson)。上游文档中的来源链接保留，不能把来源字符串等同于执行网络访问。 |
| 来源、LICENSE、相关自带测试 | PASS | [import.txt](import.txt)、引擎 [NOTICE](../../../muster/engine/NOTICE)、原始 LICENSE 字节保留；新候选 [unit-summary-3316.json](unit-summary-3316.json) 核对完整 3470 项列表：3459 通过、11 为上游已有 ignored 项，50 个进程均退出 0。完整原始结果见 [unit-modules-03](unit-modules-03/)。冻结 endpoint oracle 原始字节保留，见 [frozen-fixture-preserved.json](frozen-fixture-preserved.json)。 |

## 范围、身份和实施方向

主控：Claude Code（`wF:pM`）；worker：Codex（`wF:pS`）。任务书实际为 `brief-T-027.md`；用户输入中的 `brief-T-0027.md` 不存在，启动记录和 ticket 均指向 T-027。

固定上游为 `https://github.com/herdrdev/herdr` 的 `c4653a4f10502601ac110b12b2c45a5f7134082b`。通过 `git archive` 导入已提交源码，保持目录结构；共享工作区有其他 session 的文件，不能使用要求干净工作区的 subtree。上游克隆未修改。模型、CLI、启动参数、构建槽与 skill 快照见 [metadata.json](metadata.json)、[skills/](skills/)。请求为 `gpt-6.1-sol`、xhigh、Fast；供应商实际 tier 未验证。

Reality gate 为 PASS：固定源码、外置盘入口与隔离命名会话均已 observed；源码 observed 支持独立 CODEX_HOME。真实状态识别和 hook 行为由真实 CLI 探针验证，不用静态推断代替。目标为本 ticket 六项验收；不做 GUI、coop 接线或运行时切换。

**Tracer bullet** 是真实 CLI→server→pane→shell 读写；**Deep modules** 沿用现有控制协议，没有另造一套 API；**Ubiquitous language** 中项目/任务暂对应保留的 workspace/tab。generation 1 已发布的 right-click wire 值 `herdr` 保留为单一协议标识；Rust variant、CLI 参数和显示使用 Muster，不增加 alias 或平行 API。以后只在新协商的协议 generation 中更换 wire 值。

源码移除了在线版本/公告/发布说明获取、检测清单获取和远程发布包下载；即使配置将两种 check 设置为 true，也不能开启它们。已有本地数据解析和显示仍保留；没有把禁用网络当成禁用模型供应商连接。

主控指出 `c5a9cb0` 的机械改名误改了 386 个文件中的上游引用。新候选将仓库、issue、文档和社交来源链接恢复为 Herdr 上游，将 package 的 `repository` 设置为 `https://github.com/a1024053774/a2a`；[修复清单](upstream-reference-fix.json) 和 [冻结候选零匹配](upstream-reference-zero-3316.json) 留档。首次清理后的残留检查保留为 [压缩失败记录](upstream-reference-zero-failed.json.gz)，没有改写红态。JSON 中检索参数使用等价 Unicode 转义，以免证据本身重新包含被禁的错误名称。

严格先后顺序见 [final-preconditions.json](final-preconditions.json)：冻结候选→重建→分组单元→无 Codex 的 shell/endpoint→唯一一次新 home 的四 hook 复验。最终许可原文的字节副本见 [controller-final-grant.md.gz](controller-final-grant.md.gz)，主控原文件未改；仅这四个 hook 被信任。整个 `CODEX_HOME=/tmp/t027-2t_niqym/codex` 已删除，实际删除命令与不存在检查在 run-05 events；复制的 auth/config 未进证据或 Git。没有使用该许可建立第二个 home。

## 红态、失败与反事实

首个源码提交 `1a64cdb` 为拒绝候选：强制暂存错误纳入源码旁的 Zig 0.16 解包缓存；该缓存实际仍在内置盘。原提交保留，缓存完整移到外置盘，新候选移除 Git cache 记录，并由 build.rs 创建 ignored 外置盘 symlink。此事实以 [package-cache-fix.md](package-cache-fix.md)、[cache-contamination.json](cache-contamination.json)、[package-cache-layout.json](package-cache-layout.json) 为准；早先仅检查 cache 环境变量的通过结论无效。

- 改名前：同一名称 oracle 拒绝已安装上游 CLI 和从固定源码构建的基线，分别见 [red-installed-upstream](red-installed-upstream/)、[red-source-baseline](red-source-baseline/)。这是新合同的预期红态，不宣称上游有缺陷。[source-red.txt](source-red.txt) 保存原在线 transport 检索。
- 工具/编译错误：Python 3.9 不支持 tar extraction 的 filter 参数；首次提取未写出文件。第一次候选编译把 Windows installer 文本错误限定在 Windows，macOS 的远程代码也需要它。原日志 `build-before.log`、`build-muster-01.log` 均保留；这些不计入合同红态。
- run-01：启动 idle 时还没有原生会话；隔离 Codex 数据库 threads 数为 0，说明需要先发起首轮任务，再检查会话上报。未降级 session ID 条件。
- run-02：实际出现 17 项 hook 的 trust UI，没有批准，也没有运行已有用户 hook。界面见 [hook-approval-dialog-from-run.txt](hook-approval-dialog-from-run.txt)，原运行与失败保留。
- run-03：获得主控明确批准后，只加载/信任四个 Muster hook；32 项运行检查通过。旧的私有 home 与本轮 home 都删除，见 [prior-private-homes-cleanup.json](prior-private-homes-cleanup.json) 和该运行 events。复制的 auth/config 未进入证据或 Git。此结果是其当时候选的证据。
- 最终探针：使用许可前核对 Codex 0.160.1 原生日志，发现消息阶段字段是 `phase=final_answer`，此前未运行的探针误用了 `channel`。依据 [实际 envelope 结构](native-envelope-schema-completed.json) 修正并重新冻结，不增加兼容分支；之后才执行 run-04、run-05。旧探针版本保留在提交历史中。
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
python3 evidence/2026-10-06-m1-batch2/T-027/probe.py --binary /Volumes/WD-Elements/dev-cache/a2a/target/worker-t027/debug/muster --output NEW_DIRECTORY
python3 evidence/2026-10-06-m1-batch2/T-027/probe.py --binary /Volumes/WD-Elements/dev-cache/a2a/target/worker-t027/debug/muster --codex --output NEW_DIRECTORY
```

真实运行每次新建目录与含 t027 名称的会话；剥离继承的 HERDR/MUSTER 变量与 CODEX_THREAD_ID。Rust/Cargo/Zig 构建及编译临时目录仍在外置盘；`/tmp` 只用于短路径的运行时夹具。Codex 的 trust 必须得到对应新 home 的明确许可，不能自动复用已消耗的“下一次”批准。只停止自己创建的 server，保留运行时状态和失败记录；私有 Codex home 按许可删除。

上面的 `--codex` 命令只说明重现入口；本次唯一许可已经消耗，另一次运行需另行获得明确许可。最终检查、命令、原生 ID 与原始路径索引见 [final-runtime-evidence.json](final-runtime-evidence.json)。

## 独立审查

首次独立只读审查为 `INCOMPLETE`：主实现者在审查期间更新了已跟踪报告，审查器依冻结规则停止，未对六项 Acceptance 作出裁定。原文见 [review-01-incomplete.txt](review-01-incomplete.txt)、模型与处理记录见 [review-01-metadata.json](review-01-metadata.json)。报告和原始证据先提交冻结，再以 fresh context 审查；生产代码与已通过真实运行的 `3316be0` 相同，不重建 Codex home。审查器使用 `acceptance-auditor` 角色（固定 `gpt-5.6-luna`、max），不读取实现者对话或本报告，不修改任何源码或证据。

重新冻结报告及证据到 `fd3beb70bcc1add0eb0428e8c062e3d68e694e10` 后，fresh-context 审查返回 **PASS**，无发现；原文见 [review-02-pass.txt](review-02-pass.txt)，模型与范围记录见 [review-02-metadata.json](review-02-metadata.json)。审查器确认生产代码及探针与真实运行的 `3316be0` 差异为空，审查前后已跟踪工作树干净；结论仅限 T-027。其反事实段落称“四个相关测试”，准确数量是四次执行命令、六个失败断言；原始审查文字保持不改，以 mutant 原始日志为准。原始日志的尾部空行/空格使 whitespace check 返回 2，见 [记录](evidence-whitespace-check.json)，按原样保留，未当作代码检查通过。

## 主控收尾与局限

任务书禁止 worker 改根 README、MAP、AGENTS、CONTEXT。Muster 源码加入后，根 README 的“未实现”描述需要主控更新；当前地图结构问题为 0，README 为 stale。未验证 Windows/Linux、GUI/IME/复制、三套 coop 验收或真正运行时切换。没有吞吐、可靠性或成本收益结论。

新 Codex hook trust UI 在上游检测规则下可能仍显示 idle；本探针根据实际文本保护权限边界，不将该场景当成 blocked 检测通过。该兼容性发现交给主控安排后续范围。
