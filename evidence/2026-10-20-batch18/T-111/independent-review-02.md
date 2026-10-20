# T-111 第二轮独立审查

结论：**INCOMPLETE**。第一轮 F1 的合同缺口已由本轮独立反事实验证为修好；在已查范围内未发现新的可确认产品缺陷。真实 Electron 和第三个写库变异的新一轮独立执行尚未运行，不能把局部通过提升为完整复验通过。主控提供的 outside-03 原件支持当前候选的真实入口行为，来源及限制列在下文。

## 范围与版本

- 仓库：`/Users/luckye/Documents/Code/a2a-wt-t111`，`exec/t111`。
- 冻结候选：`5b060015b26e241c7a3ceb16384aab1669bac000`；起点：`b1ecd6e9cba23c1bbddb331822b6500a1488e2e9`。结束时 HEAD 未变。
- 目标：核实 F1 修复及任务票要求的只读流程、阶段事实、归属、折叠、窄窗、IPC 和结构完整性。非目标：实现、修复、派发、门禁交付或集成、模型运行、全站上线审查。
- 验收依据从 T-111 用户逐字需求、票中完成条件及 T-109 Resolution 重建，未使用作者会话历史。参考图已直接读取。用户已撤销截图要求，缺少截图不作拒收理由。
- 使用 Ubiquitous language：阶段、打回、父 launch、任务和 attempt 均采用票与 CONTEXT 的含义。沿现有 Tracer bullet 检查 renderer → preload → main → daemon → 门禁事件／启动记录；以 Deep modules 检查是否另造门禁或恢复层。
- 只写本报告、新审查脚本及自己创建的 `/private/tmp` 目录；没有更改产品、测试、旧证据、全局配置或 Git 元数据；未开子 agent、未调用模型、未申请升级。

## 本轮独立执行

环境：Python **3.9.6**、Node **v26.5.0**。候选和变异均由 `git archive` 创建普通副本，没有创建 worktree 或符号链接。运行：

```sh
zsh evidence/2026-10-20-batch18/T-111/REVIEW-OUTSIDE-02.sh --local
```

最终 rc **0**，局部检查 PASS。完整命令、标准输出、错误及 JSON 原件保留在：

`/private/tmp/t111-review-02-sigsr09k/summary.json`

| 检查 | 实际结果 | 能证明的内容 |
| --- | --- | --- |
| candidate-contract | rc 0，PASS | 当前合同接受好候选 |
| candidate-ipc | rc 0，PASS | 实际 main/preload 的 IPC 合同；供应的 Electron／transport 边界不证明 GUI 或 daemon |
| candidate-two-returns | rc 0，PASS | 本审查另写的票号与双打回输入；跨 attempt 来源为 checks/review；去除打回事件后为 0；追加 count=999 的单个事实只增加一次；改标题不改变打回事实 |
| count-mutant-existing-contract | rc 1，按预期拒绝 | `.slice(0, 1)` 在累计业务断言处失败：`Ticket rejection facts must accumulate across attempts`，`1 !== 3` |
| count-mutant-independent-probe | rc 1，按预期拒绝 | 独立双打回预期失败：`Two gate rejection facts must remain two returns`，`1 !== 2` |
| missing-attempt-mutant | rc 1，按预期拒绝 | 移除非空 attempt 前提，在 `Missing attempt binding must stay unassigned` 失败：`1 !== 0` |

两个已执行变异均为 `flow.ts` 的单处错误；先确认好候选通过，再执行变异。错误来自业务断言，未把缺依赖、导入或启动失败当作拒绝。变异报告内部的 `status: INCOMPLETE` 是测试脚本统一的失败标签；上述判定另外核对了 rc、断言文字和实际／预期值。

首次自写探针把 `review_result` 放在 `delivery_rejected` 之后，却期望最后阶段为实现，导致 rc 1。门禁实际顺序是先审查结果、后打回（`core.ts:3579`）；该失败是审查夹具错误，非产品红态。仅修正探针事件顺序，再用全新目录运行。首次现场完整保留在 `/private/tmp/t111-review-02-5nq9y300`，未覆盖。

## 必审项目

### (0) F1：PASS（本轮独立局部验证）

`test_t111_flow.mjs:50` 起输入旧 attempt 一次机械打回、当前 attempt 两次审查打回。64 行独立断言总数 **3**，65 行断言来源 **checks/review/review**；67–69 行移除旧 attempt 后断言 **2** 且均为 review；70–73 行分别移除 `review_result` 和 `delivery_rejected`，断言附属审查结果既不增加也不减少打回事实。

预期没有从 `projectFlow` 常量或产出中生成。产品 `flow.ts:16` 只数 `delivery_rejected`，来源按 `repair.check` 区分；没有累加 attempt 内的 `repair.count`。门禁 `core.ts:2081` 的 `rejectDelivery` 对同一 verification 去重后追加一次规范打回，`core.ts:3579` 先保存审查结果，再调用打回，因此这两个事件不能重复计数。

新合同确实拒绝第一轮原样截断变异。本轮独立双打回及输入变形也通过好候选、拒绝截断。`git diff 43717b803 5b060015b -- workbench/src workbench/app` 为空；修复没有修改产品。测试 diff 保留旧单次打回断言和其他场景，新增多次累计、来源、实际 DOM 标签／文本／可见线和实际 IPC 断言，没有删减其他业务检查。

### (1) 只读：源码检查 PASS；新独立真实复验 INCOMPLETE

`FlowPage.tsx:56` 唯一远程读取为 `window.a2a.flow()`；其按钮只修改本地页面、泳道和人数展开状态。`main.ts:143` 校验当前顶层窗口后只发送 `flow_snapshot`，不携带 operator 或窗格输入凭据。`daemon.ts:84` 把该命令列入 catalog 读取，避免记录读取请求；`flow.ts:49` 复用 sidebar 已保存事实并 SELECT tasks/events，没有写库或调用 scan。

`workbench/src/gates/`、`sidebar.ts`、`panes.ts`、`transport.ts` 相对起点没有改动。未新增派发、状态修改或另一条门禁路径。提供的 outside-03 精确原值比较通过；本轮新执行的边界复验尚待运行。

### (2) 阶段和打回：PASS（源码、合同与独立输入）

`flow.ts:18–35` 仅遍历当前 attempt 的门禁事件推进阶段；任务行提供身份，不提供推测阶段。旧 attempt 的 integrated 不推进当前阶段；普通 rejected 不算打回。累计打回在筛选当前 attempt 之前按该票所有规范打回事件统计，符合跨 attempt 事实累计；review_result 自身不算打回。未知或冲突事件状态没有被补成成功。

### (3) agent 归属：PASS（源码与局部合同）；真实 UI 使用主控原件

`flowSnapshot` 使用 `sidebarSnapshot` 的 agent，后者先核对实际父记录、同项目、角色允许关系和环路；缺失父项或冲突归属先清为 null。`flow.ts:37–40` 再要求非空当前 attempt、项目、票号、attempt、已校验父关系、允许角色及非 ended 状态。两个 undefined 无法通过该前提，独立单处变异已证明合同能拒绝。

该页没有读取窗格标题推断角色、父关系或任务，也没有重建第二套层级。worker/reviewer 分别放实现／审查列，monitor 放泳道上方；不能核对归属的非 ended 会话进入“未归属”。T-109 的启动和父关系保存路径未改。

### (4) 折叠与窄窗：源码检查 PASS；真实结果来源为主控

`FlowPage.tsx:11–18` 首屏最多四个胶囊，剩余显示准确 N，可展开并收起；21–25 行让初始已集成泳道默认折叠。39–44 行保持五个固定阶段；`flow.css:10–15` 以横向滚动容器及 1150px／230px 最小布局保留列宽。空状态有专门文案。

主控 `electron-outside-03.json` 报告两票、五人折叠展开、已集成票折叠展开、900px 横滚且 body 不溢出、空状态通过；本轮没有亲自启动 Electron，不能把这段称作本轮 UI 操作结果。

### (5) 参考图：结构说明属实；本轮未做实际像素对照

直接读取了原始参考图：横向空心节点、细线、›››、阶段名、竖排圆角胶囊、左侧彩色标记、人数折叠和折回线。`FlowPage.tsx` 与 `flow.css` 对应实现了这些结构，RESULTS 的对齐描述属实。

有意差异也在源码中成立：深色主题、实际五个门禁阶段、多票上下泳道、票号／项目／attempt／状态附文、记录号代替不存在的展示名、monitor 在上方、同源打回合并并标次数。参考图密度更低，实际胶囊有多行身份和状态文字；不能据源码断言像素密度相同。RESULTS 本身已把该对照限定为设计／源码结构，没有谎称真实截图通过。依用户要求不保存截图。

### (6) IPC 与 T-107 F2/F3：局部 IPC PASS；新真实边界复验 INCOMPLETE

新增一个受窗口校验约束的只读接口，返回的是同一个本地后台已有任务／agent 范围；没有接受任意 SQL、路径、命令或新增输入凭据。renderer 以 React 文本节点展示字符串，没有新增 HTML 注入入口。未发现新增的可确认权限漏洞。

IPC diff 把 flow 加入所有相关 contract 分支，原有拒绝与变异继续执行。本轮结果含 21 handler／22 bridge 精确名单、iframe／未知窗口拒绝、外任务和旧 launch 拒绝、历史只读 view 不发输入凭据、通知边沿、关闭与空布局反例；旧检查未被跳过。

T-107 daemon 测试只增加 flow 模式和私有 helper 准备，既有 SQLite 全表／schema／trace 原值比较、未消费 native bytes 的 offsets 断言均保留。持久化 oracle 独立遍历所有表及 trace 原始字节，不比较 hash，也不从产品返回值生成预期。新增读取路径不调用 collector。主控 outside-03 中真实 flow 读取及 flow-write-mutant 已通过；本轮脚本另明确保留 sidebar readonly 正例和一次 store.event 的反例，待执行。

### (7) design-integrity-review：PASS（已查结构范围）

按技能将本候选的验收面交由 behavioral-acceptance-review 主导，同时追踪结构风险。scanner 在当前树报告 findings 为空；它只定位未提交变更，不足以证明候选，所以另外读取了完整起点差异及直接调用链。

未新增吞异常后报成功、兼容双路、写入镜像或独立门禁。新增 catch 属于页面读取错误展示，明确提示读取失败及保留上次记录；定时刷新串行等待请求完成，卸载后停止调度。这是 UI 读取失败的归属层，未掩盖成成功。新模块把读取和投影集中，未发现绕开事实所有者的浅包装或结构捷径。

## 外部原件与仍待运行部分

本轮直接读取了现存 `contract-outside-03.json`、`counterfactuals-outside-03.json`、`daemon-outside-03.json` 和 `electron-outside-03.json`。这些是**主控执行证据**，不是本 reviewer 的独立运行。Electron 原件明确绑定完整候选、source_changes 为空、rc 对应 PASS、cleanup_complete 为 true，实际总数 **3**、来源 **checks/review/review**、两条线计数 **1/2**。反事实原件包含 baseline、missing-parent、old-attempt、ignore-events、truncate-returns、flow-write-mutant 的业务拒绝。RESULTS 中“尚待运行”是主控运行前的作者记录，不能用它否定后来原件，也不能把旧 outside-02 当成新证据。

新增 `REVIEW-OUTSIDE-02.sh` 已固定当前完整候选，保留旧脚本不变。默认模式在新的 /private/tmp 归档副本运行：

```sh
zsh /Users/luckye/Documents/Code/a2a-wt-t111/evidence/2026-10-20-batch18/T-111/REVIEW-OUTSIDE-02.sh
```

默认模式先复跑局部检查，再跑实际 flow/sidebar daemon 正例、第三个单处 `store.event` 写库变异，最后跑好候选真实 Electron 和同一 Electron 完成条件拒绝截断变异。拒绝必须同时匹配业务断言与完整清理，不能只看非零 rc。Electron 截断预期是 `Ticket header must display all three rejection facts`；写库预期是 `Sidebar read changed persisted tables or traces`。所有结果留在新的 /private/tmp/t111-review-02-*，不覆盖原件。

脚本清除 Git 路由和模型环境变量、设 LC_ALL=C 与 GIT_OPTIONAL_LOCKS=0，限制 Python 3.9；Electron 使用内置盘 43.4.1 dist；依赖为普通复制，helper chmod 只由原测试作用于私有 runtime。归档没有 .git，仅在私有 runner 中把 Git 版本标注固定为归档版本、baseline archive 查询指向原仓库只读；变异标成 mutation，不冒充干净候选。未替换产品响应、DOM 或业务断言。zsh 语法和 heredoc／runner 的 Python 3.9 语法已检查通过。默认模式本轮未执行，不预填它的结果。

地图 status 在开始和结束都是 **8 项既存缺失文件／链接，0 项 stale living docs**，涉及稀疏目录未含的 findings 和旧 grilling 文件。T-111 的“status 0 问题”未满足；未擅自修改地图或扩大写入范围。原始 status 已留在本轮工具记录，并保存结束输出到局部复验目录。

关闭本轮 INCOMPLETE 所需最小证据：执行主控运行上述新脚本，核对好候选通过、三类错误实现由指定业务断言拒绝及真实入口清理完成；并明确处置稀疏 status 的既存差异。当前没有新确认的 P1/P2/P3 修复项，不要求改产品。

T-111 REVIEW INCOMPLETE
