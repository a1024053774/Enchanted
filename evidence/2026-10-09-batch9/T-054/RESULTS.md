# T-054 交付记录

**INCOMPLETE（整票）**：worker 的实现与本地验证已完成；任务书要求的“下一次真实派发”留给执行主控，尚未运行，不能据替身结果关闭整票。ticket 保持 open，待主控关闭。未改 fork、`scripts/inbox`、Claude Code 设置或用户 Herdr server，未向任何真实 pane 发送文本。

## 范围与候选

- 任务：T-054，`ready_rev: 1`；worker `s9-t054`，pane `wF:p1G`，原生会话 `01a12058-489c-74d0-9aed-9a9351bd94fc`。本任务书没有分配门禁 attempt/fence，不能把这些字段伪造为已核对身份。
- 规范：[ticket](../../../.project-map/tickets/T-054-dispatch-wrapper-and-session-copy.md)、[spec 第 3、6 节](../../../.project-map/specs/controller-split-user-input-2026-10-09.md)、[任务书](../brief-T-054.md)。
- 基线及模型/CLI/技能来源见 [run-metadata.json](run-metadata.json)；请求了 Fast tier，供应商实际 tier 未核实。候选完整提交在交付终端及 `candidate-revision.txt`；最终交付可能另含审查报告的证据提交。
- 目标：区分执行主控派发与用户输入，保留原生会话新增字节。非目标：提取输入、判断内容含义、策略引擎、真实派发、工作台修改。

## 实现与用法

```sh
# 执行主控下一次真实派发：agent 必须来自当前已核对的 live 身份。
scripts/dispatch --batch 2026-10-09-batch9 --agent LIVE_AGENT --role worker --body-file /absolute/path/brief.md
# 需要等待时保持 Herdr 参数语义；不重试。
scripts/dispatch --batch 2026-10-09-batch9 --agent LIVE_AGENT --role reviewer --body-file /absolute/path/review.md --wait --timeout 120000

# 来源路径与原生会话 id 先核对，再显式传入。
scripts/session-copy --batch 2026-10-09-batch9 --provider codex --session-id NATIVE_ID --source /verified/path/rollout.jsonl
scripts/session-copy --batch 2026-10-09-batch9 --provider claude --session-id NATIVE_ID --source /verified/path/claude.jsonl
```

`--root` 缺省为脚本所在仓库；`--body` 与 `--body-file` 二选一。文本不做换行或 Unicode 规范化，首条附角色卡。序号在本批全部目标间递增，每个 agent 本批只附一次角色卡；同名 agent 改角色会拒绝，改批次重新附卡。

`dispatch.jsonl` 是追加式的两阶段日志：锁内写 `prepared`（全文、目标、角色、序号、时间、argv，`exit_code=null`），锁外调用 Herdr 一次，再锁内写 `completed`（相同全文及真实退出码）。预备记录先持久化，避免发送后失去来源记录，并且允许不同进程并发等待；completion 的顺序可能不同于序号。只有预备记录时表示结果未知，不证明没送达，不能自动重发。失败也消耗序号与首条角色卡资格。

`session-copy` 使用跨批次的同一把锁，从所有 `evidence/*/sessions/manifest.jsonl` 推导已复制终点；区间为 `[start_byte, end_byte)`。副本为不解析的 `.bin` 字节段，0600；清单记录 provider、原生会话 id、来源路径/设备/inode、区间、大小与 `cutoff_at`，兼容现有 inbox 的副本提醒字段。没有新增字节时不追加重复区间。所有参与接续的批次证据必须仍在该 root 下。

两个入口共用持久追加与锁代码（`scripts/record_io.py`）。写入失败保留不完整记录或副本；下一次发现损坏或孤立文件时拒绝，交执行主控核对现场。没有重试、内容解析、语义正则或第二条投递路径。

## 验证

| 检查 | 实际结果与证据 |
| --- | --- |
| 入口缺失红态 | 六个初始用例全部因入口不存在失败；[red-01.log](red-01.log)。这是新合同的 expected red，不称为旧产品缺陷 |
| 完整契约绿态 | 8/8 PASS；[green-02.log](green-02.log)。较早的 6/6 记录仍保留为 [green-01.log](green-01.log) |
| 派发 | 16 路并发序号唯一、同 agent 仅一次角色卡；worker/reviewer/monitor；日志全文等于替身实收；多行、引号、标记符号、随机 sentinel 与文件 CRLF；失败输出/退出码原样返回、无重试；PATH 缺命令记 127；不能记录则不发送 |
| 会话副本 | 首次、追加、无新增、跨两个批次、并发同一会话；Codex 与 Claude；非法 JSON/二进制原样复制；截断/轮转/缺失/损坏清单拒绝并保留现场 |
| Git 边界 | 夹具 `git check-ignore`、`git status`、`git add`、`git ls-files` 证明副本被忽略、清单可跟踪；真实副本另见 [git-check-ignore-real.json](git-check-ignore-real.json)、[git-status-real.json](git-status-real.json) |
| 已知坏实现 | 三个指定 mutant 均 FAIL：[missing-marker](missing-marker-01.log)、[overwrite-log](overwrite-log-01.log)、[overlap-copy](overlap-copy-01.log)；[执行记录](counterexamples-01.json)。新增的两个用例也拒绝缺失父入口，[red-added-01.log](red-added-01.log) |
| 真实文件只读复制 | 本 worker 的 Codex 与执行主控 Claude：首次复制 PASS，Codex 再次增量复制 PASS；[定位/首次复制](native-location-and-copy.json)、[增量复制](native-incremental-copy.json)。没有读取内容做定位，没有解析或输出原生对话正文 |
| 语法 | 列出的 Python 文件编译 PASS；[syntax-check.json](syntax-check.json) |
| 差异检查 | 源码与文档 `git diff --cached --check` PASS；全量检查在 `missing-marker-01.log` 两行报告 trailing whitespace，这是 unittest 原始失败差异输出，按证据保留要求未清洗 |
| 项目地图 | status 的 problems/stale living docs 均为 0；[审查前记录](project-map-status-before-review.log)。未改地图、术语、治理规则 |
| fresh-context 独立审查 | **INCOMPLETE（整票）**；未确认行为违规或结构绕过，worker 本地范围可判 PASS，真实派发仍缺。见 [原样报告](independent-review.md)，针对 [冻结版本](candidate-revision.txt) |
| 下一次真实派发 | **未运行**，按 brief 由执行主控亲自完成，保存批次 `dispatch.jsonl` 后再验收 |

期望来自 ticket/spec 与独立夹具，测试不导入生产模块。Herdr 替身位于每个测试 root 的 `explicitly-fake-herdr-bin/herdr`，PATH 前置，只落参数文件，不连接 server。测试保留全部输入、文件与 stdout/stderr、退出码；[完整夹具归档](contract-artifacts-01.tar.gz) 包含合成测试目录、嵌入测试 Git repo 的完整现场和 mutant 源码。原目录也保留，没有顶层 gitlink。归档不含真实原生会话副本。

重放完整绿态与反例（目录必须是新的，不能覆盖先前证据）：

```sh
python3 -B acceptance/test_dispatch_session_e2e.py --artifacts /tmp/t054-contract-NEW-artifacts
# 反例脚本固定使用 counterexamples-01-artifacts；重放请先把脚本/候选复制到一个新的同层批次路径，
# 或按 counterexamples-01.json 里的完整 argv 选择解包后的 mutant 与新的 --artifacts 目录。
DISPATCH_SCRIPT=/path/to/missing-marker/dispatch SESSION_COPY_SCRIPT=/path/to/missing-marker/session-copy python3 -B acceptance/test_dispatch_session_e2e.py --artifacts /tmp/t054-mutant-NEW-artifacts Contract.test_dispatch_multiline_roles_and_append
```

初始红态命令为 `python3 -B acceptance/test_dispatch_session_e2e.py --artifacts evidence/2026-10-09-batch9/T-054/red-01-artifacts`，当时两个入口都不存在；输出先写入批次顶层 `T-054-red-01.log`，随后只移动本任务新建的日志至此目录。现在复现该状态，按反例记录将两个 script selector 指向不存在的路径，不能删当前实现。

## 原生会话定位事实

2026-10-09，本机 Herdr 0.9.3 的只读 `herdr agent get s9-t054` 返回 `result.agent.agent_session = {agent: codex, kind: id, source: herdr:codex, value: 原生会话 id}`。按该 id 在本机 `~/.codex/sessions/` 中查**文件名**，唯一匹配 `2026/10/09/rollout-2026-10-09T07-06-59-<id>.jsonl`；不是从内容搜索 id。这是本次已核实的默认目录，其他 worker 有独立 `CODEX_HOME` 时须从其启动配置核对实际目录，本脚本不猜测。

`herdr agent get wF:pM` 同样返回 Claude 原生会话 id；在 `~/.claude/projects/*/<id>.jsonl` 按文件名定位唯一来源，本次项目目录为 `-Users-luckye-Documents-Code-a2a`。构思主控的文件按其**当时已核对的目标**重复定位，不假设它与执行主控共享 id。本次没有定位或复制未指定的构思主控会话。清单与定位证据保留准确路径；真正的字节副本只留在本机 batch9 的 `sessions/`。

## 失败方式与限制

| 失败方式 | 处理与验证范围 |
| --- | --- |
| Herdr 不在 PATH | 保存预备与 exit 127 的完成记录，stderr 报缺命令；替身环境已验证 |
| agent 名不存在、`agent_blocked` 或其他 Herdr 非零 | 原样透传输出与退出码、追加结果、不重试。非零/blocked 替身已验证；不存在真实 agent 的 Herdr 结果未触发 |
| 日志目录不存在 | 自动创建后加锁；绿态首次执行覆盖 |
| 并发追加交错 | 本批派发锁保护预备/完成追加；全 evidence 会话锁保护跨批次复制；已验证 16 路派发与 6 路复制 |
| 磁盘写满、无写权限 | 发送前持久化失败就不调用 Herdr；发送后的结果写入失败明确告警，成功 Herdr 返回变为非成功。保留 partial/孤立现场，不能判断为可重试。目录不可写入场景已验证；ENOSPC 与发送后写满未注入 |
| 来源轮转、截断 | 路径/设备/inode 变化或长度小于终点时拒绝；已验证。不读取旧段来比较；同 inode 原地改写且长度未变无法由这些元数据检测，前提是原生文件追加写入 |
| 清单手工损坏 | 拒绝非法 JSON、缺字段、大小错误、重叠/空洞、来源身份不符或孤立副本；已验证字节范围破坏。大小相同的副本内容篡改无法凭清单检测；不计算 hash |
| 进程中断 | 预备记录与部分副本保留；不自动回滚、重发或修补。未注入 kill；清单/日志不完整会拒绝后续操作 |

本票只有 macOS 运行证据（`fcntl`）；未宣称 Windows 可用。未执行 fork 的 Bun 构建/测试，因为没有改 fork，且任务书禁止改写其构建产物。未更改用户 `~/.codex`、`~/.claude`；只读来源；没有 hook、权限批准或真实 provider 测试 turn。未做收益或可靠性主张。

独立审查后只补报告、定位/截止记录与项目地图检查，不改变冻结产品源码或测试。交付本地链接检查曾失败（四个相对路径多一层），已在本报告纠正；[失败记录](delivery-links-red-01.log) 与 [复查结果](delivery-checks-01.json) 保留。原生会话副本续拷只覆盖记录中的截止点，终端最终回复之后的尾部须由执行主控在回收前补拷。

权限建议为 [scripts/dispatch-permissions.md](../../../scripts/dispatch-permissions.md) 和 [JSON](../../../scripts/dispatch-permissions.proposed.json)，**待用户批准后应用**。规则依据 [Claude Code 官方权限文档](https://code.claude.com/docs/en/permissions)，不把建议文件等同于已生效权限。主控仍须沿既有唯一门禁验收、集成与回收，worker 自报和本报告不替代门禁。

## 执行主控下一步

1. 只读审阅候选与独立审查，处理审查的实际发现和限制。
2. 下一次真实派发以本包装发送该 agent 本批首条，核对标记、角色卡、全文与完成记录；不重发未知结果。将该次证据追加进本票。
3. 核对所需两个主控的原生会话副本，在回收/批次结束前续拷。真实副本不得进 Git。
4. 经既有门禁验收交付；补勾验收项并关闭 T-054。本 worker 未执行验收、集成、回收或 push。
