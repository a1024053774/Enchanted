# T-221 日期扫描修复报告

状态：INCOMPLETE（实现与日期专项验证 PASS；T-136 回归存在基线同败，独立 agy 审查待主控）。基线：`d72a7746be0b737849bcd97caae05b1ac8689ece`；分支：`t221-dst-day-scan`。

## 失败方式清单（产品与测试修改之前记录）

1. 秋季回拨窗口晚间启动，固定 24 小时终点不含本地次日；覆盖 T-219 的 10 月 31 日晚跨入 11 月 1 日，以及 11 月 1 日晚。
2. 春季跳过日（2026-03-08）少算或多算一天，或跨日时墙钟偏移使边界错位。
3. 月末或年末的进位错误，漏掉下一月／年首日，或中间日期重复、缺失、顺序错误。
4. 起始日期错成前一天／后一天；时区转换错误（本地晚间的 UTC 已是次日）。
5. trajectoryArchive 两处原本从启动前一天扫描，统一后丢失这一天；另核对 DST 附近早间的“前一天”仍为本地日历前一天。
6. 四处循环有一处未接入共用计算；helper 测试通过，实际 native_link、Panes.scan、角色归档或复盘归档仍漏扫。
7. 扫描多到本地后天，或错误修改传入时刻；明确核对完整日期数组及输入稳定性。

测试按上述清单编写；日期预期按日历手工列出，不由产品函数生成。先只抽取原有计算（不修行为），在产品函数和消费者上记录红态，再修复。

## 目标、边界与未知

目标：四处统一为从本地起始日期到本地明天（含两端）的日期范围，归档保留前一天。非目标：记录目录命名、native_link 置灰规则、其他产品行为。采用 Ubiquitous language 中的原生会话与轨迹归档术语。该变更只涉及日期计算与现有调用者，不需要跨层 Tracer bullet；共用函数收拢实际重复计算，避免浅包装增加 Deep modules 的设计成本。

所有运行固定 TMPDIR=/private/tmp；仅写 T-221 worktree、T-221-evidence 和测试自身 /private/tmp 夹具。不修改 .project-map、不提交、不 push、不接用户 Herdr/hc、不调真实供应商模型。T-219-evidence 只读。独立 agy 审查是否由主控另行安排，留待交接。

事实差异：本机 date 实测 2026-10-31 22:48 EDT，尚未经过 2026-11-01 回拨，与任务文字“今天已经过了回拨”不一致；后续记录实际运行时刻，不改系统日期，不把注入日期冒充真实时间。

## 候选与改动

本次是用户直接指定的 T-221 worktree 实现，无受管 attempt/session/fence，不伪造身份。规格为 T-221 ready_rev 1 与本轮用户要求；代码版本由完整基线加 [candidate.patch](candidate.patch) 唯一描述，文件清单见 [candidate.json](candidate.json)。没有 commit 或 push；HEAD 仍为基线。真实回归中的 task、attempt、session/fence、CLI 版本和完整 argv 另见 [final-fixture-inspection.log](final-fixture-inspection.log) 与保留的夹具数据库。

- 新增 `workbench/src/codexScanDays.ts`：将启动日和当前日转换成本地午夜边界，以本地日历递增，终点是本地明天，含两端；每次迭代给出独立 Date。
- `nativeLink.ts/codexRootThreads`、`panes.ts/scan` 和 `trajectoryArchive.ts` 的两处查找均调用它。前两处从启动当天开始；归档传 `-1`，保留本地启动前一天。产品中删除四处旧循环，没有兼容分支或平行计算。
- 归档原来的“减固定 24 小时”在春季午夜附近会落到前两天、回拨日晚间会仍落在当天；本次按票面“本地前一天”约定处理，测试覆盖并保留红态，未保留该旧偏差。
- 新增 `workbench/tests/test_t221_codex_scan_days.ts`；仅注入时钟，调用真实产品计算和消费者。真实文件每次只放在一个候选日期目录，使起始、终止、中间每一天以及前后排除日期均可观察。`nativeLink` 的归档来源使用固定已绑定文件夹具；四处日期查找、目录遍历和数据库读取均为产品代码。
- 同步 `workbench/README.md` 的日期范围说明。`.project-map/`、原验收文件及 T-219 材料均未修改。

## 红态、绿态与变异

**日期专项：PASS。** 红态先于修复：只抽取原公式后，于 22:51:04 EDT 执行同一测试，196 项中 38 项失败。抽取 diff 见 [extraction.patch](extraction.patch)，修前函数保存为 [extracted-codexScanDays.ts](extracted-codexScanDays.ts)。测试没有另写扫描算法；时钟为外部输入，日期预期为手工写死的数组。

T-219 精确时刻用例：`since=2026-10-31T22:34:14-04:00`、`now=2026-10-31T22:35:14-04:00`，TZ 为 America/New_York。原函数仅给出 `2026/10/31`，预期为 `2026/10/31, 2026/11/01`。四个真实消费者也分别漏掉 11 月 1 日的夹具文件；原生链接仍可用、Panes 不绑定、两条归档路径找不到。详见 [red-extracted.json](red-extracted.json) 与 [red-extracted.log](red-extracted.log)，退出 1。

时间口径须准确：原失败发生在 **10 月 31 日晚跨入 11 月 1 日回拨窗口**。11 月 1 日晚到 11 月 2 日晚已是 24 小时，不能声称该窗口本身必然复现同一个漏次日缺陷。测试另覆盖了 11 月 1 日晚启动，及其归档必须包含 10 月 31 日的条件。

修复后同一命令与测试文件在 22:51:17 EDT 全部转绿，见 [green-days.json](green-days.json) 与 [green-days.log](green-days.log)，退出 0。八组日历输入各检查完整日期数组，且逐日经过四个消费者。主要手工 oracle 如下（日期均为本地日期）：

| 边界 | 启动当天至明天（含两端，完整数组） | 归档额外包含的起始前一天 |
| --- | --- | --- |
| 春季 2026-03-08 | 03/06、03/07、03/08、03/09 | 03/05 |
| 秋季回拨窗口 | 10/30、10/31、11/01 | 10/29 |
| T-219 原时刻 | 10/31、11/01 | 10/30 |
| 回拨当天晚间 | 11/01、11/02 | 10/31 |
| 月末 | 04/29、04/30、05/01 | 04/28 |
| 年末 | 2026/12/30、2026/12/31、2027/01/01 | 2026/12/29 |
| 春季后的午夜 | 03/09、03/10 | 03/08 |
| 回拨日 23:30 启动 | 11/01、11/02 | 10/31 |

六种反事实都只在 `/private/tmp/t221-mutant-*` 源码副本上运行，未修改候选。子测试均按预期以业务断言失败（退出 1）；包装脚本确认失败位置符合目标后退出 0，不能把变异结果 JSON 的 INCOMPLETE 看成产品通过。

| 变异 | 子测试失败项数 | 证据 |
| --- | ---: | --- |
| 整体恢复修前固定 24 小时算法 | 38 | [mutant-original-helper.json](mutant-original-helper.json) |
| 只漏改 nativeLink 循环 | 5，仅原生链接检查 | [mutant-miss-native.json](mutant-miss-native.json) |
| 只漏改 Panes 循环 | 5，仅窗格检查 | [mutant-miss-panes.json](mutant-miss-panes.json) |
| 只漏改按 cwd 归档循环 | 8，仅复盘归档检查 | [mutant-miss-archive-cwd.json](mutant-miss-archive-cwd.json) |
| 只漏改按 session id 归档循环 | 8，仅终端主控归档检查 | [mutant-miss-archive-id.json](mutant-miss-archive-id.json) |
| 两处归档删掉前一天 | 16，仅归档前一天检查 | [mutant-drop-previous.json](mutant-drop-previous.json) |

## 现有测试回归

用 `rg -n 'trajectoryArchive|nativeLink' workbench/tests acceptance` 查找，再以全仓测试文件搜索交叉核对。现有测试没有直接静态 import 这两个模块；命中的是经真实 daemon 间接执行并引用源码作变异的 T-135、T-136、T-195，均已逐个运行。发现记录见 [regression-discovery.log](regression-discovery.log)。没有把“无直接 import”当成无需回归。

| 测试 | 状态 | 结果 |
| --- | --- | --- |
| T-195 原生链接 | PASS | 16 项全过，含 `managed_codex_unsearchable_day_grey`；[regression-t195.json](regression-t195.json) |
| T-135 轨迹归档 | PASS | 6 项全过，含增量、半行、真实 Electron 设置页占用；[regression-t135.json](regression-t135.json) |
| T-136 复盘 | INCOMPLETE | 前 9 项通过，在 `schedule_fires_once_at_its_time` 失败；之后的开关等检查未执行；[regression-t136.json](regression-t136.json) |
| T-136 原基线对照 | INCOMPLETE | `--revision d72a7746be0b737849bcd97caae05b1ac8689ece` 仍前 9 项通过、同一条定时检查失败；[regression-t136-baseline.json](regression-t136-baseline.json) |

T-195 使用复制到本目录的 [safe-t195-native.py](safe-t195-native.py)，与 T-219 原件仅 ROOT 路径不同。Claude 与 Codex 均为真实 CLI/TUI，模型改接本地脚本化 Messages/Responses 服务。Codex provider 写入隔离 `/private/tmp/t195-codex-home-*`；配置记录见 [regression-t195.transport.json](regression-t195.transport.json)，本地请求见 [regression-t195.api.jsonl](regression-t195.api.jsonl)。实际 CLI 为 Claude Code 2.1.316、Codex 0.164.0，Node 26.5.0；模型与强度及启动参数见 final-fixture-inspection.log。没有供应商模型回合，也不据此声称真实模型能力或性能改善。

**当前日期事实**：T-195 实际于 2026-10-31 22:51:39～22:52:03 EDT 运行；Codex 启动为 `2026-11-01T02:51:44.039Z`，即本地 10 月 31 日晚。这次没有经过回拨，不能按任务描述写成“回拨已过，所以无法复现”；也没有改系统日期或时区来回避原检查。专项红态靠外部注入时刻复现，真实回归靠当前机器时间运行，两者明确区分。

**T-136 新发现（范围外，未修）**：旧测试使用 `datetime.now().astimezone()` 得到固定偏移的 Python `timezone`，再加两天。当前 `-04:00` 被带到 11 月 2 日，测试发出的 `14:01Z` 实际是纽约 `09:01 EST`，而保存的日程是 10:00，产品没有触发符合它收到的时刻。按日历推算应为 `15:01Z`。证据 [diagnostic-t136.log](diagnostic-t136.log)；这是测试时钟诊断，不当作定时产品绿态。基线同败支持它与本次 Codex 扫描变更无关。没有改测试、切 UTC 掩盖失败或扩修定时逻辑。

## 复跑、现场与边界检查

每份运行的准确命令、cwd、TZ、TMPDIR、时间、退出码在同名 `.command.json`；[COMMANDS.md](COMMANDS.md) 为完整索引，`replay.py` 自动选新输出名，保护旧结果。常用重跑命令（从 T-221 worktree 执行）：

```sh
TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py red-extracted
TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py green-days
TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py mutant-miss-panes
TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py regression-t195
TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py regression-t135
TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py regression-t136
```

红态重跑会把保存的修前 helper 放到隔离源码副本，用当前同一测试复现；不会把已修复候选上的绿态冒充历史红态。真实日期回归重跑结果受运行当天时区／日期条件影响，历史时刻以原始元数据为准。

现场保留：

- T-195：`/private/tmp/t195-8y6un44x`。
- T-135：`/private/tmp/t135-zg9pzrub`（含界面截图）。
- T-136 候选失败：`/private/tmp/t136-q1hpqpx4`；基线失败：`/private/tmp/t136-dlw6qg2l`。
- 所有日期红绿态与变异的目录由各自 JSON `root` 指向，源码变异副本由日志 `product` 指向；均未删除。

各测试已调用自身停止流程；核对当前候选后台路径和四个回归夹具均无存活进程，T-195 隔离 Codex home 已整体删除，见 [final-fixture-inspection.log](final-fixture-inspection.log)。测试服务由 runner 的 `start_new_session`、产品后台的 detached 启动和 Electron 的 `start_new_session` 脱离调用进程组。不连接 Herdr/hc，不操作其他 worktree，也不写用户全局配置。

`git diff --check`：PASS，[final-diff-check-doc-synced.log](final-diff-check-doc-synced.log)。四处调用与旧写法静态检查：PASS，[final-scan.log](final-scan.log)。项目地图首次检查正常；修改产品后曾提示 README stale（原输出 [final-project-map.log](final-project-map.log) 保留），同步日期说明后 Problems 0、Stale living docs 0，[final-project-map-doc-synced.log](final-project-map-doc-synced.log)。没有修改地图来消除提示。报告与源文件按 UTF-8 无 BOM 保存并回读核对。

## 验收条目状态

| 票面条目 | 状态 | 依据／限制 |
| --- | --- | --- |
| 修前产品同段计算的 DST 漏次日红态 | PASS | red-extracted，注入 T-219 的实际启动和现在时刻；原循环抽取后失败，未另写算法 |
| 同条件转绿；春、秋、月、年边界和中间每一天 | PASS | green-days，196 项全过；日期数组硬编码；八组输入、四个真实消费者 |
| 四处共用本地日历范围，归档保留前一天、删除旧公式 | PASS | candidate.patch、final-scan、四个漏改变异与前一天变异 |
| 当前日期 T-195 正常通过、T-219 第 6 项修复证据 | PASS | regression-t195 16 项；产品缺陷修复证据成立，但按边界不回写 T-219 或票面 |
| 独立 agy 只读审查无阻塞意见 | INCOMPLETE | 当前要求禁止真实供应商模型调用，本回合未启动 agy；不得以实现者自检替代独立审查 |

用户补充要求：失败清单先写、红绿态顺序、至少一个变异、T-219 包装复制与只读、所有命中回归逐个运行、证据与重跑命令、无 commit/push 均已执行。回归“已运行”不等于“全通过”：T-136 保持 INCOMPLETE，未运行到的后续条目没有记 PASS。初稿见 REPORT-before-implementation.md。

## 需要主控决定

1. 安排 **独立 agy 只读审查**，审查冻结候选 candidate.patch 与本报告；本回合不调用供应商模型，也不把自检计为该验收。完成检查点遵循 [behavioral-acceptance-review 技能](/Users/luckye/.agents/skills/behavioral-acceptance-review/SKILL.md) 的要求：`Review one frozen candidate snapshot in a fresh, read-only context.` 本回合是实现上下文，因此独立审查状态为 INCOMPLETE；详见 acceptance-checkpoint.md。
2. 为 T-136 固定偏移的测试时钟另行处理缺陷，并决定是否接受“专项与 T-195/T-135 已通过，T-136 基线同败”的本次交付范围。最小方向是让测试按具名本地时区推算跨 DST 的日程时刻，重新证明定时相关断言；本回合不改该测试、不改定时产品行为。
3. 由主控在获审查结论后更新 T-221、T-219 第 6 项的状态并办理后续提交／集成。本回合未改 `.project-map/`、未改 T-219-evidence、未 commit、未 push。实现候选可以审查，但整票尚不具备全部 PASS 条件。


## 第二轮（2026-10-31）：具名本地时区与同类普查

**状态：INCOMPLETE（指定修复与回归 PASS；另有不同根因的定时产品发现待主控决定，独立 agy 审查由主控安排）。** 第一轮全文原样保留；本节是第二轮新增结果，不回写第一轮当时的结论。

授权依据为主控本轮消息及只读取得的更新票面 [round2-ticket-readonly.md](round2-ticket-readonly.md)。主 checkout 仅按要求读取这份票面，未写入；worktree 的 `.project-map/` 未修改。实施前的失败方式、目标、非目标与未知已写入 [round2-plan.md](round2-plan.md)。继续使用 project-map、evidence-first-testing、document-writing；同类第二次出现后按 close-the-loop 检查测试与产品，而非只修被点名的一行。

### 改动与反例

- 新增 `workbench/tests/local_calendar.py`：在 **fixture.env** 下询问 Node 的 IANA 时区名称，用 `datetime.now(ZoneInfo(name))` 生成本地时刻。由此与真实后台使用相同时区，不从 `astimezone()` 取固定偏移，不猜缩写，无 UTC fallback。
- T-136 仅替换测试时钟来源；两天后 10:00、前一分钟／后一分钟、重复 tick、关闭后下周不启动的算法与断言保留。已有 UTC 序列化只把确定后的同一时刻送进协议，不是切换 UTC 以避开 DST。
- 普查发现 T-137 同类缺陷：两处 `datetime.now().astimezone()` 都改用共享具名时钟；`next_monday_nine` 继续按本地日历计算，tick 直接序列化该具名时区时刻。没有改产品、跳过或放宽断言。
- 新增 `workbench/tests/test_t221_calendar_clocks.py`：把“现在”注入共享真实时钟，IANA zone 查询仍真实执行，六组日期／偏移预期手工写死，覆盖春进、秋退的两天与七天，以及月末、年末。对旧固定偏移的等价变异，四组 DST 用例失败，月末／年末两组仍通过。这样在全年任意日期都能检查时钟是否又冻结偏移。
- 工作台 README 增加共享时钟与固定日期检查入口。两处产品日历扫描修复和 T-195/T-135 第一轮代码未再变动。第二轮完整候选见 [r2-candidate.patch](r2-candidate.patch)、[r2-candidate.json](r2-candidate.json)，首轮候选文件原样保留。

### 红态、绿态与回归

| 运行 | 状态 | 实际结果／证据 |
| --- | --- | --- |
| T-136 日历红态 | PASS（成功复现缺陷） | 复用已保存的 [regression-t136.json](regression-t136.json) 与 [regression-t136-baseline.json](regression-t136-baseline.json)：两次都在 `schedule_fires_once_at_its_time` 失败。主控已允许复用。 |
| 本轮 T-136 修前再跑 | INCOMPLETE（基础设施） | [r2-red-t136.log](r2-red-t136.log)：Electron 构建写文件报 `No space left on device`，尚未运行到日历断言；不能把它计为日历红态。现场 `/private/tmp/t136-em65eaom` 保留，失败构建槽由原测试既有停止流程清理。 |
| 本轮 T-137 修前 | PASS（成功复现同类缺陷） | [r2-red-t137.json](r2-red-t137.json)：前 7 项通过，`schedule_on_fires_with_chosen_runner` 失败；本地周一 09:00 使用旧偏移，触发列表为空。现场 `/private/tmp/t137-bocpsvb0`。 |
| T-136 完整绿态 | PASS | [r2-green-t136.json](r2-green-t136.json)：13 项全过，实际为 `2026-11-02T15:00:00.000Z`，对应纽约 10:00 EST；关闭后下周不触发、启动失败记录、重试不丢范围均真正执行通过。 |
| T-137 完整绿态 | PASS | [r2-green-t137.json](r2-green-t137.json)：10 项全过，实际为 `2026-11-02T14:00:00.000Z`，对应纽约 09:00 EST；之后手动复盘和重启保留设置均执行通过。 |
| 固定日历时钟检查 | PASS | [r2-calendar-clocks.log](r2-calendar-clocks.log)：1 个 unittest、6 个具名子场景全部通过。 |
| 固定偏移反事实 | PASS（正确拒绝） | [r2-mutant-fixed-offset.log](r2-mutant-fixed-offset.log)：恢复旧时钟后四个 DST 子场景按日期偏移断言失败，进程退出 1；没有修改候选源文件。 |

T-136 后续未暴露新的测试过时或产品失败，13 项全部跑完。T-137 是新增 helper 的另一个实际调用者，完整回归也通过；调用者普查见 [r2-helper-callers.log](r2-helper-callers.log)。helper 是独立测试模块，未修改通用 `scripted_claude.py`，其他现有测试不导入它；没有为未受影响且第一轮已接受的 T-195、T-135 重跑整套。

修前失败和绿态均在本机实际 2026-10-31 晚、纽约回拨前运行，没有改系统日期或切 UTC。T-136 绿态于 23:03:52～23:04:51 EDT，T-137 绿态于 23:05:13～23:07:21 EDT；日志的 UTC 日期已是 11 月 1 日，不能据此误判本地已经回拨。两份绿态均使用真实后台／门禁／CLI／Electron，模型仍为本地脚本化接口，无供应商模型调用。

第一次同时运行的 T-136 发生磁盘空间错误后，绿态改为串行，未清理或移动他人数据，也未覆盖失败输出。没有将 ENOSPC 改判为已修复的日期问题；后续串行完整通过只证明对应测试在那次运行通过。

### 同类写法普查清单

范围：当前 workbench/src、workbench/app、workbench/tests、acceptance、scripts、docs/assets；排除历史 evidence、records、findings、reports 和依赖。主扫描覆盖 660 份源码／脚本／样式文件，共 48 个命中；每个命中均列在下表，另补 4 个修后不再匹配旧模式的上下文位置。扩大日期与数字搜索见 r2-audit-wide.log；原始模式与每行源码见 r2-audit.log。

本轮没有发现尚未修复的“固定 24 小时／固定偏移跨本地日期”产品路径。定时产品的 setHours/setDate 顺序问题是另一种根因，单列为 INCOMPLETE，未把它报成安全或已修复。

| 位置 | 状态／处理 | 是否在夏令时出错及理由 |
| --- | --- | --- |
| `workbench/src/trajectoryArchive.ts:84` | PASS；首轮已修，沿用已接受的红绿态与漏改变异 | 原循环的本地日历步长配固定 24 小时终点确实漏扫；首轮已共用 codexScanDays。此处只格式化其本地日期。 |
| `workbench/src/trajectoryArchive.ts:102` | PASS；首轮已修，沿用已接受的红绿态与漏改变异 | 原循环的本地日历步长配固定 24 小时终点确实漏扫；首轮已共用 codexScanDays。此处只格式化其本地日期。 |
| `workbench/src/panes.ts:1246` | PASS；首轮已修，沿用已接受的红绿态与漏改变异 | 原循环的本地日历步长配固定 24 小时终点确实漏扫；首轮已共用 codexScanDays。此处只格式化其本地日期。 |
| `workbench/src/retrospective.ts:60` | INCOMPLETE；不改定时产品；不同根因，需主控决定 | setDate 本身不含固定 24 小时；09:00/10:00 跨回拨正确。但 59 行先 setHours、再在此回退日期，春季跳过当天会污染有效周一 02:30；独立产品反例已保存。 |
| `workbench/src/retrospective.ts:61` | INCOMPLETE；不改定时产品；不同根因，需主控决定 | setDate 本身不含固定 24 小时；09:00/10:00 跨回拨正确。但 59 行先 setHours、再在此回退日期，春季跳过当天会污染有效周一 02:30；独立产品反例已保存。 |
| `workbench/src/nativeLink.ts:141` | PASS；首轮已修，沿用已接受的红绿态与漏改变异 | 原循环的本地日历步长配固定 24 小时终点确实漏扫；首轮已共用 codexScanDays。此处只格式化其本地日期。 |
| `workbench/src/codexScanDays.ts:5` | PASS；不改 | 起点偏移、明天和循环递增均为本地 setDate，比较本地午夜边界，不假定一天为 24 小时。 |
| `workbench/src/codexScanDays.ts:7` | PASS；不改 | 起点偏移、明天和循环递增均为本地 setDate，比较本地午夜边界，不假定一天为 24 小时。 |
| `workbench/src/codexScanDays.ts:9` | PASS；不改 | 起点偏移、明天和循环递增均为本地 setDate，比较本地午夜边界，不假定一天为 24 小时。 |
| `docs/assets/showcase.js:120` | PASS；不改 | 扩大数字检索的无关命中：尺寸、颜色、PID、退出码、文本截断长度或历史注释，不参与日期／时长运算。 |
| `docs/assets/showcase.js:121` | PASS；不改 | 扩大数字检索的无关命中：尺寸、颜色、PID、退出码、文本截断长度或历史注释，不参与日期／时长运算。 |
| `docs/assets/demo.js:714` | PASS；不改 | 只从当前 Date 取月日时分秒展示记录，不跨日推算。 |
| `workbench/app/style.css:14` | PASS；不改 | 扩大数字检索的无关命中：尺寸、颜色、PID、退出码、文本截断长度或历史注释，不参与日期／时长运算。 |
| `docs/assets/demo.css:14` | PASS；不改 | 扩大数字检索的无关命中：尺寸、颜色、PID、退出码、文本截断长度或历史注释，不参与日期／时长运算。 |
| `acceptance/page/check.mjs:11` | PASS；不改 | 扩大数字检索的无关命中：尺寸、颜色、PID、退出码、文本截断长度或历史注释，不参与日期／时长运算。 |
| `acceptance/page/check.mjs:73` | PASS；不改 | 扩大数字检索的无关命中：尺寸、颜色、PID、退出码、文本截断长度或历史注释，不参与日期／时长运算。 |
| `workbench/app/main.ts:842` | PASS；不改 | 扩大数字检索的无关命中：尺寸、颜色、PID、退出码、文本截断长度或历史注释，不参与日期／时长运算。 |
| `workbench/app/renderer.tsx:95` | PASS；不改 | 将 now - Date.parse(iso) 的已流逝秒数换成小时／24 小时时长单位，既不生成日历日期，也不要求日界对齐。 |
| `workbench/app/renderer.tsx:96` | PASS；不改 | 将 now - Date.parse(iso) 的已流逝秒数换成小时／24 小时时长单位，既不生成日历日期，也不要求日界对齐。 |
| `workbench/app/MetricsPage.tsx:23` | PASS；不改 | 从本地 T00:00:00 解析 date input，终点用 setDate 加一天；23/25 小时日会保留本地午夜边界。 |
| `scripts/inbox:12` | PASS；不改 | 15 分钟、1 小时、7×24 小时均是消息年龄／延迟阈值；now 与记录统一成 UTC，不代表某个本地日历日程。 |
| `scripts/inbox:13` | PASS；不改 | 15 分钟、1 小时、7×24 小时均是消息年龄／延迟阈值；now 与记录统一成 UTC，不代表某个本地日历日程。 |
| `scripts/inbox:14` | PASS；不改 | 15 分钟、1 小时、7×24 小时均是消息年龄／延迟阈值；now 与记录统一成 UTC，不代表某个本地日历日程。 |
| `scripts/inbox:38` | PASS；不改 | 把已有时区的同一时刻转成 UTC 供时长比较，无日期增减；403 行的 now 也是 UTC。 |
| `workbench/tests/test_t139_layout_store.mjs:120` | PASS；不改 | 扩大数字检索的无关命中：尺寸、颜色、PID、退出码、文本截断长度或历史注释，不参与日期／时长运算。 |
| `workbench/tests/test_t107_daemon_readonly.mjs:42` | PASS；不改 | 日志目录取当前本地日期；40 行仅把启动时间设成日志前 60 秒（时长），不把一分钟当日历日。 |
| `workbench/tests/test_t195_native_link_e2e.py:391` | PASS；不改 | naive 本地 datetime 加一天只用于 strftime 年/月/日路径，不转换为 epoch 或附固定偏移；这是日历字段运算，跨 DST 仍取明天日期。 |
| `workbench/tests/test_t137_reflect_e2e.py:159` | PASS；本轮修复时钟来源；159/160 行日历算法保留 | 原 after 来自无参数 astimezone()，跨两天／七天会保留旧偏移，已实测红态。179、265 行改用 ZoneInfo 时钟后，此处 timedelta 按具名时区的日历日期计算。 |
| `workbench/tests/test_t137_reflect_e2e.py:160` | PASS；本轮修复时钟来源；159/160 行日历算法保留 | 原 after 来自无参数 astimezone()，跨两天／七天会保留旧偏移，已实测红态。179、265 行改用 ZoneInfo 时钟后，此处 timedelta 按具名时区的日历日期计算。 |
| `workbench/tests/test_t091_regression_collection.py:35` | PASS；不改 | 扩大数字检索的无关命中：尺寸、颜色、PID、退出码、文本截断长度或历史注释，不参与日期／时长运算。 |
| `workbench/tests/test_t091_regression_collection.py:41` | PASS；不改 | 扩大数字检索的无关命中：尺寸、颜色、PID、退出码、文本截断长度或历史注释，不参与日期／时长运算。 |
| `workbench/tests/t093_fake_login_peer.py:65` | PASS；不改 | 扩大数字检索的无关命中：尺寸、颜色、PID、退出码、文本截断长度或历史注释，不参与日期／时长运算。 |
| `workbench/tests/t093_fake_login_peer.py:69` | PASS；不改 | 扩大数字检索的无关命中：尺寸、颜色、PID、退出码、文本截断长度或历史注释，不参与日期／时长运算。 |
| `workbench/tests/test_t181_question_text_e2e.py:104` | PASS；不改 | 扩大数字检索的无关命中：尺寸、颜色、PID、退出码、文本截断长度或历史注释，不参与日期／时长运算。 |
| `workbench/tests/test_t136_retrospective_e2e.py:289` | PASS；本轮已修；13 项全套通过 | 原固定偏移加两天跨回拨差一小时；现用与后台相同 IANA 时区的 local_now + timedelta，保持墙钟 10:00。 |
| `workbench/tests/test_t136_retrospective_e2e.py:294` | PASS；不改 | 先在具名本地时区确定 10:00，再加／减一分钟；转 UTC 只序列化同一时刻，原协议与断言未改。 |
| `workbench/tests/test_t136_retrospective_e2e.py:295` | PASS；不改 | 先在具名本地时区确定 10:00，再加／减一分钟；转 UTC 只序列化同一时刻，原协议与断言未改。 |
| `workbench/tests/test_t136_retrospective_e2e.py:305` | PASS；随时钟来源修复；日历算法与断言不改 | 原 slot 固定偏移时，跨周也会错；slot 改为 ZoneInfo 后加七天按日历处理，最后才把同一时刻序列化为 UTC。关闭后不触发断言已真正执行。 |
| `workbench/tests/test_t162_role_records_metrics_e2e.py:174` | PASS；不改 | 174 行以 new Date(年,月,日+1) 构造本地次日午夜；179 行只格式化本地日期输入值，均没有固定 24 小时。 |
| `workbench/tests/test_t162_role_records_metrics_e2e.py:179` | PASS；不改 | 174 行以 new Date(年,月,日+1) 构造本地次日午夜；179 行只格式化本地日期输入值，均没有固定 24 小时。 |
| `workbench/tests/test_t091_pane_ipc.mjs:60` | PASS；不改 | 扩大数字检索的无关命中：尺寸、颜色、PID、退出码、文本截断长度或历史注释，不参与日期／时长运算。 |
| `workbench/tests/test_t124_controller_e2e.py:386` | PASS；不改 | 配额夹具的 resets_at 是未来 epoch 秒，+86400 仅安排另一个较晚重置时刻；没有约定为本地明天某个墙钟时间。 |
| `workbench/tests/test_t170_failed_launch_reclaim_e2e.py:17` | PASS；不改 | 扩大数字检索的无关命中：尺寸、颜色、PID、退出码、文本截断长度或历史注释，不参与日期／时长运算。 |
| `workbench/tests/run_t093_login_chain.py:206` | PASS；不改 | 扩大数字检索的无关命中：尺寸、颜色、PID、退出码、文本截断长度或历史注释，不参与日期／时长运算。 |
| `workbench/tests/test_t221_codex_scan_days.ts:51` | PASS；不改 | 只将产品给出的 Date 格式化成本地年/月/日；预期数组另行写死，不做跨日算术。 |
| `workbench/tests/test_t221_calendar_clocks.py:34` | PASS；不改 | 被测对象是新的具名本地时钟；日历加两天／七天后与手工写死的春、秋、月末、年末日期和偏移比对。固定偏移变异在四组 DST 断言失败。 |
| `workbench/tests/test_t167_codex_start_e2e.py:77` | PASS；不改 | HTTP 配额 header 的 reset-at 是 now 后 86400 秒的到期时刻，不是本地日历日程；用时长正确。 |
| `workbench/tests/controlled_quality_pty.ts:35` | PASS；不改 | 只格式化写记录时的当前本地日期，无跨日推算。 |
| `workbench/tests/test_t137_reflect_e2e.py:162` | PASS；本轮改为 when.isoformat() | 已有具名时区的日程直接序列化；删除多余无参数 astimezone，不在序列化前冻结偏移。 |
| `workbench/tests/test_t137_reflect_e2e.py:179` | PASS；本轮改用 local_now(fixture.env) | 原 datetime.now().astimezone() 冻结当前偏移，使下周一 09:00 跨 DST 时错误；改用具名 ZoneInfo。 |
| `workbench/tests/test_t137_reflect_e2e.py:265` | PASS；本轮改用 local_now(fixture.env) | 第二次下周一计算也必须修；不能只修默认关闭场景的第一次时钟。 |
| `workbench/tests/local_calendar.py:10` | PASS；新增共享测试时钟 | 从 fixture.env 下的 Node 读取 IANA zone，再用 datetime.now(ZoneInfo(name))；不猜固定偏移、不切 UTC、无 fallback。 |


补充普查覆盖 `workbench/terminal`（含隐藏 zsh 启动文件）、`workbench/hooks`、`workbench/bin`：共 16 份源文件／启动资源，未发现相关日期或固定一天写法，见 [r2-audit-shell.log](r2-audit-shell.log)；`rg` 退出 1 表示零命中。没有把 CSS 颜色、窗口尺寸、PID 等数字命中当日期缺陷，也没有把历史证据里的旧算法当当前产品路径。逐处清单另存 [r2-audit-decisions.md](r2-audit-decisions.md) 与机器可读 JSON。

### 普查发现的另一种定时产品缺陷（未修）

**INCOMPLETE，需要主控决定范围。** `workbench/src/retrospective.ts:59` 先在查询当天调用 `setHours`，60／61 行才回退到计划星期。对以下外部手工 oracle，直接调用真实 `Retrospectives.due()`：

- 时区 America/New_York；日程每周一 02:30，从 2026-03-01 生效。
- 查询时刻 2026-03-08 12:00 EDT；此前最近的周一是 03-02，合法计划时刻为 02:30 EST，即 `2026-03-02T07:30:00.000Z`。
- 产品实际给 `2026-03-02T08:30:00.000Z`，即 03:30 EST。根因是在 03-08 的不存在时刻 02:30 上先发生了归一化，再把被改成 03:30 的时钟回退到周一。

证据 [r2-product-due-audit.log](r2-product-due-audit.log)，重跑入口 [r2_probe_due.ts](r2_probe_due.ts)。同一探针的秋季周一 09:00、10:00 两个对照均正确；这个错误不是本轮固定偏移或固定 24 小时的根因，也不是两条完整 E2E 的失败。未自行改定时产品，遵守本轮“不改定时产品的行为”的限制；没有把该位置写成“夏令时完全安全”。最小后续方向是先选目标日历日期、再设置墙钟小时，并补有效目标星期与跳过／歧义小时的独立反例；是否并入本票由主控裁定。

### 最终检查、复跑与交接

- `git diff --check`：PASS，[r2-final-diff-check.log](r2-final-diff-check.log)。
- project-map status：PASS，Problems 0、Stale living docs 0，[r2-final-project-map.log](r2-final-project-map.log)。开始状态也已保存为 r2-status-start.log；没有改 `.project-map/`。
- 第二轮四个真实回归夹具均无存活进程；13／10 项绿态、UTF-8 无 BOM、地图不变和首轮报告前缀检查通过，[r2-final-inspection.log](r2-final-inspection.log)。T-136 绿态现场 `/private/tmp/t136-9xsb7e0c`，T-137 绿态现场 `/private/tmp/t137-fpbqdwa6`，失败现场也保留。
- 本轮写入仍仅限 T-221 worktree、T-221-evidence 以及测试自身的 `/private/tmp` 夹具；每次运行固定 TMPDIR。后台由原 detached／start_new_session 机制启动。未接 Herdr 或 hc default core，未写用户全局配置，未 commit，未 push。
- 全部原命令、退出码和复跑入口见 [r2-COMMANDS.md](r2-COMMANDS.md) 与同名 `.command.json`。常用：

```sh
TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py r2-green-t136
TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py r2-green-t137
TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py r2-calendar-clocks
TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py r2-mutant-fixed-offset
TMPDIR=/private/tmp python3 /Users/luckye/Documents/Code/a2a-worktrees/T-221-evidence/replay.py r2-product-due-audit
```

固定偏移变异和产品缺陷探针预期退出 1；不能把该退出码改成产品 PASS。修前 E2E 的原命令现在会使用已修复测试时钟；恢复旧时钟的完整 E2E 包装 `r2_legacy_e2e.py` 仅为复跑保留，本轮没有再次启动两套大夹具，不能把该未执行包装当新运行证据。

| 第二轮新增验收／要求 | 状态 | 依据 |
| --- | --- | --- |
| T-136 跨 DST 仍按本地墙钟推算：修前失败、修后通过 | PASS | 第一轮两份日历红态 + 本轮 13 项完整绿态；固定日期时钟反事实全年可复跑 |
| 后续原本未执行的 T-136 检查真正完成 | PASS | 定时关闭、启动失败记录、重试保留范围全部执行通过，无删减断言 |
| 同类写法逐处普查并修复 | PASS（普查与本类修复） | 660 份主扫描、48 个命中逐行判定，4 个上下文补项；启动脚本／钩子补查无命中；T-137 同类修复且完整绿态 |
| 普查中的旁类产品缺陷 | INCOMPLETE | 02:30 的 setHours/setDate 顺序反例已上报，未擅自改变定时产品 |
| 受影响的现有测试回归 | PASS | T-136 13 项、T-137 10 项全部通过；共享时钟只有这两份 E2E 与新时钟检查使用 |
| diff、项目状态、报告追加与边界 | PASS | 最终日志；第一轮内容作为完整字节前缀保留，仅追加本节 |
| 独立 agy 审查 | INCOMPLETE（主控负责） | 按主控明确安排，本 worker 不启动供应商模型或自行代审 |

### 需要主控决定（第二轮）

1. 定时产品在“春季跳过当天查询合法周一 02:30”时给出 03:30 的缺陷，是否另票或明确扩入 T-221；证据和最小方向见上。本轮指定的固定偏移／固定 24 小时类修复与两套真实 E2E 已通过，但不能据此把该产品发现上调为通过。
2. 依主控安排，对冻结的 **r2-candidate.patch** 进行独立 agy 只读审查，并处理后续票面、提交与集成。第一轮 candidate.patch 仅代表第一轮，不应用它替第二轮审查。worker 到此交接结束。
