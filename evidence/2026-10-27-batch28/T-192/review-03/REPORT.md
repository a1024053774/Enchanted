# T-192 独立审查第 3 轮

STATUS: INCOMPLETE  
RELEASE: INCOMPLETE  
**交付判断：NO_GO；结论：需修复。**

旧问题的主要修复有效，未复现关闭终态被重开或独有 verify 错误被隐藏。仍有三个低严重度的实现、文案问题，以及真实入口证据缺口。不能据现有材料将 T-192 两条验收整体判为 PASS。

## TARGET：对象、范围与独立性

审查对象是 `/private/tmp/t192-review3/change.diff`，基于 HEAD `c76e2ab2a7dfd5fe0692ff9f1150ef586354a4d0` 的未提交修改及两个新文件。审查期间两次将受控文件的 `git diff -- docs/index.html workbench`、两个新文件全文与给定补丁逐字比较，均一致；未计算校验值。以下源码位置均相对于 `/Users/luckye/Documents/Code/a2a`，行号对应本候选。

目标：核对 F1～F6、R1～R5、记录页打开 worker 的新路径、历史过滤与两条验收。非目标：修改实现、关闭任务、派发真实 agent、重新构建或发布、全站审查。只写本报告，没有 checkout、切分支、改仓库文件或操作既有后台。

验收依据来自 T-192、T-189、U07/U08；现有测试是待审证据，不是唯一答案。Ubiquitous language 沿用“任务、执行尝试（attempt）、会话、窗格、门禁记录”，区分运行会话与打开的窗格。按 BRIEF 接受新版“显式点击按钮、不自动切视图”的方案，不把取消自动跟随本身算成缺陷。

访问方式为源码、已有入口输出与截图、内存 SQLite、生产函数的局部执行。没有本轮原生 Electron 交互证据；涉及模拟 hooks 或 runtime 的结论只到局部逻辑层。Deep modules 方面，`task_history` 仍是既有事件表上的只读投影，未发现新增第二套可变门禁或为本次功能增加的吞异常、自动重试路径。

## FINDINGS：确定问题与证据缺口

### N1 · P3：正常合并冲突的反馈事件打断去重，重复拒绝仍显示

**位置：`workbench/src/gates/taskHistory.ts:73`、`:76`；关联 `workbench/src/gates/core.ts:1849`、`:1851`、`:1698`、`:1734`、`:1740`。**

具体状态：同一个 attempt 的一次 verify 发生合并冲突，worker 仍可接收修复反馈。真实写入路径是：

```text
verification_result(state=merge_failed)
verification_conflict(files=[...])
conflict_rework_intent
conflict_feedback_intent
conflict_feedback_delivered
verification 清理事件（实际清理时还有这些）
rejected(input.command=verify,error=merge_conflict)
```

错误结果：整理器只忽略 `command_intent/result`，其余即使根本不显示，也会覆盖 `previous`。最终拒绝之前的事件不再是 `verification_conflict`，同次冲突因而显示为“验收 · 合并失败”“合并冲突 · 文件”“门禁拒绝 · verify：merge_conflict”三步。第三步重复第二步，未兑现本次修复与现有检查所声称的冲突去重；不造成错误被隐藏，故定为 P3。

证据：本轮执行生产 `writeConflict()`、`save()` 和门禁拒绝捕获路径，数据库在内存，外部 runtime 与 Git 清理被替代；生成前三个反馈事件后仍出现重复拒绝。另以包含反馈事件的独立哨兵输入调用生产 `taskHistory()`，要求不重复展示同次拒绝的断言退出 1（附录 B）。不是实际运行 Git 合并冲突的端到端复现。

现有 `history_check.ts` 的冲突样例把 `verification_conflict` 和 rejected 直接相邻，漏掉上述生产事件，所以其 PASS 检不出此问题。修复应按同一次验收关联去重，并保留反馈或清理另行失败的不同错误；不能恢复“任意前一失败都折叠”。复验包含反馈、清理的冲突序列，以及冲突后出现 `git_failed` 等额外错误的序列。

### N2 · P3：产品页仍以“有运行会话”承诺已有分屏，与新版按钮方案不符

**位置：`docs/index.html:55`；关联 `workbench/app/renderer.tsx:1119`、`workbench/app/TaskRecord.tsx:89`。**

具体状态：用户停留在零窗格记录页，后台成功派发 worker；worker 已运行、侧栏已出现，用户尚未点击“打开 worker 会话”。

错误结果：按新版设计，任务页继续显示整页记录和按钮；产品页却说“有会话在跑时，worker 和独立审查并排”，并把整页记录只归于“没有会话的票”。同样，用户主动关闭窗格也不会使运行会话消失。这里决定展示分支的是打开的窗格数，不能用是否有运行会话替代。

证据：源码分支及已查看的 `ui/09-open-worker-button.jpg`；该截图恰好是有 worker 会话、仍为整页记录的反例。未运行产品页交互演示。首轮 F6 的无条件标题已修，但现有条件仍不准确。

修复方向：写明“有打开的窗格时，窗格在上、记录在下；没有打开的窗格时显示整页记录；当前 worker 可通过按钮打开”。不要承诺 worker 和 reviewer 一定同时并排。以新版记录页、单 worker 窗格、回收后记录页分别核对文案。

### N3 · P3：“打开 worker 会话”在 busy 时仍可点击，点击被静默丢弃

**位置：`workbench/app/TaskRecord.tsx:92`、`workbench/app/renderer.tsx:1119`；关联 `renderer.tsx:716`、`:842`、`:905`。**

具体状态：零窗格记录页已有 worker 按钮；用户“刷新列表”的 sidebar 请求尚未返回（loading=true），或正在新建终端（creating=true）。此时不是 navigating，TaskRecord 仍显示。

错误结果：按钮没有 `disabled` 或忙碌提示，但点击进入 `selectAgent()` 后立即被 `if (busy) return` 丢弃，无 IPC、无错误说明。侧栏同一动作的按钮已用 `disabled={busy}` 正确表达这个限制。

证据：本轮编译生产 TaskRecord，模拟 hooks、接口与 JSX 树，并执行生产 selectAgent 函数体：busy=true 时按钮 `disabled=false`、点击后 IPC=0；重渲染为 busy=false 后再次点击 IPC=1（附录 C）。这是临时无反馈，并非旧 R3 的永久旧闭包；忙碌结束后可以恢复。

修复方向：把相同 busy 状态传给按钮并禁用，或给出明确忙碌反馈；保持已有导航互斥。复验列表读取延迟、新建终端延迟及其结束后的再次点击。

### N4 · P2（验收证据）：真实派发回执被截断，回收任务的完整入口证据仍未闭合

**位置：`evidence/2026-10-27-batch28/T-192/green3-dispatch-while-viewing.json:1`、`RESULTS.md:55`、`:60`；另有 `green2-claim-while-viewing.json:1`。**

具体输入：按 RESULTS 引用的 green3 回执核对 task、attempt、runtime launch、实际 argv 和成功结果。文件只有 400 字节，在任务卡 goal 字符串中途结束，JSON 解析报 `Unterminated string`，没有 attempt、launch、argv 或完整结束状态。green2 claim 回执也只有 250 字节，在字符串中间截断。

结果：两份文件开头的 `ok:true` 不能代替完整、可关联的入口输出；无法据它们独立核对 RESULTS 所说的 launch 配置或把 UI/09、10 绑定到完整派发结果。这是证据缺失，不是“dispatch 已证实失败”。扫描该目录顶层 JSON 时，本轮仅这两份解析失败；七个变异结果均能解析且为 FAIL。

此外，RESULTS 明确说真实 worker 只到交付前，整页历史内容仍来自注入真实事件的夹具。因而“派发后按钮出现”与“真实任务回收后从任务格重入、状态/布局/历史一致”尚不是同一条完成的旅程。

修复方向：保留这两份截断文件，另存完整回执与构建来源，不覆盖异常证据；补一条隔离任务的真实回收入口验收。严重度 P2 指验收证据阻断，不推断生产数据或门禁损坏。

## EVIDENCE：旧问题逐项核对

| 编号 | 本轮结论 | 本轮实际核对与边界 |
| --- | --- | --- |
| F1：closed 被 revoke/revise 重开 | PASS（局部入口） | 内存 SQLite 上调用生产 `A2AGates.call()`：revoke、revise、claim 均拒 `task_closed`，状态保持 closed；提供 runtime 占位与合法 runtimeMode 后 dispatch 也拒 `task_closed`。与 green2 回执一致。未跑真实多进程锁或崩溃恢复。 |
| F2：零窗格不跟随、旧门禁栏 | 新方案局部 PASS | 不再自动跟随；记录轮询更新状态并提供手动按钮，零窗格分支不再渲染旧门禁栏。已看 UI/09、10；附录 C 支持首读即有 attempt 与后续侧栏更新均能提供按钮。真实回收全旅程仍 INCOMPLETE，busy 细节见 N3。 |
| F3：verify 独有错误消失、merge_failed 形状 | 原数据丢失已修；去重仍有 N1 | 实际 call 重放 integrate/not_verified → verify/git_failed，两条错误均保留；两种 verification_result 结构均能输出结果，冲突文件也在。未在已查序列发现新版误折叠独有错误；正常冲突存在漏折叠。 |
| F4：red_check/rule_check 缺失 | PASS（投影） | 映射保留检查编号、规则 id、状态与退出码；history_check 通过，删除 rule_check 的变异失败。两个真实事件夹具本身都没有 red_check/rule_check，仍缺真实检查全链路证据。 |
| F5：早先审查、正文与建议丢失 | PASS（投影及渲染代码） | T-2 两份审查、第一份 finding/suggestion 与每份 report 的现有断言通过；最后一份覆盖前面报告的变异失败。TaskRecord 对每份 review 渲染 findings、suggestion、report，最后一次默认展开。已看 UI/06，但没有本轮操作 UI 展开第一份。 |
| F6：产品页无条件承诺分屏 | 原标题已修，条件仍不一致 | 已说明记录页，但仍按“运行会话”划分展示，见 N2。不能将该项整体上调为 PASS。 |
| R1：已存空布局使 refresh 无效 | PASS（替换方案） | 不再刷新 prepareSelection；按钮传具体 launch 走 selectAgent → changeView({task,launch})，避开旧 saved 空布局的选择分支，不自动覆盖用户关窗格的意图。没有本轮真实回收再派发 UI 操作。 |
| R2：首次响应已有 attempt 被当基线 | PASS（局部行为） | firstAttempt/onAttemptStarted 已删除；首次成功 history 响应即计算当前 launch，附录 C 首读有 attempt、侧栏随后出现时按钮可见。 |
| R3：轮询保留旧 busy=true 回调 | PASS（旧故障机制） | effect 只更新 loaded/error，打开回调在每次渲染时重新产生；不再从轮询调用导航。busy 清除后的重渲染与点击能发 IPC，不会永久吞掉通知。临时无反馈另列 N3。 |
| R4：任意前一失败折叠 verify | PASS（原反例） | 实际只读 Git `rev-parse` 失败后，task_history 同时保留 integrate/not_verified 和 verify/git_failed；any-previous-failure 变异被业务断言检出。新版同 attempt、同错误码的 delivery_rejected 去重样例通过；不同 attempt、不同错误码不会满足分支。N1 是漏折叠，不是旧误折叠复发。 |
| R5：README 无条件隐藏 verify | PASS（原问题） | `workbench/README.md:1092` 已改为有限折叠、每次审查与零窗格展示，移除“所有 verify 被拒都不显示”的说法；不是仍留旧描述。实际冲突去重的实现缺口见 N1。 |

### openSession 与 refresh 的专项结论

- 按钮只在整页记录分支显示：history 成功加载、当前 attempt 有 `runtime_identity.launch`，且 renderer 当前 agents 中能找到这个 id。docked 版本不传 openSession，也不显示按钮。
- 侧栏尚无该会话时，不显示按钮；agents 更新触发重渲染后才出现，不需要再次更换 attempt。永久隐藏的会话不会因记录页自行恢复；主进程 select-agent 本来就要求最新 sidebar 中有该 launch。本轮将此视为复用侧栏路径的明确边界，没有把“不绕过隐藏状态”判成新缺陷。
- 侧栏中已结束的当前 worker 仍会产生按钮。select-agent 允许历史查看；`main.ts:789` 的 inspect 分支对非 running、failed、historical 等状态置 viewOnly。已查代码，没有发现该按钮会重新启动已结束会话。未本轮操作真实历史窗格，不能把静态核对写成 UI PASS。
- navigating 时记录页卸载；loading/creating 时仍可显示，所以存在 N3。用户点击直接调用 selectAgent，它与 navigate 使用同一个 busy 条件并设置 navigating。没有自动回调抢走用户后来的选择；没有本轮验证真实 IPC 重叠导航、同一帧连点或进程崩溃。
- `preload.ts:47`、renderer 的类型和 selectTask 调用、`main.ts:495` IPC 签名均已恢复单个 task 参数。搜索 app/src 未找到 `onAttemptStarted`、`firstAttempt`、`selectTask(...,true)` 或 `select-task` refresh 参数。保留的 Workbench `refresh()` 是原有“刷新列表”，不是此次已删除的参数。记录页轮询无视图刷新调用，未见本次机制导致的自动刷新循环。

## 两条验收

1. **“已回收的票点进去不是空页”：INCOMPLETE。** 真实导出的 a2a+T-138 有 30 个事件，投影能输出任务创建、交付、检查、打回、撤销与回收，不虚构集成；另一个真实夹具支持多次审查、打分、集成提交和尾注。UI/03 支持已关闭任务的记录页，UI/06 支持注入事件后的内容渲染，UI/09、10 支持派发后显式打开 worker 的画面。但它们没有证明同一真实回收任务从任务格进入时，其任务行、attempt、布局与事件一起正确恢复。RESULTS:60 也承认未走完此流程。本轮没有操作用户的 a2a+T-138。
2. **“关闭后任务格显示已关闭”：PASS（现有隔离证据范围）。** 已实际查看 UI/01 的已关闭任务格；green2-tasks-beta 为 closed，gateStateNames 有“已关闭”，任务格使用该映射；本轮关闭终态局部重放通过。没有重新构建并从当前候选操作 UI，截图与构建来源没有独立重建，因此当前候选完整原生 UI 验收仍 INCOMPLETE。

下一条有价值的 **Tracer bullet** 是隔离任务经真实入口派发、检查、审查、集成或打回，再回收，从任务格重入记录页；核对同一任务/attempt 的内容、布局与状态，然后关闭并核对任务格。该旅程应保留完整回执、构建来源与截图，避免继续用“注入事件的渲染”替代任务生命周期证据。本轮只读审查不执行这些写操作。

## COUNTEREXAMPLE：已运行检查及复现命令

环境 Node `v26.5.0`。以下从仓库根目录运行；输出与退出码记录在本文。没有创建新测试文件。

### 附录 A：现有检查与七个已知坏实现

```sh
node evidence/2026-10-27-batch28/T-192/history_check.ts
```

退出 0，status=PASS、failures=[]。输出保留 T-2 两次审查、合并提交 9312a7077f、T-138 的回收；这只是投影检查。

原 mutants.sh 会向当前目录写 JSON，本轮移除输出重定向、使用绝对检查脚本路径，在内存中交给 bash，保留原 sed 变异；没有覆盖既有证据。其临时变异目录由脚本自行清理。

```sh
python3 - <<'PY'
from pathlib import Path
import subprocess,re,json
r=Path('/Users/luckye/Documents/Code/a2a')
s=(r/'evidence/2026-10-27-batch28/T-192/mutants.sh').read_text()
s=s.replace('node history_check.ts','node '+str(r/'evidence/2026-10-27-batch28/T-192/history_check.ts'))
s=s.replace('> "history-check-$1.json"','')
p=subprocess.run(['bash'],input=s,text=True,capture_output=True,cwd=r)
for m in re.finditer(r'(\{\n "status":.*?\n\})\n([^\n]+)',p.stdout,re.S):
 d=json.loads(m[1]);print(m[2],d['status'],d['failures'])
print('wrapper exit:',p.returncode,'stderr:',p.stderr)
PY
```

七个 node 变异分别退出 1，均因对应业务断言失败：integration-c、no-quiet、no-reclaim、last-review-only、drop-all-verify、any-previous-failure、no-rule-check。包装脚本退出 0，不等于变异通过。它们能检出所针对的坏实现，不能检出 N1 或 UI 忙碌状态问题。

### 附录 B：关闭、旧 R4 与生产冲突反馈事件

```sh
node --input-type=module <<'JS'
import { DatabaseSync } from 'node:sqlite';
import { readFileSync } from 'node:fs';
import { A2AGates,Refusal } from './workbench/src/gates/core.ts';
const g=Object.create(A2AGates.prototype);g.db=new DatabaseSync(':memory:');
g.db.exec('CREATE TABLE tasks(id TEXT PRIMARY KEY,data TEXT);CREATE TABLE attempts(id TEXT PRIMARY KEY,data TEXT);CREATE TABLE verifications(id TEXT PRIMARY KEY,data TEXT);CREATE TABLE events(seq INTEGER PRIMARY KEY,time TEXT,task TEXT,attempt TEXT,type TEXT,details TEXT);');
g.operationLock=()=>({close(){}});
const base=JSON.parse(readFileSync('evidence/2026-10-27-batch28/T-192/green-close.json','utf8')).task;
g.db.prepare('INSERT INTO tasks VALUES (?,?)').run(base.task_id,JSON.stringify(base));
for(const command of ['revoke','revise','claim']){
 const r=await g.call({command,task:base.task_id,reason:'review3',spec_rev:2,owner:'review3'});
 console.log(command,r.ok,r.error,JSON.parse(g.db.prepare('SELECT data FROM tasks WHERE id=?').get(base.task_id).data).state);
}
g.runtime={};console.log('dispatch',JSON.stringify(await g.call({command:'dispatch',task:base.task_id,runtimeMode:'approval-required'})));g.runtime=undefined;
const t={...base,task_id:'review3+T-1',project_id:'review3',state:'submitted',repo:'/private/tmp/t192-review3',candidate_commit:'a'.repeat(40),current_attempt:{task_id:'review3+T-1',attempt_id:'sentinel-attempt',fence:base.fence,spec_rev:base.spec_rev}};
g.db.prepare('INSERT INTO tasks VALUES (?,?)').run(t.task_id,JSON.stringify(t));
for(const command of ['integrate','verify']){const r=await g.call({command,task:t.task_id});console.log(command,r.ok,r.error);}
console.log('unrelated',JSON.stringify((await g.call({command:'task_history',task:t.task_id})).history.steps));
const identity={launch:'sentinel-launch',thread:'sentinel-thread',shell_pid:1,leader_pid:2,native_session:'sentinel-native'};
const a={...t.current_attempt,task_id:'review3+T-2',attempt_id:'conflict-attempt',thread_id:identity.thread,runtime_identity:identity,workspace:'/sentinel/worker',turn_id:'turn'};
const v={verification_id:'sentinel-v',ordinal:1,C:t.candidate_commit,G:base.base_commit,state:'merge_failed',result:{stdout:'conflict',stderr:''},conflict:{files:['sentinel.txt']}};
const c={...t,task_id:a.task_id,current_attempt:a,verification:v};
g.db.prepare('INSERT INTO tasks VALUES (?,?)').run(c.task_id,JSON.stringify(c));
g.runtime={readThread:async()=>({runtime_identity:identity,workspace:a.workspace,provider:'codex',running:false,stopped:false,archived:false,error:null,blocked:false}),sendGateFeedback:async()=>{}};
g.cleanupVerification=async()=>{};
g.verifyCandidate=async(task,attempt)=>{g.save(task,'verification_result',v);g.save(task,'verification_conflict',v);await g.writeConflict(task,attempt,v);throw new Refusal('merge_conflict',v);};
const result=await g.call({command:'verify',task:c.task_id});
console.log('conflict return',result.ok,result.error);
console.log('conflict events',(await g.call({command:'events',task:c.task_id})).events.map(e=>e.type));
console.log('conflict steps',JSON.stringify((await g.call({command:'task_history',task:c.task_id})).history.steps));
g.db.close();
JS
```

退出 0。关闭四个入口均拒 `task_closed`；integrate 返回 not_verified，verify 经真实只读 Git 返回 git_failed，两条在 history 中均可见。冲突部分**替代了 verifyCandidate 的 Git/合并过程与 cleanupVerification**，调用真实 writeConflict 产生反馈事件；结果为同次冲突的三条显示步骤，包括重复 verify 拒绝。只证明事件序列与投影问题，不宣称真实 Git 冲突全流程通过。

以下哨兵断言独立检查“不重复表达同次冲突”，本候选退出 1，`AssertionError: 1 !== 0`：

```sh
node --input-type=module <<'JS'
import assert from 'node:assert/strict';
import {taskHistory} from './workbench/src/gates/taskHistory.ts';
const e=(seq,type,details)=>({seq,time:'2026-10-27T08:00:00Z',attempt:'unseen-conflict',type,details});
const events=[e(1,'verification_result',{state:'merge_failed'}),e(2,'verification_conflict',{conflict:{files:['novel.txt']}}),e(3,'conflict_rework_intent',{}),e(4,'conflict_feedback_intent',{}),e(5,'conflict_feedback_delivered',{}),e(6,'rejected',{input:{command:'verify'},error:'merge_conflict'})];
const steps=taskHistory(events).steps;console.log(JSON.stringify(steps));
assert.equal(steps.filter(s=>s.label==='门禁拒绝'&&s.detail==='verify：merge_conflict').length,0,'same verify conflict is already explained by its structured conflict step');
JS
```

### 附录 C：按钮、首读、侧栏、busy 与结束状态

下列命令编译生产组件、替代 hooks/JSX 渲染器和 IPC，执行真实 selectAgent 函数体；不是 React DOM 或 Electron 测试。

```sh
node --input-type=module <<'JS'
import { readFileSync } from 'node:fs';
import { createRequire,stripTypeScriptTypes } from 'node:module';
const require=createRequire(new URL('./workbench/package.json',import.meta.url));
const {transformSync}=require('rolldown/utils');
let source=readFileSync('workbench/app/TaskRecord.tsx','utf8').replace(/^import .*\n/gm,'');
const transformed=transformSync('TaskRecord.tsx',source,{jsx:{runtime:'classic'},typescript:{onlyRemoveTypeImports:true}});
if(transformed.errors.length)throw transformed.errors[0];
const code=transformed.code.replace('export function TaskRecord','function TaskRecord').replace(/export \{[\s\S]*?\};?\s*$/,'');
let states=[],slot=0,effectDeps,cleanup,timer,first=true,calls=0,busy=true,agents=[],lastOptions;
let loaded={task:{task_id:'sentinel+T-3',title:'哨兵任务',state:'claimed',current_attempt:{attempt_id:'a',runtime_identity:{launch:'new-worker'}}},history:{steps:[],reviews:[],score:null,integration:null,closed:null}};
const React={Fragment:'fragment',createElement:(type,props,...children)=>({type,props:props??{},children})};
const useState=init=>{const i=slot++;if(!(i in states))states[i]=init;return [states[i],v=>states[i]=v];};
const useEffect=(fn,deps)=>{if(!effectDeps||deps[0]!==effectDeps[0]){cleanup?.();effectDeps=deps;cleanup=fn();}};
const TaskRecord=new Function('React','useState','useEffect','window','setInterval','clearInterval','gateStateNames',code+';return TaskRecord;')(
 React,useState,useEffect,{a2a:{taskHistory:async()=>structuredClone(loaded)}},fn=>(timer=fn,1),()=>{},{});
const renderer=readFileSync('workbench/app/renderer.tsx','utf8');
const agentCode=stripTypeScriptTypes(renderer.slice(renderer.indexOf('  const selectAgent ='),renderer.indexOf('  const decideRoleRequest =')));
const flatten=(tree)=>!tree||typeof tree!=='object'?[]:[tree,...(tree.children??[]).flat(Infinity).flatMap(flatten)];
const flush=async()=>{for(let i=0;i<5;i++)await Promise.resolve();};
function render(){slot=0;const selectAgent=new Function('busy','setNavigating','setNavigationError','window','applySelection','setFocusedAgent','setPage','setFocusRequest',agentCode+';return selectAgent;')(
 busy,()=>{},()=>{},{a2a:{selectAgent:async()=>{calls++;return {focusKey:'k'};}}},()=>{},()=>{},()=>{},()=>{});
 return flatten(TaskRecord({task:'sentinel+T-3',docked:false,openSession:launch=>{const agent=agents.find(row=>row.id===launch);return agent?()=>void selectAgent(agent):null;}})).find(x=>x.type==='button');}
render();await flush();
console.log('sidebar missing, button:',!!render());
agents=[{id:'new-worker',state:'running'}];let button=render();console.log('first read already has attempt, button:',!!button);
button.props.onClick();await flush();console.log('busy click:',JSON.stringify({disabled:button.props.disabled??false,ipcCalls:calls}));
busy=false;button=render();button.props.onClick();await flush();console.log('after busy clears, IPC calls:',calls);
agents=[{id:'new-worker',state:'ended',history:true}];console.log('ended session, button:',!!render());
loaded.task.current_attempt=null;timer();await flush();console.log('after attempt revoked, button:',!!render());
cleanup();console.log('unmount cleanup called');
JS
```

退出 0，输出依次为：侧栏缺失 false；首读已有 attempt true；busy click 为 `disabled:false,ipcCalls:0`；busy 清除后 IPC=1；已结束会话按钮 true；撤销 current_attempt 后 false；清理函数已调用。清理函数被调用不等于已验证全部迟到响应时序。

## LIMITATIONS：证据覆盖与未查项

- 已实际查看 UI/01、03、06、09、10；没有本轮重看 UI/02、04、05、07、08，也没有重新打开打包应用。截图只能支持静态画面，不能单独证明点击过程、构建来源或完整生命周期。
- 读取了前两轮报告与 RESULTS 的逐项处理；历史删除的三个手工变异输出没有恢复，未将重建的七个变异冒充旧失败证据。旧 green-history.json 仍按已知旧版本输出看待，不当作最终过滤快照。
- 未执行完整 build、真实 worker/reviewer、实际红态/规则检查全链路、真实 socket/IPC 全旅程、锁竞争、恢复/重启、读屏、性能或产品页交互演示。上述均不报告 PASS。
- Agent 产品本轮适用的轴是编排状态、异步更新、身份/会话查看与界面入口；身份权限只追了本次新增路径及直接调用方，不是全权限审计。模型能力、检索、文件解析、部署发布不是本补丁承诺的能力，本轮不评估。
- project-map status 开始、结束均退出 0：Problems(0)、Stale living docs(0)。这只证明地图检查结果，不代替文案与实现一致性审查。
- 证据读取时两份截断 JSON 的解析失败已保留并列 N4；几次定位命令因路径不存在或搜索无命中而退出 1，不算产品红态。只有附录 B 的哨兵断言失败属于本文新增行为反例。

## RULE：应补在哪里

历史过滤这一失败类别已在多轮重复出现。应在现有 history_check.ts 中加入带真实反馈/清理事件的同次冲突序列，并同时断言额外错误仍可见；当前候选必须先使新断言失败，再验证修复。按钮 busy 与已存空布局的手动打开路径应进入任务页真实入口验收，不能只靠历史投影或连续两张截图。无需新增平行 API 或兼容层。

**最终结论：需修复。**
