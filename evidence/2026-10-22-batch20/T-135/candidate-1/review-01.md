# T-135 独立审查报告：轨迹归档（候选 1）

- **审查对象**：提交 [`e0330f663`](file:///Users/luckye/Documents/Code/a2a/workbench/src/trajectoryArchive.ts) 与 [`0383b3cb1`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t135_trajectory_archive_e2e.py)，父提交 `e4d45c511`
- **审查依据**：
  - 任务卡：[T-135-trajectory-archive.md](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-135-trajectory-archive.md)
  - 契约规格：[native-cli-orchestration-2026-10-10.md](file:///Users/luckye/Documents/Code/a2a/.project-map/specs/native-cli-orchestration-2026-10-10.md) 第 8 节“轨迹归档”
  - 候选证据与运行记录：[RESULTS.md](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-135/candidate-1/RESULTS.md) 与 [green.json](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-135/candidate-1/e2e/green.json)
- **审查方式**：只读静态代码走查与证据独立核验，未运行任何 shell 命令，未改动仓库。

---

## 重点审查结论

### 1. 增量与完整行逻辑（[`trajectoryArchive.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/trajectoryArchive.ts)）

- **偏移计算与续接**：
  - 代码通过 `SELECT max(end) FROM trajectory_archive WHERE launch=? AND source=?` 获取上次已记录终点，作为本次 `start` 偏移。
  - 读取从 `start` 到 `size` 的物理字节。下一段写入时记录 `start + complete`，偏移连续性无跳跃无重叠。
- **截断与文件缩小**：
  - 若检测到 `size < start`（行 228–234），明确拒绝按猜测偏移继续，向事件库发送 `trajectory_source_truncated` 事件（以 `${launch}\0${path}\0${size}` 缓存去重防刷），直接跳过，符合契约。
- **半写入行的延迟处理与并发写入**：
  - 代码在当前读取 chunk 中寻找末尾换行：`const complete = chunk.lastIndexOf(10) + 1`。
  - 若 chunk 不包含换行（`complete === 0`），直接跳过本次复制，`start` 偏移保持不变，等待下一轮扫掠补全；若末尾有未完成的半行，仅压缩截取至最后一个 `\n` 的完整行部分。
  - ASCII 换行符 `10`（`\n`）在 UTF-8 编码下具有单字节唯一性（UTF-8 多字节序列后续字节最高位必为 `10xxxxxx`，数值不可能为 10），因此绝不会切断多字节 UTF-8 字符。
- **gzip 成员追加（RFC 1952 Concatenated Members）**：
  - 每一段完整行独立经 `gzipSync` 压缩成单独的 gzip 成员，通过 `appendFileSync` 追加至目标 `.gz`。
  - Python 标准库 `gzip.decompress()` 以及标准工具（`gzip -dc`, `zcat`）能天然且正确地将多成员流拼接解压为单连续文本。测试中通过 4 段追加验证解压结果与原生文件完全一致。
- **多来源隔离**：
  - 对单个 launch 下的多个文件（如 Codex 的主/副 rollout），以 `basename(source.path) + '.gz'` 分别建文件，按各自的 `source` 路径在数据库中追踪独立的 `(start, end)`。

### 2. 来源定位与权限边界

- **未批准角色的终端绝对受保护**：
  - 后台启动的 `launch_records` 中，普通终端在创建时角色为 `shell`，代码显式检查 `if (record.role === 'shell') continue;`（行 174），彻底排除普通终端。
  - 终端主控（行 186–196）仅扫描 `orchestration_events` 中已被用户批准的请求（`data.approved === true`）。未申请、申请中未决、被用户拒绝的终端，都不会进入 `sources`。
- **防路径穿越与越界文件读取**：
  - `claudeTranscript` 仅在 `home/projects/*/` 下定位，且 `session` 取自角色申请（在 `roleRequests.ts` 已被正则 `/^[0-9A-Za-z][0-9A-Za-z-]{7,63}$/` 限制），不含 `..` 或路径分隔符；
  - `codexRollout` 仅在 `home/sessions/YYYY/MM/DD/` 下查找。无法利用虚假路径越界读取系统敏感文件。

### 3. 后台接线与运行机制（[`daemon.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts)）

- **Stop 后归档与定时归档的互斥性**：
  - `TrajectoryArchive.sweep()` 全程采用 Node.js 同步 API（`openSync`, `readSync`, `fstatSync`, `appendFileSync`, `db.prepare().run()`），没有哪怕一个 `await` 或异步让出事件循环的操作。
  - 在 Node.js 单线程事件循环模型下，Stop 钩子触发的 `archiveSweep(launch)` 与 30 秒定时器的 `archiveSweep()` 必定串行独占执行，不存在线程并发或协程交错写同一个归档文件的竞态条件。
- **出错记录与静默风险**：
  - `archiveSweep` 在顶层捕获了异常并追加 `trajectory_archive_failed` 事件，不会吞掉错误导致无痕迹。
  - 但注意：`sweep()` 内部对单个 source 缺少局部异常隔离（见下文发现项 1）。
- **只读命令不污染状态**：
  - 命令 `trajectory_archive` 已被加入 `readOnly` 校验集。
  - 处理函数 `archive.usage()` 仅调用 `SELECT count(DISTINCT launch)` 和文件系统 `statSync`，不写数据库，不追加事件；`trajectory_archive` 表上亦配置了防 UPDATE/DELETE 的 SQLite 触发器。

### 4. 设置页占用与实际一致性

- 后端 `archive.usage()` 递归遍历并累加 `data/archive` 下所有文件的物理大小（行 260–261）。
- 前端在设置对话框打开时通过 IPC 调用 `window.a2a.archiveUsage()`，展示会话数与格式化大小，读取失败时有明确的 `role="alert"` 报错，不会静默归零。
- 端到端测试由真实 Electron 实例打开设置对话框，提取 DOM 数据属性 `data-archive-bytes`，断言其与夹具磁盘文件大小完全相等（`61529 === 61529`），并留下截图证据。

### 5. 测试期望独立性与变异有效性

- **期望独立性**：
  - 测试断言未采用实现代码的自身输出；
  - 期望内容取自测试自己向终端键入的 `TYPED` 字符串、原生文件读取的原文字节切片、主动注入的半行与补齐内容，以及由 Python 遍历磁盘文件独立的 `st_size` 累加和。
- **变异与已知坏实现有效性**：
  - `red-parent`（`e4d45c511`）：超时失败（退出码 1）；
  - `mutant-partial-line-copied`（不截取换行）：精准捕获于 `half_line_not_archived`（退出码 1）；
  - `mutant-not-incremental`（每次从 0 开始）：精准捕获于 `second_turn_continues_first`（退出码 1）；
  - 回归测试 `test_t122_claude_worker_e2e.py` 全绿通过（退出码 0）。

---

## 发现项清单

### 发现 1 (P2 - 重要): `sweep()` 遍历源文件时缺少单会话异常隔离

- **文件与行号**：[`workbench/src/trajectoryArchive.ts#L221-L254`](file:///Users/luckye/Documents/Code/a2a/workbench/src/trajectoryArchive.ts#L221-L254)
- **严重度**：P2
- **失败场景**：
  在后台每 30 秒执行的全局全量扫描 `archiveSweep()`（未指定 `launch`）中，循环遍历 `this.sources()` 的所有会话。若其中某一个历史会话的源文件发生权限异常（EACCES）、文件损坏或在 `existsSync` 与 `openSync` 之间被并发清理导致 `ENOENT`，抛出的异常会直接打断 `sweep()` 的整个 `for` 循环，导致排在该异常 source 之后的所有其他正常活跃会话在此轮定时归档中被全部饿死。只要该坏文件持续存在，全局周期性增量归档将一直处于阻断状态。
- **整改建议**：
  在 `for (const source of this.sources(launch))` 循环体内增加局部 `try ... catch`，单个 source 处理失败时上报该 source 的失败事件后 `continue` 继续处理下一会话，保证会话之间的故障隔离。

---

### 发现 2 (P3 - 轻微/性能): 历史 Codex 终端主控记录失效后无上限的文件系统遍历

- **文件与行号**：[`workbench/src/trajectoryArchive.ts#L210-L217`](file:///Users/luckye/Documents/Code/a2a/workbench/src/trajectoryArchive.ts#L210-L217)
- **严重度**：P3
- **失败场景**：
  对于历史已批准的 Codex 终端主控，当原生 CLI 的 30 天自动清理机制将原文件删除后，每次 30 秒周期扫描时，`codexRollout` 会从 `request.time` 开始逐日直到当前日期（例如 60 天以上）对每个日期目录执行 `existsSync` 与 `readdirSync`。随着使用时间累积，已过期的历史会话将造成无意义的周期性磁盘 I/O 放大。
- **整改建议**：
  可在定位到文件或确认文件已被清理后记录终态，避免长期盲扫历史日历目录。

---

### 发现 3 (P3 - 轻微/健壮性): 磁盘 gzip 追加与数据库索引插入非原子

- **文件与行号**：[`workbench/src/trajectoryArchive.ts#L250-L253`](file:///Users/luckye/Documents/Code/a2a/workbench/src/trajectoryArchive.ts#L250-L253)
- **严重度**：P3
- **失败场景**：
  先执行 `appendFileSync(file, member)`，后执行 `this.db.prepare('INSERT INTO trajectory_archive...').run()`。若在两者之间发生断电/进程被 SIGKILL，或 SQLite 因磁盘已满抛出异常，会导致 `.gz` 文件已物理追加新成员，但 DB 中没有记录推进后的 `end`。下一次 `sweep` 重试时，会从旧的 `start` 重新读取并再次压缩追加，造成归档解压后出现重复内容。

---

### 发现 4 (P3 - 轻微/性能): `trajectory_archive` 表缺少查询索引

- **文件与行号**：[`workbench/src/trajectoryArchive.ts#L162-L165, L223`](file:///Users/luckye/Documents/Code/a2a/workbench/src/trajectoryArchive.ts#L162-L165)
- **严重度**：P3
- **失败场景**：
  建表语句仅定义了主键 `seq`，而每次获取起点均运行 `SELECT max(end) FROM trajectory_archive WHERE launch=? AND source=?`。随着归档轮次增长，每次查询都需要全表扫描。
- **整改建议**：
  建表时补充 `CREATE INDEX IF NOT EXISTS trajectory_archive_lookup ON trajectory_archive(launch, source);`。

---

### 发现 5 (P3 - 轻微/整洁度): `sources()` 对多次批准的终端主控可能产生重复项

- **文件与行号**：[`workbench/src/trajectoryArchive.ts#L186-L196`](file:///Users/luckye/Documents/Code/a2a/workbench/src/trajectoryArchive.ts#L186-L196)
- **严重度**：P3
- **失败场景**：
  若同一个终端发生过多次角色申请与批准，`sources()` 可能会将同一文件重复压入数组。虽然第二遍运行时由于 `size === start` 会被提前跳过，但多走了一次无意义的文件打开与 DB 查询。

---

## 总体审查结论

# **PASS**

**判定理由**：
1. **验收条件完全满足**：Ticket T-135 所定义的全部验收项（真实的 Claude worker 2 回合增量归档、末行不完整行延迟归档、设置页与磁盘占用完全一致）均已实现且通过真实环境测试；
2. **证据闭环且独立**：拥有修前父版本的红态失败证据（`red-parent`）、两个针对关键设计点的有效代码变异反例（`partial-line-copied` 与 `not-incremental`），以及已有套件的无回归证据（`t122-green`）；
3. **架构安全合规**：增量分段使用 RFC 1952 规范的多成员 gzip，偏移与断行计算严谨；严格隔离非受管终端；命令与后台接线无并发踩踏隐患。
4. 发现的 P2（单 source 异常隔离）及 P3 项为系统健壮性与后续维护优化点，不构成阻塞主线交付的硬伤，建议在后续批次中针对 P2 补充单 source 的 `try-catch` 保护。
