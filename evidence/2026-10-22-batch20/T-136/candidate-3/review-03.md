# T-136 候选 3（提交 `077b83728`）独立审查报告

本审查以改动 diff（[`full.diff`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/agy-t136c3-AsYi/full.diff)，父提交为 `338c51b4f`）、上一轮审查报告（[`candidate-2/review-02.md`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-136/candidate-2/review-02.md)）、本轮结果（[`candidate-3/RESULTS.md`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-136/candidate-3/RESULTS.md)）及三轮完整运行证据（含真实 Haiku 运行证据 [`candidate-1/real-haiku/`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-136/candidate-1/real-haiku/) 和端到端产物 [`candidate-3/e2e/`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-136/candidate-3/e2e/)）为准，采用纯只读方式核对。

---

## 一、重点核对结论

### 1. 两条发现的修复核对与新引入问题分析

#### (1) 审查 02 发现 1（原 P2）：启动失败后下次复盘范围起点错误（已修复，无新问题）
- **实现位置**：[`workbench/src/retrospective.ts:77-79`](file:///Users/luckye/Documents/Code/a2a/workbench/src/retrospective.ts#L77-L79) 与 [`workbench/README.md:963-964`](file:///Users/luckye/Documents/Code/a2a/workbench/README.md#L963-L964)。
- **代码核对**：
  ```ts
  // From the end of the last run that started: a run whose terminal never opened reviewed nothing (review 02).
  const since = range.since !== undefined ? range.since
    : this.runs(project).findLast(run => !this.events(run.id).some(event => event.type === 'start_failed'))?.until ?? null;
  ```
- **行为分析**：
  1. 使用 `findLast` 从历史运行倒序查找，若最近的运行存在 `start_failed` 事件，则直接跳过，向前追溯至上一次真正启动过的运行；
  2. 若该项目此前从未成功启动过复盘（包括只有失败记录或初次运行），`findLast` 返回 `undefined`，`since` 解析为 `null`，复盘包涵盖全部历史数据；
  3. 若此前存在成功启动的运行，`since` 正确取该成功运行的 `until`，中途因偶发故障没能启动的运行区间不会被遗漏。
- **环境与兼容性**：项目 Node 引擎为 Node 26.5+（`package.json` 指定 `>=26.5.0 <27`），`Array.prototype.findLast` 原生支持。无状态污染，未引入新缺陷。

#### (2) 审查 02 发现 2（原 P3）：`firstLine()` 缺乏打开异常防护（已修复，无新问题）
- **实现位置**：[`workbench/src/trajectoryArchive.ts:86-88`](file:///Users/luckye/Documents/Code/a2a/workbench/src/trajectoryArchive.ts#L86-L88)。
- **代码核对**：
  ```ts
  // Another session's file that vanished, cannot be opened, or is still being started is simply not this one.
  let parsed: any = null;
  try { const meta = firstLine(join(dir, name)); parsed = meta && JSON.parse(meta); } catch { continue; }
  ```
- **行为分析**：
  1. 将 `firstLine(join(dir, name))` 与 `JSON.parse(meta)` 统一置于 `try ... catch { continue; }` 内；
  2. 当遍历 `sessions/YYYY/MM/DD/` 遇到并发轮转删除（`ENOENT`）、权限异常（`EACCES`）或半写入的损坏 JSON 时，均安全捕获并直接跳过，不再中断 `codexRolloutIn()` 和外层 `sources()`，彻底消除了后台 30 秒轮询归档被单文件异常阻断的风险；
  3. `firstLine()` 内部已有 `try ... finally { closeSync(fd); }` 保护，不会造成文件描述符泄漏。未引入新缺陷。

---

### 2. 新检查与变异证明核对

在 [`workbench/tests/test_t136_retrospective_e2e.py`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t136_retrospective_e2e.py) 中：
1. **新增检查项**：`retry_after_failed_start_keeps_range`（行 321–325）。在制造项目目录移走导致 `start_failed` 后，恢复目录并重新触发复盘，断言重试运行成功且 `again['run']['since'] is None`。
2. **反例与变异击杀核对**（核对 [`candidate-3/e2e/exits.txt`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-136/candidate-3/e2e/exits.txt) 与各 json 产物）：
   - **候选 2 父提交反例（`red-candidate-2.json`，`338c51b4f`）**：精准失败于 `AssertionError: retry_after_failed_start_keeps_range`（重试的 `since` 错误取到了失败时刻的时间戳 `19:57:29.749Z`，而非 `None`），退出码 1。
   - **变异体反例（`mutant-since-after-failed-run.json`）**：将 `.findLast(...)` 还原为 `.at(-1)`，精准失败于 `retry_after_failed_start_keeps_range`，退出码 1。
   - **绿态运行（`green.json`）**：通过包含新增检查项在内的全部 13 项 checks，退出码 0。
3. **证明充分性**：检查项期望独立于实现，父提交与变异体双重反例精准击杀，充分证明修复有效。

---

### 3. 综合三轮核对：T-136 验收条件全覆盖情况

对照 [T-136 任务卡](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-136-retrospective.md) 四项验收条件：

| 验收条件 | 达成依据与核对来源 | 结论 |
| :--- | :--- | :--- |
| **复盘包** | 经 `package_matches_scenario` 严格校验任务、门禁、审查、打分、问题、输入、尾注、指标快照与夹具数据一致；经 `second_package_only_in_range` 与 `second_package_archive_in_range`（变异击杀）证明范围外历史任务与归档均不进包。 | **满足** |
| **真实入口** | `candidate-1/real-haiku/run-02.json` 经真实 Electron 界面触发 Claude Code（`claude-haiku-5-5`），真实登录凭据，会话只写 `out/`；生成的 `findings/2026-10-22-retrospective-56c536cd.md` 报告保真；越权写项目被沙箱和权限拦截（变异 `out-not-confined` 证明）。 | **满足** |
| **周期** | `schedule_fires_once_at_its_time` 注入时钟到点启动一次且不重复；`schedule_off_does_not_fire` 界面关闭后下一周不再触发；变异体 `schedule-fires-when-disabled` 精准被杀。 | **满足** |
| **截图与复现命令** | 端到端与真实运行均包含完整的 `commands.sh`、`exits.txt`；测试截图覆盖启动、建议、批准、导入失败及周期关闭；证据与夹具按 T-088 策略归档并留有 `fixtures.archive.json`。 | **满足** |

---

## 二、审查发现项清单（Findings）

本轮改动无新增 P0–P3 缺陷。

---

## 三、总体结论

**PASS**

### 判定理由
1. 上一轮独立审查报告中指出的 P2 缺陷（启动失败后范围起点继承错误）与 P3 缺陷（`firstLine` 异常阻断归档）均已在根因层面妥善修复，未引入新问题；
2. 新增检查项期望值独立，针对父提交候选 2 与变异体 `since-after-failed-run` 的反例均精准击杀，证明有效；
3. 综合三轮审查与真实运行证据，T-136 任务卡中规定的复盘包、真实入口、周期判定、写入边界约束以及截图/复现命令等验收条件已全部满足。
