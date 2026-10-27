# T-192 独立审查第 2 轮

**状态：NO_GO。结论：需修复。** 行为检查发现确定缺陷；完整端到端验收证据仍为 INCOMPLETE。

审查对象为 `/private/tmp/t192-review2/change.diff`，基于 HEAD `c76e2ab2a7dfd5fe0692ff9f1150ef586354a4d0` 的未提交修改和两个新增文件。开始与结束时逐字比较了给定补丁、仓库 `git diff -- docs/index.html workbench` 及两个新文件，均一致。未 checkout、切分支、修改仓库或操作既有后台；仅创建本报告。以下源码路径相对于 `/Users/luckye/Documents/Code/a2a`，行号对应本候选。

范围依据为 T-192、T-189 和 U07/U08：回收后任务页仍能读取任务卡、各执行尝试的检查与审查等记录；门禁关闭后的任务格显示“已关闭”。本轮重点核对六项旧问题、刷新时序和历史投影，不是全站审查。Ubiquitous language 沿用项目术语：任务、执行尝试（attempt）、窗格、门禁记录，不将“已有 attempt”等同于“已有打开的窗格”。

## F1～F6 逐项结论

| 首轮编号 | 本轮结论 | 代码、证据与边界 |
| --- | --- | --- |
| F1：关闭被 revoke/revise 重开 | PASS（已查入口） | `core.ts:3948` 新增 closed 拒绝。内存 SQLite 上重放生产 `A2AGates.call()`：revoke、revise、claim 均返回 `task_closed`，状态仍 closed；提供占位 runtime、合法 runtimeMode 后 dispatch 也返回 `task_closed`。与 `green2-revoke-closed.json`、`green2-revise-closed.json`、`green2-tasks-beta.json` 一致。没有复验多进程锁竞争或崩溃恢复。 |
| F2：零窗格页面不跟随、旧门禁栏 | 部分修复，NO_GO | 零窗格时不再渲染旧门禁栏，记录页轮询自己的状态；ui/07、08 支持无已存布局的 claim 跟随机制。已有空布局、首次读取时序和旧 busy 闭包仍会漏刷，见 R1～R3。 |
| F3：verify 拒绝过滤、merge_failed 形状 | 部分修复，NO_GO | 独立的早期 verify 拒绝已能显示；两种 verification_result 写法和冲突文件的现有断言通过。但“上一个显示步骤失败”不等于“同一次 verify 的重复失败”，仍会隐藏独有原因，见 R4。 |
| F4：red_check/rule_check 缺失 | PASS（纯投影） | `taskHistory.ts:34`、`:36` 已映射编号/规则 id、通过状态及退出码；现有哨兵断言通过，删除规则映射的变异失败。没有真实运行含这些检查的 worker → verify 全链路，因此不能把投影 PASS 写成完整门禁验收 PASS。 |
| F5：报告及早先审查丢失 | PASS（投影与静态渲染核对） | `taskHistory.ts:75` 保存每次 review 的问题、建议和 report；`TaskRecord.tsx` 逐份渲染，最后一次默认展开。真实事件夹具的两份审查、首份建议和各份正文断言通过；只保留最后审查的变异失败。实际查看 ui/06，能看到两次审查入口。未在本轮操作 UI 展开第一份报告。 |
| F6：产品页无条件承诺分屏 | PASS（原问题） | `docs/index.html:55` 已区分有会话时的窗格与无会话时的整页记录，原来的无条件标题已移除；与 renderer 的两种展示分支方向一致。没有打开产品页运行交互演示。工作台 README 还有不同步措辞，见 R5；当前刷新缺陷也限制了产品页在时序变化中的兑现。 |

## 确定问题

### R1 · P2：已回收任务留下 saved 空布局，强制刷新仍不会打开新 worker

**位置：`workbench/app/main.ts:759`、`:765`；关联 `workbench/src/store.ts:82`、`workbench/src/panes.ts:2156`。**

具体状态：旧 worker 曾打开窗格，回收时 `archiveThread()` 调用 `forgetOpen()`，留下 opened/closed 历史事件。`hasPaneLayout()` 因为查的是“曾有事件”，仍返回 true；`openPanes()` 此时为空。任务撤销清空当前 attempt 后停在记录页，再成功派发新 attempt。

错误结果：回调即使成功调用 `selectTask(task,true)`，`prepareSelection()` 仍得到 `saved=true, launches=[]`；只有 `!saved` 才创建跟随当前 worker 的默认窗格，所以刷新后还是零窗格。TaskRecord 随导航卸载、重建，新的 attempt 成为首次读取基线，后续轮询也不再触发。用户仍须点侧栏会话才能看新 worker。

证据：附录 A 用生产 OrchestrationStore 的内存事件投影和生产 prepareSelection 函数体重放，输出 `saved:true,panes:[]`；新 attempt 出现前后均为 0 窗格。后台读取接口被模拟，没有启动真实 CLI。静态核对确认真实回收会写出同样的 closed 布局事件。现有 ui/07 的 claim 不涉及曾打开并回收的 worker，不能覆盖此路径。

修复方向：在任务视图协调层处理“旧 attempt 的已存空布局 → 新 attempt”，让刷新实际纳入新 worker；同时保留用户对当前 attempt 主动关闭窗格的意图，不能仅把所有 saved 空布局无条件替换。复验曾打开旧 worker → 回收/撤销 → 停留记录页 → 真实派发新 worker。

### R2 · P2：新 attempt 在首次 taskHistory 读取前出现，会永远被当成基线

**位置：`workbench/app/TaskRecord.tsx:26`；关联 `workbench/app/main.ts:752`、`:765`。**

具体时序：prepareSelection 读取到 `current_attempt=null`，准备零窗格；在 TaskRecord 首次 taskHistory 读取前，后台已经派发新 attempt A。首次响应包含 A。

错误结果：代码只把 A 写入 `firstAttempt.current`，不发通知；以后轮询仍是 A，始终不会调用 onAttemptStarted。任务页显示已认领等新状态，却一直不出现 worker。不是多等一个轮询周期就能恢复。

证据：附录 B 执行生产 effect 函数体，连续三次轮询；正常 null → A 发出 1 次刷新，首读即 A 发出 0 次刷新。这里模拟 hooks 和接口，证明分支行为；未声称真实 Electron 时序实测。

修复方向：比较“当前视图实际绑定的 attempt/窗格”和门禁返回值，首次响应也应能发现视图落后。复验在 prepareSelection 与第一次 history 响应之间派发，且此后不再更换 attempt。

### R3 · P2：轮询永久保留初次挂载的 busy=true 回调，加载完成后仍无法刷新

**位置：`workbench/app/TaskRecord.tsx:27`、`:33`；关联 `workbench/app/renderer.tsx:727`、`:763`、`:775`、`:1121`。**

具体时序：以任务视图启动窗口或重载 renderer，初始 `refresh()` 先取得 selection 并设置 selectedTask，然后等待较慢的 sidebar。TaskRecord 此时可以挂载，因为其显示条件只排除 navigating，未排除 loading；它收到的 onAttemptStarted 闭包中，navigate 的 busy 为 true。sidebar 返回后 loading=false，父组件虽传入了新回调，但 effect 依赖只有 `[task]`，轮询仍调用旧回调。

错误结果：后来新 attempt A 出现，旧 navigate 执行 `if (busy) return`，没有发 IPC。TaskRecord 已先将 firstAttempt 改成 A，以后不会重试，页面永久停在零窗格。

证据：附录 B 按 `[task]` 的依赖语义模拟重渲染，并执行生产 navigate 函数体。初次 busy=true、随后 busy=false 的场景在三次轮询后仍为 `refreshRequests:0`。这不依赖并发写入或错误后台；本轮未启动 Electron 重现 sidebar 延迟。

修复方向：轮询使用最新的回调/导航状态，并在视图刷新真正完成前保留待处理的 attempt。仅将回调加入依赖可能因父组件每次渲染都创建新函数而不断重启读取，需连同调用方一起处理。复验“初始 sidebar 延迟 → 加载完成 → 派发”，以及创建终端/导航忙碌期间出现新 attempt，确认不会吞通知或抢回用户已选择的页面。

### R4 · P2：把上一个显示步骤的失败当作本次 verify 的重复失败，仍隐藏独有错误

**位置：`workbench/src/gates/taskHistory.ts:71`、`:72`。**

具体输入：同一 submitted attempt 下，先误执行 integrate，门禁拒绝 `not_verified`；随后 verify 在真实 Git 边界失败，产生 `command_intent`、`command_result` 和 `rejected {input:{command:'verify'},error:'git_failed'}`。

错误结果：最后显示的步骤仍是前一次 integrate 的“门禁拒绝”（passed=false），本次 verify 的唯一失败原因被折叠。页面只告诉用户不能集成，完全不告诉用户验收因为 Git 失败而无法开始。两个错误没有重复关系。代码既没检查 previous 是失败检查类型，也没核对同一次验证，更没有要求原始事件紧邻；被过滤的 command 事件还扩大了错误折叠范围。

证据：附录 C 经生产 `A2AGates.call()`、真实只读 Git 子进程、内存 SQLite 重放：两个调用依次返回 `not_verified`、`git_failed`；原始事件有两条 rejected，task_history 只有 integrate 的一条。仅任务操作锁替换为无副作用占位。相同缺陷也会藏掉 merge_failed 后收集冲突信息时另行发生的 Git 错误（后者仅静态核对，未注入）。

修复方向：仅在同一次 verify 已有充分表达该拒绝原因的结构化事件时去重；不能用任意失败展示步骤作为去重凭据。复验独立拒绝 → 早期 verify 失败、正常检查失败 → 对应重复拒绝、合并失败后额外 Git 失败三个不同序列。

### R5 · P3：README 仍把所有 verify 拒绝描述为隐藏

**位置：`workbench/README.md:1092`。**

具体输入：验收开始前独立发生 verify/git_failed，且前面没有失败步骤。现有测试确认它会显示在时间线；README 却仍写“草拟任务卡、查状态和 verify 被拒这几类……拒绝不进时间线”。修复 R4 后，这条无条件说明还会更不准确。

影响：当前使用说明误述门禁记录的过滤范围。“没有当前 attempt”与实现使用的“没有打开窗格”也不是同一条件；“最近一次审查”未说明已有逐次报告入口。应同步这一段，准确表述显示条件、完整审查列表及有限去重规则。`docs/index.html` 的 F6 修改本身已纠正原问题，不需要重做整站。

## 刷新循环、已有窗格和导航并发

- **未发现必然无限刷新，局部探针 PASS。** 正常 null → 新 attempt 在三轮观察中只通知一次；`firstAttempt` 在调用回调前更新，导航时 TaskRecord 又会卸载。R1/R2/R3 的确定结果是漏刷，不是已证实的循环。
- **已有窗格时误触发：已查调用方，未发现。** `renderer.tsx:1129` 的 docked TaskRecord 不传 onAttemptStarted；只有零窗格版本传回调。因此 docked 轮询发现新 attempt 不会自行重选任务。未实测全部窗格操作组合。
- **离开页面后的迟到响应：局部探针 PASS。** effect 清理置 mounted=false、清理 timer；卸载后完成的请求没有调用回调，见附录 B。
- **与 navigate 并发：不能判为完整 PASS。** 主进程 `main.ts:498` 在 refresh=true 前仍检查 switching/creating/closing，未发现本次补丁绕开操作互斥。渲染器的旧闭包问题见 R3；它也不能保证在后续忙碌状态下使用最新 busy。未运行真实跨 IPC 的重叠导航、排队响应、创建终端和崩溃重载试验，不宣称这些全都安全，也不把潜在竞态写成已发生的错误导航。

按 Deep modules 检查，task_history 作为同一事件表的只读投影是合理边界；本轮未发现新增第二套可变门禁、吞异常或自动重试路径。问题集中在视图协调和投影语义，无需新增平行 API 或兼容层。

## 两条验收的证据判定

1. **“已回收的票点进去不是空页”：INCOMPLETE。** T-138 真实导出事件的纯投影检查通过，包含回收且没有虚构集成；ui/03 支持关闭任务的整页记录，ui/06 支持注入真实历史事件的 T-2 渲染。但这不是一张经真实派发、检查、审查、集成/打回和回收的任务，从同一实际状态库进入记录页的完整入口证明。RESULTS 明说 T-2 只注入事件，任务当时仍 ready、未写相应 attempts；ui/07 又只是 claim、窗格“尚未启动窗格”。本轮没有操作用户 a2a+T-138 或真实 CLI。因此内容投影已有支持，真实回收任务的状态/布局/记录一致性尚未完成验收；R1～R3 还阻断回收后再派发的跟随旅程。
2. **“关闭后任务格显示已关闭”：PASS（现有隔离证据范围）。** 实际查看 ui/01 的任务格“已关闭”；`green2-tasks-beta.json` 中 beta+T-1 仍为 closed，renderer 任务格通过 gateStateNames 显示 closed 的中文名；`green2-history-beta.json` 有关闭理由。本轮 F1 重放支持已查变更入口不再重开。没有重新打包或操作 UI，截图与当前构建产物的绑定没有独立重建，不将此局部 PASS 扩大为当前候选完整 UI 验收 PASS。

建议补一条 **Tracer bullet**：真实入口打开已回收的旧任务记录 → 停留时派发新 worker → 有实际红态/规则检查 → 审查打回、修复、再审 → 回收 → 从任务格重入记录 → 关闭 → 任务格及页内均显示已关闭。保留同一任务/attempt、构建版本、入口输出与截图，并分别覆盖首次读取和初始 loading 的两个时序。报告不代替这条实际验收。

## 已重放的现有检查与证据限制

环境为 Node `v26.5.0`。从仓库根目录运行：

```sh
node evidence/2026-10-27-batch28/T-192/history_check.ts
python3 /Users/luckye/.agents/skills/project-map/scripts/project_map.py status --root /Users/luckye/Documents/Code/a2a
```

history_check 退出 0、PASS。地图检查开始、结束均退出 0：Problems(0)、Stale living docs(0)；这不能替代实际文案核对。

**六个变异全部重放，均被业务断言检出：** integration-c、no-quiet、no-reclaim、last-review-only、drop-all-verify、no-rule-check，各退出 1。最后一个仍能证明规则检查不可被删，但这六个变异不能检出 R1～R4。当前测试只有“此前无失败的早期 verify”反例，没有“此前另一次操作失败”的反例，也没有视图生命周期测试。

原 `mutants.sh` 实际会向当前目录写六个 JSON，并非完全只读。本轮将脚本的结果重定向移除，把 history_check 路径改为绝对路径，在内存中交给 bash 执行，保留其原始 sed 变异和退出结果；未覆盖既有证据。可重复命令如下，结果直接打印到终端（脚本原有临时目录会自行清理）：

```sh
python3 - <<'PY'
from pathlib import Path
import subprocess, re, json
r = Path('/Users/luckye/Documents/Code/a2a')
s = (r/'evidence/2026-10-27-batch28/T-192/mutants.sh').read_text()
s = s.replace('node history_check.ts', 'node '+str(r/'evidence/2026-10-27-batch28/T-192/history_check.ts'))
s = s.replace('> "history-check-$1.json"', '')
p = subprocess.run(['bash'], input=s, text=True, capture_output=True, cwd=r)
for m in re.finditer(r'(\{\n "status":.*?\n\})\n([^\n]+)', p.stdout, re.S):
    d = json.loads(m[1]); print(m[2], d['status'], d['failures'])
print('wrapper exit:', p.returncode, 'stderr:', p.stderr)
PY
```

原先首轮的三个手工变异输出及零字节文件已被实施者删除，RESULTS 如实承认；本轮没有找回这些文件，不能把现有六个重建输出说成保留了旧失败证据。`green2-history-beta.json` 修正了旧 green-history 的过滤版本不一致问题，但不补足真实回收 UI 旅程。

本轮探针的两次 TS 提取脚本初稿因未正确剥离类型而退出 1；另一次把变异输出重定向到 `/dev/stdout` 被环境拒绝。这些是探针搭建失败，修正后才取得本文结果，不算产品红态或变异检出。未删除既有异常证据。

没有执行完整 build、真实 worker/reviewer、真实 socket/IPC 全旅程、并发锁竞争、崩溃恢复、读屏或性能测试。ui/01、03、06、07、08 已实际查看；本轮未重新查看 ui/02、04、05，不以它们的画面增加独立证据。

## 附录 A：回收后的已存空布局

以下命令均从仓库根目录运行。输入、输出保存在本报告，所有数据库只在内存中；附录 A/B 对后台接口或 hooks 的模拟仅证明所列局部控制流。

```sh
node --input-type=module <<'JS'
import { readFileSync } from 'node:fs';
import { stripTypeScriptTypes } from 'node:module';
import { DatabaseSync } from 'node:sqlite';
import { OrchestrationStore } from './workbench/src/store.ts';
const s = readFileSync('workbench/app/main.ts','utf8');
const region = (a,b) => s.slice(s.indexOf(a),s.indexOf(b,s.indexOf(a)));
const code = [region('function mapLayout(', '// A task arrangement'),
  region('async function taskPaneLayout(', 'async function serializedArrangement('),
  region('function restoreArrangement(', '// New terminals start'),
  region('async function prepareSelection(', 'export async function run(')].join('\n');
const store = Object.create(OrchestrationStore.prototype);
store.db = new DatabaseSync(':memory:');
store.db.exec('CREATE TABLE launch_records(id TEXT PRIMARY KEY,task TEXT,attempt TEXT,data TEXT);CREATE TABLE orchestration_events(seq INTEGER PRIMARY KEY,time TEXT,type TEXT,launch TEXT,task TEXT,attempt TEXT,data TEXT);');
const id = 'review2+T-1';
store.launch({id:'old-worker',task:id,attempt:'old-attempt',project:'review2'});
store.event('pane_layout_opened',{position:0},{id:'old-worker',task:id});
store.event('pane_layout_closed',{},{id:'old-worker',task:id});
let task = {task_id:id,project_id:'review2',current_attempt:null};
const request = async (_,q) => q.command === 'workbench_snapshot' ? {ok:true,task} :
  {ok:true,saved:store.hasPaneLayout(id),panes:store.openPanes(id),arrangement:null};
const prepare = new Function('request','randomUUID',stripTypeScriptTypes(code)+';return prepareSelection;')(request,()=> 'pane-key');
console.log('layout',JSON.stringify({saved:store.hasPaneLayout(id),panes:store.openPanes(id)}));
console.log('before',(await prepare({state:'unused',task:id})).panes.length);
task = {...task,current_attempt:{attempt_id:'new-attempt'}};
console.log('after',(await prepare({state:'unused',task:id})).panes.length);
store.db.close();
JS
```

退出 0：`layout {"saved":true,"panes":[]}`、`before 0`、`after 0`。

## 附录 B：首次读取、旧闭包、卸载保护

```sh
node --input-type=module <<'JS'
import {readFileSync} from 'node:fs';
import {stripTypeScriptTypes} from 'node:module';
const s=readFileSync('workbench/app/TaskRecord.tsx','utf8');
const body=s.slice(s.indexOf('  const firstAttempt ='),s.indexOf('  if (error)'));
const code=stripTypeScriptTypes('function observe({task,onAttemptStarted}){'+body+'}')+';return observe;';
const r=readFileSync('workbench/app/renderer.tsx','utf8');
const nav=stripTypeScriptTypes(r.slice(r.indexOf('  const navigate ='),r.indexOf('  const selectTask =')));
const flush=async()=>{for(let i=0;i<6;i++)await Promise.resolve();};
async function scenario(name,initialAttempt,mountBusy){
  let attempt=initialAttempt,timer,ref,deps,cleanup,calls=0;
  const api={a2a:{taskHistory:async()=>({task:{current_attempt:attempt?{attempt_id:attempt}:null}})}};
  const effect=(fn,next)=>{if(!deps||next[0]!==deps[0]){cleanup?.();deps=next;cleanup=fn();}};
  const observe=new Function('useRef','useEffect','setLoaded','setError','window','setInterval','clearInterval',code)(
    ()=>ref??=({current:undefined}),effect,()=>{},()=>{},api,fn=>{timer=fn;return 1;},()=>{});
  const navigateFor=busy=>new Function('busy','setNavigating','setNavigationError','applySelection','setPage',nav+';return navigate;')(busy,()=>{},()=>{},()=>{},()=>{});
  const callback=busy=>()=>{void navigateFor(busy)('打开新会话',async()=>{calls++;return null;});};
  observe({task:'p+T',onAttemptStarted:callback(mountBusy)});await flush();
  observe({task:'p+T',onAttemptStarted:callback(false)});
  attempt='new';for(let i=0;i<3;i++){await timer();await flush();}
  console.log(JSON.stringify({name,refreshRequests:calls,observedAttempt:ref.current}));cleanup();
}
await scenario('normal',null,false);
await scenario('new-before-first-read','new',false);
await scenario('mount-busy-then-idle',null,true);
let resolveRead,cleanup,cleaned=false,callbacks=0;
const observe=new Function('useRef','useEffect','setLoaded','setError','window','setInterval','clearInterval',code)(
  ()=>({current:null}),fn=>{cleanup=fn();},()=>{},()=>{},
  {a2a:{taskHistory:()=>new Promise(r=>{resolveRead=r;})}},()=>1,()=>{cleaned=true;});
observe({task:'p+T',onAttemptStarted:()=>callbacks++});cleanup();
resolveRead({task:{current_attempt:{attempt_id:'late'}}});await flush();
console.log(JSON.stringify({name:'late-after-unmount',callbacks,cleaned}));
JS
```

退出 0。三个场景的 refreshRequests 依次为 **1、0、0**，observedAttempt 均为 new。卸载后的 callbacks=0、cleaned=true。该探针没有渲染 DOM，也没有模拟完整 React 调度器；它保留了本问题依赖的 `[task]` effect 复用和闭包语义。

## 附录 C：真实门禁拒绝被误折叠；关闭入口复验

```sh
node --input-type=module <<'JS'
import { DatabaseSync } from 'node:sqlite';
import { readFileSync } from 'node:fs';
import { A2AGates } from './workbench/src/gates/core.ts';
const g=Object.create(A2AGates.prototype);g.db=new DatabaseSync(':memory:');
g.db.exec('CREATE TABLE tasks(id TEXT PRIMARY KEY,data TEXT);CREATE TABLE attempts(id TEXT PRIMARY KEY,data TEXT);CREATE TABLE verifications(id TEXT PRIMARY KEY,data TEXT);CREATE TABLE events(seq INTEGER PRIMARY KEY,time TEXT,task TEXT,attempt TEXT,type TEXT,details TEXT);');
g.operationLock=()=>({close(){}});
const base=JSON.parse(readFileSync('evidence/2026-10-27-batch28/T-192/green-close.json','utf8')).task;
g.db.prepare('INSERT INTO tasks VALUES (?,?)').run(base.task_id,JSON.stringify(base));
for(const command of ['revoke','revise','claim']){
  const r=await g.call({command,task:base.task_id,reason:'review2',spec_rev:2,owner:'review2'});
  console.log(command,r.ok,r.error,JSON.parse(g.db.prepare('SELECT data FROM tasks WHERE id=?').get(base.task_id).data).state);
}
g.runtime={};
console.log('dispatch',JSON.stringify(await g.call({command:'dispatch',task:base.task_id,runtimeMode:'approval-required'})));
g.runtime=undefined;
// 现有非 Git 目录，令真实只读 rev-parse 失败；不执行 Git 写操作。
const t={...base,task_id:'review2+T-1',project_id:'review2',state:'submitted',
  repo:'/private/tmp/t192-review2',candidate_commit:'a'.repeat(40),
  current_attempt:{task_id:'review2+T-1',attempt_id:'sentinel-attempt',fence:base.fence,spec_rev:base.spec_rev}};
g.db.prepare('INSERT INTO tasks VALUES (?,?)').run(t.task_id,JSON.stringify(t));
for(const command of ['integrate','verify']){
  const r=await g.call({command,task:t.task_id});console.log(command,r.ok,r.error);
}
const raw=await g.call({command:'events',task:t.task_id});
const h=await g.call({command:'task_history',task:t.task_id});
console.log('raw',JSON.stringify(raw.events.map(e=>({type:e.type,error:e.details.error}))));
console.log('steps',JSON.stringify(h.history.steps));g.db.close();
JS
```

本轮分别执行关闭入口和误折叠检查，均退出 0，结果：revoke/revise/claim 为 `false task_closed closed`，有 runtime 的 dispatch 为 `false task_closed`。integrate 为 `false not_verified`，verify 为 `false git_failed`。原始事件依次为 rejected/not_verified、command_intent、command_result、rejected/git_failed；投影只剩 `integrate：not_verified`。此输入的预期来自“独立的新失败应可读”这一契约，不来自实现输出。

## 后续检查应放在哪里

同类问题 F2/F3 已重复出现。应在工作台任务视图的真实入口验收中加入 R1～R3 的时序和已存布局用例；在现有 history_check.ts 中加入“前一失败属于不同操作”和“同次 verify 发生额外失败”的独立断言，并用当前候选作为已知坏实现确认会失败。真实入口证据须保留命令、输出和截图；纯投影用例不能替代它。只读审查没有修改测试、票或地图。

**最终结论：需修复。**
