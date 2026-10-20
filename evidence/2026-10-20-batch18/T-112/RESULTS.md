# T-112 / a1 交付记录

状态：**INCOMPLETE**。实现及本地合同检查已完成；真实 daemon + 原生 CLI + 本地假 API、Electron 设置保存和 macOS 沙箱反例仍须执行主控运行外部脚本。本记录不替代独立验收，不宣称可集成。

起点：`e3102389eda8952ea92cae4b373e14eaff898314`，分支 `exec/t112`。不调用模型、不 push、不修改全局 CLI 配置、不走 submit。提交尾注由现有会话钩子生成。

## 实现

- 五个角色的模型、思考强度、Fast 写入 a2a 自己的 SQLite 追加式事件，不另建设置文件或平行库。逐字段优先级：派发覆盖 > 角色设置 > 出厂 `gpt-6.1-sol / high / Fast=false`。
- `dispatch`、`run --wait-seconds N` 新增 `--model`、`--effort`、`--fast true|false`，参数穿过真实门禁到 Panes。主控 prepare/start 也支持覆盖；manifest 的 execution 低于命令行覆盖。
- worker_executor_mismatch 保留 Codex CLI 身份检查，删除模型名单与 xhigh 检查。旧 Claude 合同的 effort 枚举也已移除。未知非空取值不改成默认值，交给 CLI。
- 原生 CLI 在会话建立前非零退出时记录 launch_failed。保留成功退出后的既有 zsh 行为；失败退出不再被 zsh 掩盖。原始错误保留于 launch 的 PTY 记录。
- reviewer 使用自己的设置；独立 home、候选副本、网络/tmp 限制、没有 worker Git hook 环境等原权限合同不变。模型/强度/tier 与完整 argv 一致记录，未把请求值当实际供应商 tier。
- Herdr 期 scripts/launch-worker 保留默认值，移除 effort 的 argparse choices；不引入从工作台数据库读取设置的第二启动路径。

Tracer bullet：设置表单 → IPC → SQLite → 派发 → argv 已接通；真实外部边界仍待复验。Deep modules：复用现有 OrchestrationStore、门禁和启动器。Ubiquitous language：沿用五个现有角色名，不新增角色别名。

## 按验收核对

| 要求 | 状态与证据 |
| --- | --- |
| 修前 high 红态 | 聚焦红态 PASS：focused-red-02.json，公开 Panes.createThread、已装 0.162.1 的真实版本探测，确实因 worker_executor_mismatch 拒绝。**完整真实派发红态 INCOMPLETE**，须运行外部脚本先测起点。focused-red-01 是依赖缺失的设置失败，不算业务红态。 |
| high/xhigh/其他文档取值启动，argv 一致 | 合同 PASS：execution-final-05.json。真实 CLI 启动及假 API 请求核对 **INCOMPLETE**；脚本覆盖 high、xhigh、low 和 Fast。 |
| 角色设置持久化、覆盖优先级、出厂值 | SQLite 重开、五角色默认、角色隔离、逐字段覆盖 PASS；真实 Electron 表单保存后下一次派发 **INCOMPLETE**，已编入脚本。 |
| 不支持值由 CLI 报错并记启动失败 | 不过滤 sentinel、保留 argv、启动失败事件合同 PASS；真实 CLI 解析错误 **INCOMPLETE**，已编入脚本。 |
| reviewer 权限不受强度影响 | 候选副本 argv、网络/tmp、home、无 worker hooks 的合同 PASS；原生 sandbox 拒绝写受保护文件并允许写候选副本 **INCOMPLETE**，已编入脚本。不是 --sandbox read-only，不能把原合同错误改写为这个参数。 |
| 全仓固定值检索 | search-final-02.json 保存命令与原文输出。有效 managed 启动不再按 model/effort 固定值拒绝；身份/尾注与实际交付匹配检查继续保留。旧 provider 合同还有 Pi/OMP/Grok 自己的枚举和 provider 默认值；当前原生工作台没有这些运行时，未扩展到其他供应商。 |
| README、角色卡 | PASS：README 写明设置/覆盖命令及 CLI 边界；五张角色卡写明默认见设置、可改；AGENTS.md 未改。 |
| project_map status 0 问题 | **INCOMPLETE**：稀疏 checkout 从开场起就有 8 个缺失文件链接问题，0 stale；已上报，不能擅改地图或补关 ticket。 |

## 已运行检查

以下命令的输出文件均保留；测试使用独立 sentinel 和需求中的期望值，不读取生产默认常量充当答案。

```sh
node workbench/tests/test_t112_execution.mjs evidence/2026-10-20-batch18/T-112/execution-final-05.json
python3 -B workbench/tests/test_t112_counterfactuals.py --summary evidence/2026-10-20-batch18/T-112/mutants-final-04.json
python3 -B workbench/tests/test_t112_herdr.py --summary evidence/2026-10-20-batch18/T-112/herdr-01.json
node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs evidence/2026-10-20-batch18/T-112/ipc-final-05.json
node workbench/tests/test_t108_questions.mjs evidence/2026-10-20-batch18/T-112/t108-final-03.json
node workbench/tests/test_t093_launch_profile.ts evidence/2026-10-20-batch18/T-112/claude-profile-01.json
node workbench/app/build.mjs --slot t112-final-02
```

以上最终运行均 PASS。5 个已知坏变异分别证明：拒绝旧 Claude effort 枚举、错误覆盖优先级、reviewer 误用 worker 设置、旧 worker 固定模型/强度门禁、启动失败被 shell 掩盖。IPC 原有拒绝检查未删减，新增设置 channel 的 iframe/未知窗口/非法 role/权限字段拒绝与精确透传；最终为 23 handlers / 24 bridge 字段。

首次变异设置阶段发生 ENOSPC，业务变异未执行；已保留 mutants-setup-failure-01.json，仅清理本票可重建依赖缓存并改为共用一份私有测试依赖。首次最终 T-108 复跑发生活跃夹具根目录 ENOENT，保留 t108-final-02.json 并上报；其后 t108-final-03.json PASS，不把前次失败删除或算成业务红态。构建 stdout/stderr 在 build-final-02.json，成功后的临时构建目录已清理。

CLI 帮助和版本原文：cli-help-01.json。PATH 当前是 Codex 0.163.0，门禁固定版本仍是 0.162.1；真实脚本显式使用已安装的 `/Users/luckye/.codex/packages/app-server-daemon/releases/0.162.1-aarch64-apple-darwin/bin/codex`，没有放松版本检查。配置文档来源/读取结果在 cli-config-docs-01.json、claude-config-web-02.txt；Claude 文档的 urllib 读取失败已保留，另经官方网页工具读取。产品使用自由文本，不从文档快照生成固定枚举。

## 主控需要运行

```sh
zsh evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-ARCHIVE-LOCAL-01.sh
zsh evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-COMMIT-01.sh
zsh evidence/2026-10-20-batch18/T-112/RUN-OUTSIDE-NATIVE-01.sh
```

默认使用主 checkout 已有的 Electron 43.4.1 内置盘运行时；可用 T112_ELECTRON_DIST 指定同版本目录。脚本先测冻结起点的 high 拒绝，再测候选。只使用隔离 repo/state/home、本地固定 Responses API、私有源码和依赖副本；只在该副本修改 spawn-helper 执行位，不建链接，不调用模型，不截屏。后台 detached；结束时核对并清理本次拥有的进程。原始夹具归档到外置盘，核对文件数与字节数后清理原目录；盘未挂载就报归档失败，不回退内置盘。失败后保留 summary，重跑须另取 summary 文件名，不能覆盖原失败。

## 范围外问题及交接

- inbox `20261020T124548Z-worker:t112-a1-issue-001`：地图缺失文件；AGENTS.md:67、69 仍要求固定模型/强度、不用 Fast，须主控转交维护。本票新要求覆盖旧固定值，但 worker 不改治理文件。
- 同条 issue：当前两个主控是真实 Claude 入口，monitor 尚无真实 attached runtime。五角色设置已保存，**没有新增 Codex 主控或 monitor 启动器**。出厂模型名按任务要求统一保存；启动现有 Claude 主控前须选择其支持的模型或传覆盖。这个默认值与现有 Claude 入口的可用性冲突须主控确认，不能宣称开箱即用。
- inbox `20261020T130602Z-worker:t112-a1-issue-001`：T-108 活跃夹具缺失，原因未知。后续复跑 PASS，仍保留失败现场记录。
- 与 T-110 的接线范围：renderer.tsx 第 10–11 行 import、第 48 行 bridge 类型、第 570 行组件；main.ts 第 139 行起新增独立 settings IPC；preload.ts 新增一个 bridge 方法。sidebar.ts、原通知区块和原样式文件未改。设置组件/CSS 分别在 ExecutionSettings.tsx、execution-settings.css。

本票保持 INCOMPLETE，待真实外部检查、默认值冲突处置与完整 checkout 的地图检查完成。

本地提交：INCOMPLETE。git add --sparse 被沙箱拒绝创建本 worktree 的 index.lock（git-add-sandbox-01.json）。按派发要求未申请升级，已生成 RUN-OUTSIDE-COMMIT-01.sh；主控先运行该脚本即可在 exec/t112 上提交。脚本恢复本 worker 的原启动/原生会话环境，沿用钩子自动加尾注，没有手写 A2A-*，不 push。

独立审查发现并已修外部 runner：门禁拒绝用 JSON + exit 1，旧 run() 误当设置失败，红态场景无法到达自己的断言。现仅对 CLI call 接受退出 0/1，仍由每个场景核对 ok/error；exit 2 用法错误仍拒绝。实际 runner 函数与真实退出 1/2 子进程合同见 runner-refusal-contract-01.json。尚无修后的完整原生运行证据，不把此修复写成外部验收通过。

独立审查：independent-review-01.md 对冻结副本的结论原样为 FAIL。两个发现已在后继候选修复：P1 的 exit-1 处理见上述 runner 合同；P2 不再按 shell 源码片段判定，而是实际执行记录下来的 zsh + 私有失败 CLI，确认退出码 23 后记录启动失败事件。含惰性字符串、实际掩盖失败的变异被新断言以 0 != 23 拒绝，见 execution-final-05.json、mutants-final-04.json。没有把冻结候选的旧审查改成修后 PASS；最终独立审查仍交执行主控。

外部步骤按上方顺序：先归档本地临时夹具，再提交候选，最后运行真实验证，使 launch 的 code_revision 绑定完整提交。native runner 会拒绝未提交的源码/测试；原生验证结果落地后还需由主控纳入后续证据提交。归档脚本如实列出已不存在的旧夹具，不补造归档。
