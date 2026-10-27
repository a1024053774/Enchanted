# T-199 独立审查第 2 轮

STATUS: PASS（本候选的只读审查；本轮端到端复跑为 INCOMPLETE，见限制）

TARGET: `/private/tmp/t199-review2/change.diff`，基于 `606a5e193db81e0accc7781a93e6b44dca74e272`。开始和收尾时，仓库中四个候选文件的 `git diff` 均与该文件全文一致；没有追随其他脏文件扩大审查范围。

## FINDINGS

没有发现与本改动相关、可确定的新增问题；没有需要列出严重程度和失败场景的缺陷项。

## EVIDENCE：首轮三点

| 首轮事项 | 本轮核对 | 结果 |
| --- | --- | --- |
| P2：运行证据没有绑定代码版本 | `e2e/green-base-revision.txt` 是上述完整基准版本；`e2e/green-working-tree.diff` 与当前 `panes.ts`、`renderer.tsx`、测试三文件的 diff 全文一致。修前 JSON 的 argv 明确指定 `--revision 606a5e193`；变异 JSON 明确指定 `--mutant gone-size-empty`。最终界面补有 `ui-final-build.txt`，记录基准、源码 diff、打包和启动命令、包内尺寸分支。 | 已处理；新增材料支持候选归属。旧 `ui/01`、`ui/02` 仍只作为现象记录，不追认它们的构建来源。 |
| P3：界面类型没有声明 null | `workbench/app/renderer.tsx:55` 已声明 `size?: { cols: number; rows: number } \| null`。 | 已处理。 |
| 建议显式标记没有终端的替身 | `workbench/src/panes.ts:214` 声明 `gone?: true`；`:618` 只在 `registerGone` 的替身构造中设置；`:1604` 据此返回 null。 | 已处理；不再从尺寸合法性推断领域状态。 |

此处按 **Ubiquitous language** 区分“已停止”和“没有终端”：正常退出的真实 PTY 不因此变成 `gone`。按 **Deep modules**，修改留在内部状态与外部快照的转换处，没有新增包装层、平行 API、异常吞噬或兼容实现。

## EVIDENCE：替身与其他 Pane 使用者

已搜索 `workbench/src`、`workbench/app` 的 `gone`、PTY 创建及尺寸读取路径。`gone` 只有上述构造处写入；普通 shell（`panes.ts:302`）、主控（`:443`）、恢复的真实会话（`:671`）、新建 worker/reviewer/monitor（`:905`）均创建新 Pane，持有真实 PTY，不继承该标记。只有 worker/reviewer 的恢复分支调用 `registerGone`（`:591`、`:599`）；monitor 走 `restore`。

替身持有 `pty: { pid: shell }`、`stopped: true` 的表示在修前版本已经存在；本改动没有引入这种不完整 PTY 对象。逐项核对结果：

| 使用者 | 位置 | 核对结果 |
| --- | --- | --- |
| worker reclaim | `workbench/src/gates/core.ts:4363`、`:4385`；`workbench/src/panes.ts:2138`、`:2150`、`:2167` | `readThread` 对 stopped 替身不再查询进程，只读取 pid 等现有身份字段；`stopThread` 调用 `terminate` 后在 stopped 分支返回，不访问缺失的 `onExit`、`kill`。 |
| reviewer reclaim / archive | `workbench/src/gates/core.ts:2686`；`workbench/src/panes.ts:2156` | 走相同的停止接口；archive 只更新布局、事件和 archived 状态，不调用 PTY 方法。 |
| signal | `workbench/src/daemon.ts:175`、`:827`；`workbench/src/panes.ts:1630`、`:1679`、`:2004` | 外部调用先认证 launch token；替身 token 为空，旧进程的原 token 不匹配。signal 中的 `pane.pty` 直接访问是现有的 pid 字段；`scan` 在 stopped 时直接返回（`:1142`）。未发现因新增 `gone` 或 null 尺寸而引入的方法缺失问题。 |
| 写入与 resize | `workbench/src/panes.ts:1284`、`:1312`、`:1371`；`workbench/src/daemon.ts:672` | 现有 stopped 检查会拒绝替身写入和 resize；没有因显示恢复而放开终端输入。 |

本轮还调用实际 `registerGone`，以不存在的 PID 经真实 libproc 查询创建 reviewer 替身，再调用 `status`、`readThread`、`stopThread`、`archiveThread`，全部通过。该检查使用内存 store，并非完整门禁端到端验收。

## EVIDENCE：三份端到端记录

以下文件均位于仓库 `evidence/2026-10-27-batch28/T-199/`。已读取 JSON、日志和测试执行路径，逐项核对 RESULTS 表格：

| 文件 | 实际记录 | 与表格是否一致 |
| --- | --- | --- |
| `e2e/green.json` | `status: PASS`；21 项检查；重启前 running、160×45，重启后 size null；通过重新派发、集成、monitor 恢复与回收等本场景后续检查。 | 一致。通过范围限 `restart-working` 分支，不表示所有 T-124 变体都跑过。 |
| `e2e/red-606a5e193.json` | 通过前 12 项后，在 `gone_worker_has_no_size` 因 size `{}` 抛 AssertionError；对应日志指向测试第 588 行。 | 一致；是目标缺陷断言失败，非启动或依赖失败。 |
| `e2e/mutant.json` | 通过同样前 12 项后，在同一断言因 `{}` 失败；日志与 JSON 一致。 | 一致；变异只撤销 null 分支。 |

两个反例的 JSON 顶层仍为 `INCOMPLETE`，因为测试只在成功结束时改成 PASS；它们同时保存明确的 AssertionError。这不表示目标反例未触达。日志中的未捕获断言与 RESULTS 所述退出 1 相符，但 JSON 本身没有单独保存退出码字段。

三份记录查询旧 worker 时 lifecycle 都已是 `ended`；自动 run 可以在查询前完成回收归档。这里检查的仍是相同 thread 的替身，其 size 分支不依赖 archived。最终界面另有 `final-pane-status-gone-4.json` 覆盖未归档的 `interrupted` 状态。不能把两种生命周期混写成同一个观测值。

测试的 oracle 来自 T-199 票：已消失窗格没有终端尺寸，活窗格有整数尺寸。`tests/test_t124_controller_e2e.py:572`、`:586` 通过真实 socket 查询同一 worker thread；不是调用生产函数生成期望值。`--revision` 从 Git 提取生产源码到隔离目录，运行的仍是当前测试；`--mutant` 复制源码后只替换唯一命中的尺寸分支（`:65`）。已有反事实确实区分修前和修后；活窗格正例也会拒绝“所有 size 恒为 null”的错误实现。

**Tracer bullet** 的证据链是后台重启恢复 → socket 状态响应 → 界面显示。端到端 JSON 覆盖前两段；界面段依据补充的最终构建记录与截图核对，不把 CLI 测试冒充 Electron UI 测试。

## EVIDENCE：界面与 README

`workbench/README.md:227` 的新增措辞与实现一致：限定在已确认原进程消失、登记 `pane_gone_confirmed` 的 worker/reviewer 替身，其 size 为 null，界面只读显示历史输出；没有把所有 stopped 窗格都称作没有终端。

`renderer.tsx:347` 将 null 保持为无尺寸状态，`:259` 跳过固定 PTY 尺寸 resize，`:263` 使用本地 FitAddon；只有 writable 时才向后台发送 resize（`:265`）。`app/main.ts:523`、`:540` 使 interrupted/ended 窗格保持不可输入。`renderer.tsx:538` 的布局属性不是输入权限开关。

已查看 `ui/03-green-final-build.jpg`：T-2、attempt 前缀 8928eb62，与 `final-dispatch.json` 对应；截图显示只读标记及终端内容，没有整数 API 错误。`final-pane-status-gone-4.json` 的 thread、launch、shell pid、native session 与该派发匹配，size null、stopped true、lifecycle interrupted。构建记录的基准、源码 diff 和包内尺寸分支与本候选相符。

## COUNTEREXAMPLE：本轮独立补充检查

执行下面命令，退出 0。实际 `registerGone` 替身在候选下返回 null，修前 `status` 返回 `{}`；停止、归档可完成。另用非默认尺寸 103×29 验证运行和停止的真实终端形状均保留尺寸，拒绝“所有 stopped 都返回 null”的错误策略。实际安装的 xterm 对 undefined/undefined 抛出原错误，对 103×29 接受。

```sh
node --input-type=module <<'JS'
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { Panes } from '/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts';
const repo = '/Users/luckye/Documents/Code/a2a';
const record = { id: 'review2-launch', thread: 'review2-thread', role: 'reviewer', cli: 'Claude Code', native_session: 'review2-native', worktree: '/private/tmp/t199-review2' };
const events = [];
const store = {
  threadLaunch: () => record, launchRecord: () => record,
  lastEvent: (id, types) => types.includes('pane_started') ? { data: { shell_pid: 2147483647 } } : null,
  event: (type, data) => { events.push({ type, data }); return events.length; }
};
const panes = new Panes('/private/tmp/t199-review2', store, {}, () => {});
await panes.registerGone(record);
const pane = panes.panes.get(record.thread);
assert.ok(pane, JSON.stringify(events));
assert.equal(pane.gone, true);
assert.equal(events.at(-1).type, 'pane_gone_confirmed');
const old = execFileSync('git', ['show', '606a5e193:workbench/src/panes.ts'], { cwd: repo, encoding: 'utf8' });
const begin = old.indexOf('  status(thread: string) {'), end = old.indexOf('\n  async signal(', begin);
assert.ok(begin >= 0 && end > begin);
const oldStatus = new Function('return ({' + old.slice(begin, end).replace('status(thread: string)', 'status(thread)') + '}).status')();
const wire = value => JSON.parse(JSON.stringify(value));
assert.deepEqual(wire(oldStatus.call(panes, record.thread)).size, {});
assert.equal(panes.status(record.thread).size, null);
assert.equal((await panes.readThread(record.thread)).stopped, true);
await panes.stopThread(record.thread);
await panes.archiveThread(record.thread);
assert.equal(panes.status(record.thread).size, null);
assert.equal(panes.status(record.thread).lifecycle, 'ended');
const rows = [{ case: 'actual-registerGone', candidate: null, parent: {}, reclaimed: true, archived: true }];
for (const stopped of [false, true]) {
  panes.panes.set(record.thread, { ...pane, gone: undefined, archived: false, stopped, pty: { pid: 2147483647, cols: 103, rows: 29 } });
  const size = panes.status(record.thread).size;
  assert.deepEqual(size, { cols: 103, rows: 29 });
  rows.push({ case: stopped ? 'stopped-real-terminal-shape' : 'live-terminal-shape', candidate: size });
}
const require = createRequire(repo + '/workbench/package.json');
const { Terminal } = require('@xterm/xterm');
const term = new Terminal();
assert.throws(() => term.resize(undefined, undefined), /This API only accepts integers/);
term.resize(103, 29); assert.equal(term.cols, 103); assert.equal(term.rows, 29); term.dispose();
console.log(JSON.stringify({ status: 'PASS', level: 'L1 plus real libproc missing-PID query; no daemon or UI', rows, xterm: 'undefined rejected; 103x29 accepted' }, null, 2));
JS
```

该检查没有启动后台或 UI。真实终端正例使用对象形状，不是新建 node-pty；不能据此宣称动态 resize、任意 ANSI/TUI 历史重放已经实测。

## LIMITATIONS：本次复跑与边界

本轮从 `workbench` 执行了两条命令，均退出 1，原始摘要保留在审查目录。重放时必须换未使用过的 summary 路径：

```sh
python3 -B tests/test_t124_controller_e2e.py --end restart-working --summary /private/tmp/t199-review2/recheck-green.json
python3 -B tests/test_t124_controller_e2e.py --end restart-working --summary /private/tmp/t199-review2/recheck-red.json --revision 606a5e193
```

两次都仅通过前 7 项检查，在测试第 554 行的 `monitor_reads_but_cannot_write` 提前失败，工具原始结果是 `Exit code 71`、`sandbox-exec: sandbox_apply: Operation not permitted`。均未触达重启或新增尺寸断言，故本轮独立端到端复跑状态为 **INCOMPLETE（环境阻断）**，不能作为候选失败或修前反事实。没有修改测试、移除 sandbox 或再运行同样会被此前置条件阻断的变异。上述 PASS 结论依据已核对的候选源码、现有真实入口证据及补充隔离反事实，不声称本轮重新取得端到端绿态。

没有重新打包或运行 Electron，也没有读取已删除的最终包；包内源码分支依据保存的构建记录，界面结果依据已有最终截图。未核验完整 T-124 所有分支、所有 CLI/reviewer 的真实重启、滚动与缩放、任意历史输出保真；这些均不冒充已查。模型为脚本化接口，本审查不涉及模型理解能力、检索、跨租户或生产业务写入。

开始和收尾的项目地图 status 均退出 0，结构问题 0、stale living docs 0；候选四文件 `git diff --check` 退出 0。未改仓库文件，未 checkout 或切分支，未操作 `/private/tmp/t190` 后台或应用，未访问 `~/Library/Application Support/a2a-orchestrator`。本轮复跑使用独立 `/private/tmp/t124-*` 夹具；脚本收尾后两个夹具的 daemon.pid 均不存在，未据此额外宣称所有子进程都已独立核验退出。

结论：**可合并**。
