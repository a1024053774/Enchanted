# T-199 独立审查

STATUS: INCOMPLETE

TARGET: `/private/tmp/t199-review/change.diff`，基于仓库 HEAD `606a5e193db81e0accc7781a93e6b44dca74e272`。开始及收尾核对时，仓库 `workbench/src/panes.ts` 的工作区 diff 与该补丁逐字节一致；审查只针对这份补丁，不包含其他已有脏文件。

根因判断成立，候选能修复所述序列化问题；当前没有发现另一条可达的非整数尺寸生产路径。但是，所给红绿证据没有记录运行代码版本、构建来源和复现命令，尚不能确认红态来自未修代码、绿态来自本候选。因此本次不出具真实入口验收通过结论。

## FINDINGS：需处理的问题

### 1. [P2，阻断验收] 红绿证据未绑定运行代码，无法确认反事实和候选复验

- **位置：** `evidence/2026-10-27-batch28/T-199/red-pane-status.json:1`、`green-pane-status-gone.json:1`、`green-pane-status-live-shell.json:1`；同目录 `ui/01-red-integer-error.jpg`、`ui/02-green-gone-pane-readonly.jpg`。
- **失败场景：** 若红态来自未知构建、绿态来自另一份本地代码，现有文件仍会呈现同样的 `{}`、`null` 和成功截图；审查无法据此验证“未修版本经真实入口失败、本候选经同一入口恢复”。这不是认定证据造假，而是候选归属无法核对。
- **已查事实：** 目录共有 10 个文件，只有 JSON 响应和两张截图，没有执行脚本、完整命令、退出状态、后台/应用启动与重启记录、运行源码或构建版本清单。`red-dispatch.json` 中的 `base_commit` 属于被派发的 lcu 任务，不能当作工作台后台版本。
- **最小处理：** 保留现有证据，补充可复现步骤及运行版本绑定；如无法补出原运行的来源记录，在新的隔离环境对明确的未修版本和本候选各运行一次：创建 worker/reviewer → 后台重启并确认原进程消失 → 读取 `pane_status` → 打开同一窗格核对错误消失且输出可见。另保留活终端尺寸正例。记录命令、输出、退出状态、源码版本及应用/后台实际使用路径。不要事后把现有文件标成已完成版本核验。

### 2. [P3，非阻断] 前端快照类型没有声明新增的 `null` 值

- **位置：** `workbench/app/renderer.tsx:55`，对应生产者 `workbench/src/panes.ts:1603`。
- **失败场景：** 后台返回 `size: null` 时，实际响应不符合 `size?: { cols: number; rows: number }` 的声明。当前两个运行时读取点能处理 null，但类型使用者会被告知“存在时一定是尺寸对象”，无法准确表达这条恢复路径。
- **最小处理：** 将声明改为 `size?: { cols: number; rows: number } | null`。这是接口描述同步；未发现它在现有读取点造成运行时崩溃。

## EVIDENCE：根因与其他路径

**PASS（静态链路及隔离逻辑）。** `registerGone` 在 `workbench/src/panes.ts:600` 开始，核对记录的 shell、leader 进程已消失后，于 `:616` 创建 `pty: { pid: shell }`，没有 `cols/rows`。旧 `status()` 将二者直接放进对象，JSON 序列化时两个 undefined 属性都被省略，得到 `{}`。

`workbench/src/daemon.ts:809`、`:819` 将 `status()` 分别交给工作台快照和 `pane_status`。`renderer.tsx:347` 中的 `?? null` 不会消除 `{}`；只读分支在 `:259` 把它当成尺寸，`:260` 调用 `term.resize(undefined, undefined)`。所安装 xterm 6.0.0 的 `src/browser/public/Terminal.ts:147`、`:260` 会校验整数并抛出所述错误。读取循环在 `renderer.tsx:380` 捕获后结束，输出读取未能继续。这与红态截图一致。

其他尺寸来源已查：

| 路径 | 位置 | 结果 |
| --- | --- | --- |
| 普通 shell 创建 | `panes.ts:297` | node-pty，初始 `160×45` |
| 主控创建 | `panes.ts:437` | node-pty，初始 `160×45` |
| 会话恢复 | `panes.ts:665` | node-pty，初始 `160×45` |
| worker/reviewer/monitor 创建 | `panes.ts:900` | node-pty，初始 `160×45` |
| PTY 尺寸更新 | `daemon.ts:669` | 两维均须为整数且在范围内；停止、归档、失败或关闭中的窗格拒绝更新 |
| node-pty 尺寸保存 | `node_modules/node-pty/lib/unixTerminal.js:51`、`:249` | 初始化两维；成功 resize 后保存两维；退出/关闭未清空尺寸 |

已搜索 `workbench/src`、`workbench/app` 中 PTY 赋值、尺寸赋值和 resize 调用；没有发现另一条生产写入路径把尺寸改成非整数。**这个结论限定于已查代码和本机安装的 node-pty 1.1.0，不是对未来改动或任意对象损坏的保证。**

不能改成简单的 `pane.stopped ? null : ...`：正常退出的真实 PTY 对象仍保留尺寸，只读重放仍会使用它。隔离正例确认候选保留这种情况的尺寸。

## 修复层次判断

`status()` 拥有“内部窗格如何表示为外部快照”的责任，因而在此把“没有终端尺寸”表示为 `null` 是合适的修复层次。给 `registerGone` 填造出的 `160×45` 会谎报终端尺寸；在前端吞掉 resize 异常也会绕开根因，两者都不应采用。

**对本候选：未确认存在项目规则禁止的吞异常、重试或兼容路径。** 新代码没有新增异常边界；结构扫描也未报告新增异常处理。当前可达对象中，四条真实 PTY 路径都有整数尺寸，只有 `registerGone` 的替身没有尺寸，因此这个分支在当前代码里承担的是两种内部状态的序列化。不能仅因使用条件表达式，就将其定性为有害 fallback。

不过，`Number.isSafeInteger(cols)` 不是“没有终端”的精确领域表达：它也会把假设中的活 PTY 非整数列数正常化为 null，而且不检查 rows。该假设不由已查生产路径产生，故不列为已确认运行缺陷，也不建议再叠加通用校验兜底。

若调整内部表达，优先在 `registerGone` 构造时显式标记“没有终端”，再由 `status()` 据此输出 null；标记应只覆盖替身，保留已停止真实终端的尺寸。不要为了这一处增加包装层、平行 API 或兼容实现。按 **Deep modules**，这些浅层接口没有收益；按 **Ubiquitous language**，应区分“进程已停止”和“没有终端”。本次没有实施任何重构，显式标记属于设计改进建议，不单独阻断当前补丁。

## `size: null` 的读取方

**PASS（静态）；界面运行结果仅限提供的截图。** 生产读取点已搜索，尺寸对象只在以下两处直接消费：

- `renderer.tsx:347`、`:255`：null 跳过固定 PTY 尺寸分支，使用 FitAddon 适配本地显示。`writable` 为 false 时不会执行 `:267` 的后台 resize。后台 `lifecycle: interrupted` 经 `app/main.ts:523`、`:540` 得到 `input_enabled: false`，`renderer.tsx:346` 仍禁用输入。
- `renderer.tsx:538`：`data-readonly` 变为 false。这个属性控制 `style.css:173`、`:174` 的固定终端尺寸滚动布局，不控制输入权限。没有 PTY 尺寸时恢复容器布局与 FitAddon 分支相符；标题的“只读”仍由 `renderer.tsx:472` 的输入权限控制。

因此，`data-readonly=false` 不会把替身变成可写窗格。后台对停止窗格的 resize 拒绝也保留。没有查出其他生产代码直接解引用 `pane.size.cols/rows`。测试中的尺寸读取如 `test_t175_terminal_glyphs_e2e.py:96`、`:113` 针对该测试创建的活 shell，并不覆盖替身。

限制：null 情况没有可用的原 PTY 尺寸；本次没有核验任意 ANSI/TUI 历史输出在不同容器宽度下的完整重放保真，也没有实际运行 FitAddon、滚动和窗口缩放场景。

## 红绿证据与反例

| 检查 | 状态 | 实际证明范围 |
| --- | --- | --- |
| 红态状态和截图 | INCOMPLETE | JSON 为 `{}`；截图确实显示整数 API 错误，但未确认未修代码的运行来源 |
| 已消失窗格绿态 | INCOMPLETE | 同一 thread、launch、shell pid；size 从 `{}` 变成 null，截图有终端输出且无原错误；未绑定本候选运行版本 |
| 活 shell 正例 | INCOMPLETE | start/status 的 launch、thread 一致，status 为 `running`、`stopped:false`、`160×45`；覆盖该次活 shell 的状态尺寸，未证明界面输入/动态 resize 全部不受影响 |
| 反事实隔离逻辑 | PASS，L1 | HEAD 的真实 `status()` 方法返回 `{}`，不满足“无终端为 null”；当前方法满足 |
| 非默认尺寸及停止真实终端 | PASS，L1 | 输入 `103×29` 时，活状态及停止状态均保留该尺寸；相应断言可区分“所有 size 都返回 null”和“所有 stopped 都返回 null”的错误实现，但未另行运行这两种变异 |
| 实际 xterm 整数校验 | PASS，L1 | 安装包对 undefined/undefined 抛出同一错误，对 `103×29` 接受；没有打开 UI |
| 清理响应 | 观察已核对 | revoke/reclaim 返回 ready、current_attempt:null；shell close 返回 ok。没有独立复查运行状态、进程或用户数据，不能由响应推导清理已完全完成 |

隔离检查没有启动后台、PTY、socket 或应用，也没有调用模型。它补足了逻辑层反事实和尺寸变化的哨兵输入，**不能替代 L3 真实入口的版本绑定和复验**。本次范围是恢复状态与终端交互表面；模型理解、检索、跨租户和外部业务写入验收不适用。

## 本次执行及限制

- 只读检查源码、依赖实现、已有测试和指定证据；查看两张原始截图。未修改仓库、未 checkout/切分支，未操作 `/private/tmp/t190` 后台或应用，未访问 `~/Library/Application Support/a2a-orchestrator`。
- 结构扫描命令：`python3 /Users/luckye/.agents/skills/design-integrity-review/scripts/design_integrity.py --cwd /Users/luckye/Documents/Code/a2a --format json`，退出 0，`findings: []`。静态扫描没有替代上述调用链审查。
- session 开始和结束均运行项目地图 status。结束命令：`python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root /Users/luckye/Documents/Code/a2a`，退出 1：结构问题 0，`workbench/README.md` 因未提交的 `panes.ts` 改动被标 stale。未在只读审查中更改文档或 Verified；自动 stale 提示本身不能证明文档内容已错误。
- 未运行构建、完整回归或真实 Electron 重启测试；未把历史 T-168 等测试通过结论用于当前候选。没有读取实现者会话来补足证据来源。

隔离检查的完整命令如下；实际退出状态为 0（Node v26.5.0）。重放前须保持本报告所指 HEAD 和候选 diff 不变。

```sh
node --input-type=module <<'JS'
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { isDeepStrictEqual } from 'node:util';
import { Panes } from '/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts';
const repo = '/Users/luckye/Documents/Code/a2a';
const record = { id: 'review-launch', thread: 'review-thread', role: 'reviewer' };
const store = { threadLaunch: () => record, lastEvent: () => null };
const panes = new Panes('/private/tmp/t199-review', store, {}, () => {});
const parentSource = execFileSync('git', ['show', 'HEAD:workbench/src/panes.ts'], { cwd: repo, encoding: 'utf8' });
const begin = parentSource.indexOf('  status(thread: string) {');
const end = parentSource.indexOf('\n  async signal(', begin);
if (begin < 0 || end < 0) throw new Error('status extraction failed');
const parentStatus = new Function('return ({' + parentSource.slice(begin, end).replace('status(thread: string)', 'status(thread)') + '}).status')();
const rows = [];
for (const [label, pty, stopped, expected] of [
  ['gone', { pid: 12345 }, true, null],
  ['live-sentinel', { pid: 12345, cols: 103, rows: 29 }, false, { cols: 103, rows: 29 }],
  ['stopped-real-terminal', { pid: 12345, cols: 103, rows: 29 }, true, { cols: 103, rows: 29 }]
]) {
  panes.panes.set(record.thread, { record, pty, stopped, failed: null, active: null, queue: [] });
  const actual = panes.status(record.thread).size;
  const parent = parentStatus.call(panes, record.thread).size;
  rows.push({ label, actual, expected, pass: isDeepStrictEqual(actual, expected), parent: JSON.parse(JSON.stringify(parent)), parentPass: isDeepStrictEqual(parent, expected) });
}
const require = createRequire(repo + '/workbench/package.json');
const { Terminal } = require('@xterm/xterm');
const term = new Terminal({ cols: 160, rows: 45 });
let badResize;
try { term.resize(undefined, undefined); badResize = 'unexpected success'; }
catch (e) { badResize = String(e); }
term.resize(103, 29);
console.log(JSON.stringify({ level: 'L1 isolated logic; no daemon, socket, PTY or UI started', rows, actualXterm: { badResize, validResize: { cols: term.cols, rows: term.rows } } }, null, 2));
term.dispose();
if (!rows.every(row => row.pass) || rows[0].parentPass || !badResize.includes('This API only accepts integers')) process.exitCode = 1;
JS
```

该命令的原始标准输出如下，标准错误为空：

```json
{
  "level": "L1 isolated logic; no daemon, socket, PTY or UI started",
  "rows": [
    {
      "label": "gone",
      "actual": null,
      "expected": null,
      "pass": true,
      "parent": {},
      "parentPass": false
    },
    {
      "label": "live-sentinel",
      "actual": {
        "cols": 103,
        "rows": 29
      },
      "expected": {
        "cols": 103,
        "rows": 29
      },
      "pass": true,
      "parent": {
        "cols": 103,
        "rows": 29
      },
      "parentPass": true
    },
    {
      "label": "stopped-real-terminal",
      "actual": {
        "cols": 103,
        "rows": 29
      },
      "expected": {
        "cols": 103,
        "rows": 29
      },
      "pass": true,
      "parent": {
        "cols": 103,
        "rows": 29
      },
      "parentPass": true
    }
  ],
  "actualXterm": {
    "badResize": "Error: This API only accepts integers",
    "validResize": {
      "cols": 103,
      "rows": 29
    }
  }
}
```

## RULE：本缺陷的回归检查

建议在现有 `workbench/tests/` 的恢复端到端流程中保存上述“重启后替身状态 + 真实界面输出”场景，并同时保留活终端及停止真实终端的尺寸正例。必须在未修版本上以 `{}` 或整数 API 错误失败，再在绑定版本的候选上通过。该机械检查比再加一条文字规则更能防止同类问题。**Tracer bullet** 应贯通后台恢复、状态响应和前端显示；本次只读审查没有新增或运行这条测试。

结论：**需修复**。阻断项是问题 1 的真实入口证据归属缺口；根因与局部逻辑已得到支持，问题 2 为非阻断的类型契约同步项。补齐前，整体状态保持 **INCOMPLETE**。
