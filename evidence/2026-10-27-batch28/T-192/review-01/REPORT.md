# T-192 独立只读审查

**状态：NO_GO。结论：需修复。**

审查对象为 `/private/tmp/t192-review/change.diff`：基于仓库 HEAD `c76e2ab2a7dfd5fe0692ff9f1150ef586354a4d0` 的未提交改动及两个新增文件。审查期间用逐字比较确认：仓库的 `git diff -- workbench`、`TaskRecord.tsx` 和 `taskHistory.ts` 与给定补丁一致，没有 checkout、切分支或修改仓库。本文所有源码路径均相对于 `/Users/luckye/Documents/Code/a2a`，行号对应本候选。

验收依据为 T-192、T-189、U07/U08，以及本候选 README 明示的“关闭后不能重开”。目标是回收后可读任务卡、各 attempt 的检查与审查记录，关闭后状态正确，并保留正常派发与门禁语义。本次没有修复实现，没有操作用户或既有隔离后台。

## 问题

### F1 · P1：已关闭任务可以经 revoke/revise 重开

**位置：`workbench/src/gates/core.ts:3945`、`:3967`；新增关闭分支在 `:3973`，派发防线在 `:1565`。**

失败场景：任务已为 `closed`，`current_attempt=null`、`integration_intent=null`。执行 `{"command":"revoke","task":"beta+T-1","reason":"review probe"}`，或 `{"command":"revise","task":"beta+T-1","spec_rev":2}`，两者均成功，任务变回 `ready`。之后 claim/dispatch 的 `task.state !== "closed"` 检查不再阻止它。正常主控就能走到此路径，不需要伪造身份或并发。

根因是原 revoke/revise 分支只排除了 `accepted`，随后 `invalidate()` 无条件写回 `ready`。此外，`taskHistory.closed` 仍保留旧关闭事件，任务记录可能同时显示“待认领”和“已关闭”。这破坏了本次新增的终态契约。

证据：附录 A 使用生产 `A2AGates.call()`、生产状态保存与内存 SQLite，以现有 `green-close.json` 为输入，分别得到 `ok:true,state:"ready"`。仅操作锁替换为无副作用占位，因此这是 L1 状态流转证据，不冒充真实 socket 或并发测试。

最小修复：在能调用 `invalidate()` 的任务变更入口拒绝 `closed`；保留历史 attempt 清理和只读查询。复验 closed → revoke/revise → claim/dispatch 的组合，确认所有拒绝都不改变终态。

### F2 · P2：删除默认窗格后，没有任务级同步接替它

**位置：`workbench/app/main.ts:764`；关联 `:415`、`:608`、`:504`，`workbench/app/renderer.tsx:740`、`:946`、`:1128`。**

失败场景一：打开没有已存布局、没有当前 attempt 的 ready 任务，当前页产生 `paneKeys=[]`。后台随后成功 dispatch 新 worker。主进程 `selection()` 只返回已有 `context.panes`，不会读取新布局；渲染器定时读取 sidebar 和 selection 也不会创建窗格。原先负责调用 `a2a:snapshot`、发现默认 worker 的 `SessionPane` 已不存在，所以新 worker 不会出现在当前任务页。重新选择任务或点击侧栏会话才能看到。

失败场景二：同样停在零窗格 ready 任务页，主控执行 close。`TaskRecord` 自己的轮询会显示“已关闭”，但父页面 `task` 仍来自旧 `selectedTask`；底部门禁栏继续显示“待认领”。sidebar 更新不会更新 `selectedTask`，selection 也返回旧 `context.task`。

证据：源码控制流，加附录 C 对真实函数体的隔离执行。结果为初始 `panes:0,layout:null,names:{}`；后台换成有 attempt 的快照后，selection 仍返回空 paneKeys；重新 prepareSelection 才得到一个窗格。该探针模拟后台读接口，没有启动 Electron；状态栏矛盾为静态推理，未声称 UI 实测。

最小修复：在任务级读取和协调当前状态、实际可打开的会话及窗格集合，让零窗格视图也能观察变化，并将更新后的任务提供给门禁栏。不要以重新插入空终端来遮住历史页。复验“停在空记录页 → dispatch”和“停在 ready 页 → close”，无需额外导航即可得到正确画面。

### F3 · P2：按命令名过滤全部 verify 拒绝，隐藏独有故障原因

**位置：`workbench/src/gates/taskHistory.ts:17`、`:26`、`:36`。**

失败场景：submitted 任务执行 verify，在取得集成分支 G 时失败，例如工作分支引用不存在。`core.ts:1761` 在产生 verification_result 之前调用 integration；失败只产生 command 事件和 `rejected { input:{command:"verify"}, error:"git_failed", ... }`。整理器既不展示 command 事件，又直接丢弃这个 rejected。用户在任务页看不到验收为什么无法开始。

另一个实际写入形态是合并冲突：`core.ts:1833` 的 verification_result 直接以 v 为 details，即 `details.state="merge_failed"`，不是 `details.verification.state`；随后还有 verification_conflict 和 verify/merge_conflict 拒绝。当前整理结果只有“验收 · 未通过”，detail 为 null，冲突文件和 merge_conflict 原因均消失。这否定了“每个 verify 拒绝都已有验收和打回步骤表达”的注释假设。

证据：附录 B 分别输入上述事件形态；前者 steps 为空，后者只有一个 detail=null 的失败步骤。事件形态与 core 的真实写入分支逐项核对过。

最小修复：只去除已经被同一次 verification 的结构化步骤充分表达的重复拒绝，保留未被表达的错误；按现有写入格式识别 merge_failed/verification_conflict。不要通过统一过滤整个 verify 命令去重。复验验收前 Git 失败、合并冲突、正常检查失败三个不同路径。

### F4 · P2：真正执行的红态检查、规则检查不进入时间线

**位置：`workbench/src/gates/taskHistory.ts:34`、`:35`、`:49`。**

失败场景：任务卡包含 red_commands，项目配置包含 rule_checks；门禁执行后写入 `red_check` 和 `rule_check`。两个类型都命中 default，整条步骤被丢弃。反而“不适用”的两个事件有展示。成功任务会缺少实际执行过的质量检查，失败任务也无法从时间线查看对应检查的具体结果。

证据：`core.ts:2236` 写入 red_check，`:2244` 写入 rule_check；附录 B 使用相同结构的哨兵输入，输出 steps=[]。原 `history_check.ts` 的两个夹具只走“不适用”，因此其 PASS 无法覆盖此缺陷。

最小修复：在同一个整理器中映射 red_check、rule_check，保留检查编号或规则 id、通过状态及必要失败信息。复验至少一个真实红态检查和一个真实规则检查，包含失败输入；相应缺失事件的坏实现必须被断言检出。

### F5 · P2：审查报告被删掉，先前的审查问题也无法回看

**位置：`workbench/src/gates/taskHistory.ts:61`；`workbench/app/TaskRecord.tsx:48`。**

失败场景：审查员提交有效 review_submit，包含 findings 的 suggestion 和 `report["完成条件与变异检查"]`。`core.ts:4099` 将这些数据保存在 review.result，随后写入 review_result。整理器只返回 verdict 和简化的 failure_scenario，丢掉 report、suggestion；后一次审查还会覆盖整个 history.review。时间线对早先审查也只留下“需修复”字样，没有查看其问题或报告的入口。即使只有一次可合并审查，报告正文也不会显示。

证据：现有真实 T-2 夹具有两次审查：第一次 1 条 finding，第二次 0 条，两次都有“完成条件与变异检查”报告。实际输出仅剩最后的 `verdict:"可合并",findings:[]`。截图 ui/04 也只展示审查结论。这未满足 T-192/T-189 的“审查报告”，不能把“最近一次结论”当作等价交付。

最小修复：通过现有 task_history 保留可按 attempt/审查次数打开的报告及问题详情，包含修复建议；结果摘要仍可显示最近一次结论。复验有问题 → 修复 → 可合并的任务，确认两次报告可读且归属正确。

### F6 · P3：产品页仍无条件承诺点击任务进入 agent 分屏

**位置：`docs/index.html:55`。**

失败场景：用户按产品页第 1 节第 3 步点击已关闭、没有窗格的任务，实际进入整页记录。产品页仍写“点一张票，进入 agent 分屏”“worker 和独立审查并排”，没有说明记录页。T-192 明确要求对照此处，做不到的改产品页；本候选只更新了 workbench README。

证据类型：产品页与实现分支的静态对照。最小修复是准确区分有会话时的窗格和无会话时的记录页，并核对交互演示文字。无需扩大到整站重做。

## 已检查的边界与限制

- **操作锁与并发：静态已查，运行时 INCOMPLETE。** close 在 `request()` 取得任务 operationLock 后才 load、判断和 save；claim/dispatch、revoke/revise 使用同一把任务锁。没有发现新增的“先读状态、后抢任务锁”竞态。没有执行多进程锁竞争或崩溃注入，不据此宣布并发验收通过。
- **关闭条件：静态已查。** reason 经 text() 校验；ready、无 current_attempt、无 integration_intent 三个判断确实存在。正常绑定当前 attempt 的 run 无法通过 close 条件。它不检查 run 锁或历史未回收 attempt，因此不能将 close 成功解读为所有历史 worker 已停止。revoke 可清空 current_attempt 并将仍未回收的旧 worker 留给后续清理；本次未把这解释成额外的“关闭即回收”契约。
- **abandoned/upgraded：静态已查。** abandon 终结 attempt 后仍保留 current_attempt，reclaim 也保留该指针与终结状态，故直接 close 会拒绝；先 revoke 清除后才满足 ready 条件。这与候选明定的 close 条件一致，没有凭空判为状态卡死，但缺少这条旅程的实际验收。
- **run/resumeRuns：静态已查，运行时 INCOMPLETE。** follow/resumeRun 绑定原 attempt；在 current_attempt 已清空、任务随后关闭的路径，current() 会拒 stale_attempt，runFailed 走 superseded 及历史清理，不会因 closed 自动接管别的 attempt。恢复中回收后再派发的窗口若遇 close，dispatch 会拒 task_closed。没有执行真实后台重启、run 恢复或清理失败场景。
- **reclaim/integrate：静态已查。** closed 没有 current_attempt，integrate 的 not_verified 前置条件阻断；按历史 attempt reclaim 走 historicalAttempt，ownsTask=false，不会直接把 closed 写回 ready。未跑真实 worktree 清理。revoke/revise 的确定漏洞见 F1。
- **sidebar/metrics：静态已查。** projectCatalog 直接保留任务状态，界面用新增 gateStateNames 显示 closed；metrics 以既有 score_recorded 为输入，未发现仅因 closed 枚举新增而必然崩溃的分支。未运行完整 sidebar/metrics 回归，不能外推为全部通过。
- **空布局：局部探针 PASS。** prepareSelection 的零窗格结果为 layout=null、names={}；restoreArrangement、paneRects 对空值有分支，序列化布局也接受 null。`options.launch=[]` 在 unsaved 情况仍拒绝；saved 空布局的原有允许行为没有被本次条件改动改变。没有实测窗口关闭、重启恢复和布局持久化全过程。
- **事件字段：局部已核对。** submitted.commit、path_check.forbidden、oracle_check.modified、completion_check.result、review_result.review、score_recorded.data、integrated.intent.M/C、trailer_check.commit/trailers 与 core 写入相符。merge_failed 的另一种 details 结构不符，见 F3。未声称所有历史版本的事件格式都已覆盖。
- **结构：在本补丁中未发现新增吞异常、重试或第二套可变门禁 API。** task_history 是同一事件表的只读投影，TaskRecord 的读取失败有可见错误。按 Deep modules 的标准，事件整理放在一个小接口后是合理的；需要修的是这个投影遗漏的语义。没有为了修复而建议新增兼容层或平行 API。

## 现有证据能支持什么

证据目录为 `evidence/2026-10-27-batch28/T-192/`。

| 证据 | 本次核查结果 | 证明范围 |
| --- | --- | --- |
| red-close.json、red-history.json、red-tasks-after-revoke.json | 已读，前两者为拒绝，后者为 ready | 原入口缺少两个命令及回收后的状态问题；红态未证明全部 UI 旅程 |
| green-close*.json、green-dispatch-closed.json、green-tasks-after-close.json、green-history.json | 已读关闭、空理由、重复关闭、关闭后拒派及历史数据 | 隔离 beta+T-1 的单条关闭路径；没有覆盖 F1 的绕行 |
| history_check.ts、history-fixture.json | 本次重跑，退出 0、PASS | 真实导出夹具中的集成 M、尾注、回收等断言；只证明纯投影逻辑 |
| history-check-mutant1/2/3.json | 已读，均记录对应业务断言 FAIL | 三个特定坏实现被检出；未保存可重跑的 mutant 源码/完整生成命令，本次未重建这些变异 |
| history-check-mutant.json | 0 字节 | 不作为通过或失败证据；原样保留 |
| ui/01、02、03 | 已实际查看截图 | 同一隔离任务从占位窗格到整页记录；任务格与页内能显示已关闭、理由和任务卡 |
| ui/04、05 | 已实际查看截图 | 用真实事件填入的夹具能渲染集成、尾注、打分和时间线；不是现场完成一次派发到回收的证明 |

**证据版本存在具体不一致：** `green-history.json` 的 steps 仍包含 seq 4/5 等 card_validate、card_save 和 create 拒绝，而本候选 `quietRefusals` 会过滤它们。该 JSON 至少早于最终过滤行为，不能作为最终整理器输出的完整快照；关闭理由等其中的事实仍可核对。ui/03 则已不显示这些草拟拒绝。应补最终候选的入口输出并绑定构建版本，不能把这份旧绿态当成最终输出一致性证明。

**“已回收的票不再是空页”：INCOMPLETE。** 原始 a2a+T-138 仅作为投影函数夹具验证；UI 截图是 beta+T-1，以及向另一个任务注入真实事件的 T-2。RESULTS 明确说明 T-2 的任务行仍为 ready，未写入对应 attempts，不能证明真实任务与其会话、状态、布局一同恢复正确。无存活窗格的静态画面有证据，真实回收任务的完整内容与后续派发仍缺入口复验。

**“关闭后显示已关闭”：隔离任务静态画面有支持；当前候选整体不能 PASS。** 尚有 F1 的终态漏洞和 F2 的页面同步问题。未在用户真实状态中关闭任何任务。

没有启动或重打包 Electron，没有操作原后台，没有跑完整 build、真实 worker/reviewer、socket 端到端旅程、读屏或性能测试。截图与当前补丁的构建版本绑定也未独立复核。以上跳过项均不写成通过。project-map status 在开始与结束检查均显示 Problems(0)、Stale living docs(0)，但这不替代产品页的实际语义核对。

## 可重放的本次检查

以下命令从仓库根目录运行。只用内存数据，不修改仓库或既有状态。原有检查命令为：

```sh
node evidence/2026-10-27-batch28/T-192/history_check.ts
python3 /Users/luckye/.agents/skills/project-map/scripts/project_map.py status --root /Users/luckye/Documents/Code/a2a
```

### 附录 A：closed 的两个重开入口

```sh
node --input-type=module <<'JS'
import { DatabaseSync } from 'node:sqlite';
import { readFileSync } from 'node:fs';
import { A2AGates } from './workbench/src/gates/core.ts';
const gates = Object.create(A2AGates.prototype);
gates.db = new DatabaseSync(':memory:');
gates.db.exec('CREATE TABLE tasks(id TEXT PRIMARY KEY,data TEXT); CREATE TABLE attempts(id TEXT PRIMARY KEY,data TEXT); CREATE TABLE verifications(id TEXT PRIMARY KEY,data TEXT); CREATE TABLE events(seq INTEGER PRIMARY KEY,time TEXT,task TEXT,attempt TEXT,type TEXT,details TEXT);');
gates.operationLock = () => ({ close() {} });
const base = JSON.parse(readFileSync('./evidence/2026-10-27-batch28/T-192/green-close.json','utf8')).task;
for (const command of ['revoke','revise']) {
  gates.db.prepare('INSERT OR REPLACE INTO tasks VALUES (?,?)').run(base.task_id,JSON.stringify(base));
  const r = await gates.call({ command, task:base.task_id, reason:'review probe', spec_rev:2 });
  console.log(JSON.stringify({command,ok:r.ok,state:r.task?.state,error:r.error}));
}
gates.db.close();
JS
```

本次退出码 0，输出：

```json
{"command":"revoke","ok":true,"state":"ready"}
{"command":"revise","ok":true,"state":"ready"}
```

### 附录 B：遗漏事件及审查报告

```sh
node --input-type=module <<'JS'
import { taskHistory } from './workbench/src/gates/taskHistory.ts';
import { readFileSync } from 'node:fs';
const e = (seq,type,details) => ({seq,time:'2026-10-27T08:00:00Z',attempt:'sentinel-attempt',type,details});
console.log('quality',JSON.stringify(taskHistory([
  e(1,'red_check',{index:1,B:'base',C:'candidate',test_paths:['test.js'],base_result:{returncode:1},candidate_result:{returncode:0},passed:true}),
  e(2,'rule_check',{id:'sentinel-rule',result:{returncode:0},passed:true})
]).steps));
console.log('verify',JSON.stringify(taskHistory([
  e(1,'rejected',{input:{command:'verify'},error:'git_failed',details:{stderr:'fatal: invalid ref refs/heads/work'}})
]).steps));
console.log('merge',JSON.stringify(taskHistory([
  e(1,'verification_result',{state:'merge_failed',result:{returncode:1}}),
  e(2,'verification_conflict',{state:'merge_failed',conflict:{files:['sentinel.txt']}}),
  e(3,'rejected',{input:{command:'verify'},error:'merge_conflict'})
]).steps));
const f=JSON.parse(readFileSync('./evidence/2026-10-27-batch28/T-192/history-fixture.json','utf8'));
const rows=f['a2a-lcu-demo+T-2'];
console.log('reviews',JSON.stringify({
  input:rows.filter(r=>r.type==='review_result').map(r=>({findings:r.details.review.result.findings.length,reportSections:Object.keys(r.details.review.result.report??{})})),
  output:taskHistory(rows).review
}));
JS
```

本次退出码 0。quality 与 verify 均输出 `[]`；merge 仅输出一条 passed=false、detail=null 的“验收”。reviews 的输入有两份报告、第一次有 1 条问题，输出仅剩最后可合并且 findings=[] 的摘要。哨兵输入是本次新增的独立反例，没有写入产品文件或复用生产常量作为答案。

### 附录 C：零窗格与后续派发

```sh
node --input-type=module <<'JS'
import { readFileSync } from 'node:fs';
import { stripTypeScriptTypes } from 'node:module';
const src=readFileSync('./workbench/app/main.ts','utf8');
const region=(a,b)=>src.slice(src.indexOf(a),src.indexOf(b,src.indexOf(a)));
const code=[
  region('function mapLayout(', '// A task arrangement'),
  region('async function taskPaneLayout(', 'async function serializedArrangement('),
  region('function restoreArrangement(', '// New terminals start'),
  region('async function prepareSelection(', 'export async function run('),
  region('function selection(', '// T-177:')
].join('\n');
const fixture={task:{task_id:'p+T',project_id:'p',current_attempt:null},saved:false};
const request=async(_,q)=>q.command==='workbench_snapshot'
  ? {ok:true,task:fixture.task}
  : {ok:true,panes:[],saved:fixture.saved,arrangement:null};
const f=new Function('request','randomUUID','requireSavedPane','requireCurrentPane','requireShellPane','requireAgentView','readOperatorCredential',
  stripTypeScriptTypes(code)+';return {prepareSelection,selection};')(request,()=> 'pane-key');
const p=await f.prepareSelection({state:'unused',task:'p+T'});
console.log(JSON.stringify({panes:p.panes.length,layout:p.layout,names:p.names}));
try { await f.prepareSelection({state:'unused',task:'p+T',launch:[]}); }
catch(e) { console.log(e.message); }
const context={task:p.task,project:null,options:{},panes:new Map(),parked:new Map(),layout:p.layout,names:p.names};
fixture.task={...fixture.task,current_attempt:{attempt_id:'new-worker'}};
console.log(JSON.stringify({backendHasAttempt:!!fixture.task.current_attempt,paneKeys:f.selection(context).paneKeys}));
console.log(JSON.stringify({reselectedPanes:(await f.prepareSelection({state:'unused',task:'p+T'})).panes.length}));
JS
```

本次退出码 0，输出依次为零窗格与 null 布局、显式空数组拒绝、新 attempt 存在但 paneKeys=[]、重新选任务后 panes=1。这是隔离逻辑证据，未代替真实窗口旅程。

## 修复后的最小验收

先修复 F1，再补 F2 的任务级同步及 F3～F5 的事件内容，最后同步 F6 文案。采用一条 Tracer bullet 验收旅程：真实入口建任务并打开无窗格页面 → 后台派发并在原页面看到 worker → 执行非空红态/规则检查 → 审查打回并修复 → 集成回收 → 查看两次审查报告及检查 → 关闭 → 尝试 revoke/revise/再派发，确认终态仍为 closed。保留命令、任务与 attempt 标识、候选构建标识、输出和界面截图；再单独覆盖验收前失败与合并冲突。这些行为断言应进入工作台对应门禁和 UI 验收入口，不能只依靠两份“不适用”夹具。

**最终结论：需修复。**
