# 独立审查报告：T-130 候选 1（提交 `566e54b57` 与 README 补充 `619bb849`）

本报告由独立审查者以只读方式生成，审查对象为提交 [`566e54b57`](file:///Users/luckye/Documents/Code/a2a)（父提交 `04354734b`）与补充提交 [`619bb849`](file:///Users/luckye/Documents/Code/a2a)，对比差异位于 `/private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/agy-t130-tX2U/full.diff`，验证证据基于 [`RESULTS.md`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-130/candidate-1/RESULTS.md)。

---

## 一、重点审查分析

### 1. 钩子逻辑正确性（[`workbench/hooks/hook.py`](file:///Users/luckye/Documents/Code/a2a/workbench/hooks/hook.py#L106-L177) `claude_turn_facts`）

- **会话记录定位与越界防护**：
  - 配置目录使用 `env.get('CLAUDE_CONFIG_DIR') or (Path(env['HOME']) / '.claude')`，优先支持隔离沙箱注入的环境变量，默认回退安全。
  - Glob 搜索限定为 `projects.glob('*/' + native + '.jsonl')`，仅在项目子目录下一级匹配会话文件。
  - 严格核验匹配唯一性：`len(files) == 1`；当无匹配或有多重同名会话时，安全回退 `('unknown', 'unknown')`。
  - 路径边界防御：核查 `projects not in files[0].resolve().parents`，通过 `resolve()` 展开符号链接，杜绝跨目录逃逸或路径遍历攻击。
- **会话号核对**：
  - 逐行扫描 JSONL 中的 `assistant` 记录时，执行 `record.get('sessionId') == native` 强校验；若发现跨会话记录或会话 ID 错乱，立即抛出 `ValueError` 中止。
- **半行与 `<synthetic>` 截断处理**：
  - 严谨处理并发未刷盘：`if not line.endswith('\n'): break`。遇到不完整的半行立即停止扫描并安全采纳此前最新事实，避免 `json.loads` 解析崩溃。
  - 过滤内部合成消息：显式跳过 `model == '<synthetic>'`（针对错误/取消等合成事件），继续回溯直至提取上一次真实的模型调用事实。
- **两种思考强度字段（`effort` 与 `perTurnEffort`）的合并**：
  - 逻辑为收集非空值集合 `{value for value in (latest.get('effort'), latest.get('perTurnEffort')) if value}`。
  - 单字段存在、双字段一致时均能正确提取；若双字段出现互斥冲突值，直接触发 `ValueError` 阻断提交；均缺省时稳妥回退 `'unknown'`。
- **Fail-Closed 故障安全设计**：
  - 在 [`hook.py:209-211`](file:///Users/luckye/Documents/Code/a2a/workbench/hooks/hook.py#L209-L211) 中捕获 `(OSError, KeyError, ValueError, CalledProcessError)`，向 stderr 打印告警并调用 `sys.exit(1)`。
  - 作为 Git 的 `prepare-commit-msg` 钩子，退出码 1 保证 Git 立即放弃本次提交，绝不写入空、错乱或伪造的尾注。
- **Codex 分支隔离**：
  - 钩子以 `home = env.get('CODEX_HOME')` 作为分流判断。在受管工作台环境中，Codex 会话由 [`workbench/src/panes/panes.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/panes/panes.ts#L619) 显式注入独立 `CODEX_HOME`，因此完全走原有的 Codex 分支，对 Codex 会话零侵入、零污染。
- **沙箱与权限安全性**：
  - Git commit 在子进程/钩子环境中触发，对配置目录的访问仅以只读方式读取对应会话的 `*.jsonl` 文件。实测证据（`user-config-compare.txt`）证明比对前后用户 `~/.claude` 配置完全一致，无任何副作用或信息泄露。

### 2. 与门禁 `trailer_check` 的配合（[`workbench/src/gates/core.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L2193-L2198)）

- **尾注事实与交付记录（Stop 事实）的一致性**：
  - 受管 worker 启动时已由启动参数绑定 `--model` 与 `--effort`。Git commit 时钩子记录当时观察到的模型事实；Stop 钩子触发时由 [`claudeTurnFacts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/panes/panes.ts#L309) 解析相同事实并更新至 `pane.model` 与 `pane.effort`，供 `submit` 生成交付凭据。
  - 若在会话过程中发生非授权模型漂移或切换，导致提交尾注与 Stop 事实分歧，门禁 `trailer_check` 判定 `trailer_identity_mismatch` 并拒收交付，这符合门禁对溯源一致性的强契约要求。
- **门禁对 `unknown` 宽容度的合理性**：
  - 在 `workbench/src/gates/core.ts` 中，`trailers.model !== "unknown"` 但允许 `trailers.effort === "unknown"`（当 provider 为 claude 且 transcript 未输出 effort 时）。
  - 此设计是合理的：部分 Claude Code 上游或兼容转接层不输出 reasoning_effort 属性；且在 `submit` 业务入口（[`core.ts:3964`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L3964)）处，门禁对交付记录本身另有非空强校验，不会发生伪造交付逃逸。

### 3. 测试完备性与证据真伪（[`RESULTS.md`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-130/candidate-1/RESULTS.md)）

- **单测独立性（[`test_t130_hook_claude_facts.py`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t130_hook_claude_facts.py)）**：
  - 单测使用预先构造的测试输入与环境变量，独立验证常规多轮、半行未刷盘、`<synthetic>` 穿透、双字段冲突、跨项目路径越界等 10 种边界用例。
  - 变异测试（Mutants 1~9）及父提交对比中，针对包括“去除半行检查”、“删除 `<synthetic>` 过滤”、“忽略 effort 冲突”、“放宽边界检查”在内的变异体均准确识别并产生 exit=1 失败，证明测试具备充分的坏实现辨别力。
- **端到端测试（[`test_t122_claude_worker_e2e.py`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t122_claude_worker_e2e.py)）**：
  - E2E 测试基于真实 mock 终端服务注入 `claude-haiku-5-5-t122-served`，断言提交尾注真实携带了观察到的实际模型名称与 effort；父提交在该用例上明确重现 `AssertionError` 红态，本候选成功转绿。
- **报告真实性**：
  - `RESULTS.md` 所引用的各个退出码、日志、UI 回读及配置文件比对证据文件均真实存在且与执行输出一致，没有夸大或伪造事实。

### 4. 其他检查项

- **文档更新**：[`workbench/README.md`](file:///Users/luckye/Documents/Code/a2a/workbench/README.md#L68) 中的架构与使用说明同步更新了 Claude Code 会话尾注钩子行为，与代码实际行为保持一致。

---

## 二、审查发现明细

| 严重度 | 文件与行号 | 失败场景 | 建议 |
| :--- | :--- | :--- | :--- |
| **无** | - | **无发现**（未发现 P0 / P1 / P2 / P3 缺陷） | 保持当前实现 |

*(经过全面审查与推演，`workbench/hooks/hook.py`、`workbench/src/gates/core.ts` 及相关测试设计完备、边界严谨、防御充分，无阻断性或功能性缺陷。)*

---

## 三、总体审查结论

**PASS**
