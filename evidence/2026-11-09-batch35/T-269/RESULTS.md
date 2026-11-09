# T-269 结果记录

这份记录由 Claude Code 会话 `8be1abdd-5af9-4023-bff8-cbc0f40d9a84` 写。命令都在仓库根 `/Users/luckye/Documents/Code/a2a` 下运行。运行时是 `/Applications/Enchanted.app` 0.1.6 自带的 Node v24.18.1，用 `ELECTRON_RUN_AS_NODE=1` 启动。父版本是 `519fafb21`。

## 改动

- `workbench/src/store.ts`：
  - 建表时加两个索引：`orchestration_events(launch, type)`、`orchestration_events(type)`；
  - 新增 `launchEvents(launch)`，按索引只读一个会话的事件，按 seq 排序。
- `workbench/src/panes.ts` 12 处、`workbench/src/daemon.ts` 1 处：`store.read().filter(e => e.launch === X …)` 改成 `store.launchEvents(X)`，原有的其他过滤条件保留。这条读取路径是审查 01 第 5 条指出的：hook 处理和每秒一次的窗格快照都走它，而它每次都把整张表读出来、逐行解析。
- `workbench/README.md`：补一句索引和 `launchEvents` 的说明。

## 测试与判红

```bash
ELECTRON_RUN_AS_NODE=1 /Applications/Enchanted.app/Contents/MacOS/Enchanted workbench/tests/test_t269_event_indexes.mjs <新的输出路径>
```

| 运行 | 被测代码 | 结果 | 文件 |
|---|---|---|---|
| 绿态 | 本次候选 | PASS，19 项全过 | `green-02.json` |
| 父版本 | `519fafb21` 的 store、panes、daemon | FAIL，18 项里 14 项不过：没有索引，没有按 launch 读取，11 条查询全表扫描，源码里还有读全表再按 launch 过滤的写法 | `red-parent-02.json` |
| 变异 1 | 候选去掉 `(launch, type)` 索引 | FAIL，6 项：缺这个索引；4 条按 launch 的查询只能按 type 缩小范围 | `mutant-no-launch-index.json` |
| 变异 2 | 候选的 `questions()` 改回读全表再过滤 | FAIL，1 项：源码检查发现读全表再按 launch 过滤的写法 | `mutant-questions-full-read.json` |
| 变异 3 | 候选的 `launchEvents` 去掉 `ORDER BY seq` | FAIL，1 项：返回顺序不对 | `mutant-launch-read-unordered.json` |

`red-parent-01.json` 是测试第一版在父版本上的输出：16 项里 12 项不过，11 条查询全表扫描，其中包括别名查询 `SCAN e`。第一版测试有两个漏洞，就是审查 01 的第 1、2 条：它不核对具体是哪两个索引，带索引的 SCAN 也算通过。所以第一版的结论已经作废，`red-parent-01.json` 只作为历史保留。第一版的绿态输出 `green-01.json` 在重写测试时被我删掉了，没有留存。

## 正式数据副本上的耗时

`live-copy-timing-01.json`，命令见 `time_live_copy.mjs` 的开头。副本是用 `.backup` 从正式状态文件复制的，复制时只读打开原文件，有 210,547 行，用完已删除。

| 查询 | 修复前 | 修复后 |
|---|---|---|
| 查一条不存在的事件 | 31.7 ms | 0.06 ms |
| 读事件最多的那个会话（1,352 行） | 1,415 ms（读全表再过滤） | 9.1 ms（`launchEvents`） |
| 角色申请列表 | — | 0.28 ms |
| 轨迹归档来源 | — | 112 ms |
| `openPanes` | — | 0.63 ms |

在没有索引的正式数据上第一次打开（包括建索引），耗时 311 ms；第二次打开 1 ms。

在这次测量里，没有索引的那几条查询先跑过，数据库已经预热。所以 311 ms 只是这份没有竞争的副本上的数字，不能当作冷启动的上限，也不能当作有别的连接抢锁时的上限。

## 现有测试

`run_regression.py` 跑 15 个用到 store、问题投影或回合信任的测试。父版本和候选各跑一次。父版本那次是把 store、panes、daemon 三个文件临时换回 HEAD 跑的，跑完已还原并逐字节核对。

**作废的第一轮**：`regression-parent.json`、`regression-candidate.json`。复审指出两个问题：
- 两个 T-108 合同文件只导出函数，单独运行时一个场景也没执行，退出码 0 却被我算成了通过；
- `t166` 是我给错了输出路径，测试在准备阶段就失败了。

这两份只作历史保留，结论不再使用。

**第二轮**：`regression-parent-02.json`、`regression-candidate-02.json`。运行器按一条规则判定：退出码 0 本身不算通过，测试必须报告 PASS 才算。两个合同文件改由 `t108_contract_driver.mjs` 调用它们导出的函数，`t166` 改为先建好输出目录。

- 15 项在两边的退出码、状态、判定和错误都一样。比较时去掉了临时路径和进程号。
- 两边都通过的有 5 项：`t109_hierarchy`、`t140_project_events`、`relay_core`、`t166_queued_input`、`t258_codex_late_start`。`t166` 走的是排队输入的历史读取（`panes.ts:2258`）；`t258` 走的是晚启动的信任检查（`panes.ts:1898`）。
- 两个 T-108 合同真正跑了用例，两边失败的用例名单完全一样：
  - answer lifecycle 共 14 个用例，12 个通过；失败的 2 个是 `shell_refusal`、`shell_unknown_pty`。
  - hook failure 共 429 个用例，250 个通过，179 个失败。

  这两组用例走到了改动过的问题投影、回答和信任检查（`panes.ts:2581`、`2586`、`2606`、`2344`、`2516`）。
- 另外 8 项两边都失败，失败原因在父版本上就存在：旧断言跟不上现在的代码、缺 `vm.SourceTextModule`、缺 `~/.codex/packages/app-server-daemon`、`ERR_INVALID_STATE`，以及 `t108_questions` 在第 36 行就停下。其中有些在执行到改动的代码之前就已失败，所以这几项只能说明改动没有让结果变差，不能证明后面那部分代码没有回归。
- `t078_pane_runtime` 失败时不会关掉它启动的 hc core。三轮运行共留下 6 个这样的进程，已全部停止；三轮新建的临时目录也已删除。正式后台的 hc core（42545、99586）和 T-249 验收留下的那一个（857、58541）没有动。

返回顺序：没写 ORDER BY 的事件查询包括按单个 type 相等、按 launch 加 type 相等过滤的，也包括 `hasPaneLayout` 和门禁 `core.ts:4577` 的存在性查询，以及侧栏按 launch 分组取最大值的聚合。我没有发现哪个使用方依赖这些查询的返回顺序，但 SQL 本身不保证它们的顺序，所以这里不作“顺序不变”的普遍承诺。

## 审查

- **审查 01**（gpt-6-astra xhigh，只读，`review-01.md`）：结论“不可合并”，共 5 条。
  - 第 1 条（漏检缺少 `(launch, type)` 索引）：变异 1 判红为证。
  - 第 2 条（放过带索引的全表 SCAN）：由复审员把原反例交给现在的判定、确认被拒为证。变异 2 证的是第 5 条，不是第 2 条。
  - 第 3、4 条：这份记录已补齐证据并更正说法。
  - 第 5 条：已改用 `launchEvents`。
- **复审**（`review-02.md`）：结论“不可合并”。
  - 审查 01 的第 1、2、4、5 条确认已解决；13 处替换逐处核对等价。
  - 敏感路径上没有发现会损坏数据的路径。0.1.6 读写带索引的库，只在内存库里核对过兼容，真实文件的回退没有验证。
  - 拒绝的唯一理由是第一轮回归空跑，已按上面的规则重跑，补出第二轮。按“一次审查，最多一次复审”的规则，不再开第三轮。
- **范围外、早已存在**：侧栏每 3 秒按 launch 分组取最大时间（`sidebar.ts:153`）仍要遍历所有带 launch 的行。复审员的合成夹具上一次 153 ms；我在正式数据副本上量到 22 ms，记录在本节之前那次测量的输出里，没有另存。这一项不在 T-269 里修。

## 还没有的证据

装进正式版之后的后台 CPU、采样和 hook 处理时长，还没有测。
