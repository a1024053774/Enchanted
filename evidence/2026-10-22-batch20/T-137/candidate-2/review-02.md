# T-137 复审 02 报告：Reflect 页、复盘移入与定期复盘默认关闭

本审查为只读独立复审，依据 [`review-01.md`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/review-01.md)、[`full.diff`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/full.diff)、[`candidate-2.diff`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/candidate-2.diff)、[`candidate-2-RESULTS.md`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/candidate-2-RESULTS.md)、[`green-02.json`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/green-02.json) 与 [`exits-02.txt`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/exits-02.txt) 完成。

---

## 一、`review-01` 发现的处理与成立性核对

### 1. 【Finding 1】“关系不明进未归属”无测试断言与夹具覆盖（原 P2）
- **核对结果**：**已按说明闭环**。
- **事实依据**：
  1. [`test_t137_reflect_e2e.py`#L266-L267](file:///private/tmp/a2a-t133-c1/workbench/tests/test_t137_reflect_e2e.py#L266-L267) 在夹具中增加 `T-3` 任务，由操作员身份派发（`fixture.operator`），未附加主控终端，其 `parent_launch` 为空；
  2. [`test_t137_reflect_e2e.py`#L306-L307](file:///private/tmp/a2a-t133-c1/workbench/tests/test_t137_reflect_e2e.py#L306-L307) 通过选择器 `document.querySelectorAll('.reflect-loose .reflect-node')` 抓取未归属节点；
  3. [`test_t137_reflect_e2e.py`#L319](file:///private/tmp/a2a-t133-c1/workbench/tests/test_t137_reflect_e2e.py#L319) 增加新检查 `session_without_controller_unassigned`，严格断言 `by[workers['T-3']]['parent'] == ''` 且 `loose == [workers['T-3']]`；
  4. [`green-02.json`#L167-L169](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/green-02.json#L167-L169) 记录 `loose` 数组确切包含且仅包含 `T-3` 的 launch ID。

### 2. 【Finding 2】“已有设置不改写”未提供存量升级测试证据（原 P2）
- **核对结果**：**已按说明闭环**。
- **事实依据**：
  1. [`test_t137_reflect_e2e.py`#L356-L368](file:///private/tmp/a2a-t133-c1/workbench/tests/test_t137_reflect_e2e.py#L356-L368) 在测试末尾增加了后台重启测试链路：`daemon_stop` → 等待 socket 释放 → 备份凭据 → 携既有数据目录 `daemon_start` → 重新认证并等待恢复；
  2. 增加检查 `saved_schedule_survives_restart`，断言重启后读取的配置 `kept['enabled'] is True` 且 `kept['model'] == MODEL`，未被出厂默认值覆盖；
  3. 增加变异 `defaults-overwrite-saved`（见 [`candidate-2.diff`#L141-L143](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/candidate-2.diff#L141-L143)），将构造函数中的空表判断置空从而每次启动均无条件写默认值；该变异在 [`exits-02.txt`#L3](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/exits-02.txt#L3) 退出码为 1，精确失败在 `saved_schedule_survives_restart`。

### 3. 【Finding 3】同一毫秒交接优先归属给已结束角色（原 P3）
- **核对结果**：**已按说明处理（代码落位）**。
- **事实依据**：
  [`reflect.ts`#L35](file:///private/tmp/a2a-t133-c1/workbench/src/reflect.ts#L35) 将 `roleAt` 从 `held.find(...)` 改为 `held.findLast(...)`。由于 `held` 是按事件确认时间顺序正序追加，若 R1 在时间点 $T$ 结束而 R2 在时间点 $T$ 生效，在 `time === T` 启动的会话经由 `findLast` 从末尾逆序遍历，优先匹配到最新生效的 R2。候选说明中如实记录“同一毫秒的极限边界未构造夹具”，作为低概率极值边界，代码逻辑已完备。

### 4. 【Finding 4】监视器（monitor）角色未在端到端用例中实际派发（原 P3）
- **核对结果**：**已按说明闭环**。
- **事实依据**：
  1. [`scripted_claude.py`#L67](file:///private/tmp/a2a-t133-c1/workbench/tests/scripted_claude.py#L67) 补全了 `monitor_role_card` 的启动配置；
  2. [`test_t137_reflect_e2e.py`#L272](file:///private/tmp/a2a-t133-c1/workbench/tests/test_t137_reflect_e2e.py#L272) 通过执行主控显式为 `T-2` 挂载 `monitor`；
  3. [`test_t137_reflect_e2e.py`#L313](file:///private/tmp/a2a-t133-c1/workbench/tests/test_t137_reflect_e2e.py#L313) 在检查 `sessions_under_the_role_held_when_they_started` 中增加了监视器的断言：`len(monitors) == 1 and monitors[0]['parent'] == e2 and monitors[0]['level'] == '2'`；
  4. [`green-02.json`#L131-L135](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/green-02.json#L131-L135) 证实监视器节点已正常生成并在第二层渲染。

### 5. 【Finding 5】RetrospectiveSections 中 version 状态未加入 useEffect 依赖（原 P3）
- **核对结果**：**复核确认原 Finding 5 不成立，候选不修改的理由成立**。
- **事实依据**：
  核对 [`full.diff`#L183-L184](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/full.diff#L183-L184) 及原代码文件 [`RetrospectiveSections.tsx`#L34](file:///private/tmp/a2a-t133-c1/workbench/app/RetrospectiveSections.tsx#L34)：
  ```typescript
  32:     const timer = setInterval(load, 5000);
  33:     return () => { mounted = false; clearInterval(timer); };
  34:   }, [project, version]);
  ```
  在 `full.diff` 中，因 `@@ -11,19 +11,22 @@` 与 `@@ -34,13 +37,12 @@` 两段 diff hunk 之间恰好折叠了未修改的第 30-33 行（原文件行号），第 34 行的 `}, [project, version]);` 始终存在。`review-01` 误将 diff hunk 折叠处当作依赖缺失。候选处理说明指出的“不成立：依赖是 [project, version]，原页面同样”完全属实。

---

## 二、本轮改动新引入问题核查

对 [`candidate-2.diff`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/candidate-2.diff) 与现有运行环境进行深度检查：
1. **API 与兼容性**：[`reflect.ts`#L35](file:///private/tmp/a2a-t133-c1/workbench/src/reflect.ts#L35) 使用的 `Array.prototype.findLast` 在 Node.js 18+ 原生支持，测试执行无 runtime 异常；
2. **测试资源与进程回收**：`test_t137_reflect_e2e.py` 重启后台时显式重命名凭据文件并在 `finally` 块中通过 `fixture.stop()` 和 `electron.stop()` 兜底清理，无进程孤儿与 socket 泄露；
3. **未引入新问题**：未引入任何 P0–P2 缺陷。

---

## 三、新检查与新变异核查

### 1. 新检查 `session_without_controller_unassigned`
- **独立性**：断言期望（`parent === ''` 且唯一归入 `.reflect-loose`）直接来源于 ticket 票面条款（“关系不明的进‘未归属’”），不依赖实现代码内部逻辑。
- **抓缺陷能力**：若未归属节点被丢弃、误挂到主控下、或 DOM 未单独分组，该检查立即断言失败。

### 2. 新检查 `saved_schedule_survives_restart` 与新变异 `defaults-overwrite-saved`
- **独立性**：跨进程重启后验证之前保存的 `model: 'claude-haiku-5-5'` 与 `effort: 'low'` 是否保留，不使用默认出厂配置，具备明确的黑盒独立性。
- **抓缺陷能力**：
  - 真实代码在 [`retrospective.ts`#L37-L38](file:///private/tmp/a2a-t133-c1/workbench/src/retrospective.ts#L37-L38) 仅在 `SELECT 1 FROM retrospective_schedule LIMIT 1` 为空时写一次默认值；
  - 变异 `defaults-overwrite-saved` 篡改判断体，使得每次启动均无条件写入默认配置；
  - 该变异在 [`exits-02.txt`#L3](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/exits-02.txt#L3) 准确退出 1，且精确由 `saved_schedule_survives_restart` 捕获。变异与检查有效匹配。

---

## 四、复审发现列表（Findings）

### 1. 【已知极值边界】同一毫秒交接未构造精确微秒碰撞夹具
- **文件与行号**：[`reflect.ts`#L35](file:///private/tmp/a2a-t133-c1/workbench/src/reflect.ts#L35)
- **严重度**：**P3**
- **失败场景**：
  代码已将 `held.find` 规整为 `held.findLast`，能够保证逆序优先匹配最新角色。但端到端夹具中两次角色变更之间存在真实时间间隔，未通过时钟 Mock 注入“结束与生效时间戳完全相同到同一毫秒”的合成数据。鉴于实际生产中角色交接由两次顺序 socket 消息驱动、同毫秒并存概率极低，且当前代码逻辑严谨，本项作为已知极限边界记录，不阻碍发布。

---

## 五、总体结论

### **PASS**

**理由**：
1. **前轮缺口全数闭环**：`review-01` 指出的两条阻碍性 P2 发现（未归属分支缺少覆盖、存量设置保留缺少证据）均已补充端到端真实场景与断言；P3 监视器用例已覆盖；P3 毫秒归属已由 `findLast` 纠正；P3 `version` 依赖经确证属于上轮审查对 diff 折叠的误判，原代码无缺陷。
2. **端到端证据链完整且可复现**：`green-02.json` 覆盖全部 10 项端到端检查（包含 `session_without_controller_unassigned` 与 `saved_schedule_survives_restart`），`exits-02.txt` 证明父提交红态（exit=1）、5 个独立变异（含新变异 `defaults-overwrite-saved`，全部 exit=1）及既有测试 `t136-green`（exit=0）全部真实有效。
3. **无新缺陷**：本轮累计改动代码精炼，符合根因最小改动原则，完全满足 T-137 验收条件。
