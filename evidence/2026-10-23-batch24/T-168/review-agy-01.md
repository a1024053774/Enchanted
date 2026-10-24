# T-168 独立审查 01（agy，PASS）

启动参数：agy --model gemini-3.8-flash-high --mode auto --add-dir /Users/luckye/Documents/Code/a2a-review/T-168-r1 -i "$(cat /Users/luckye/Documents/Code/a2a-review/T-168-r1/prompt.txt)"
# pane wG:p25 started 2026-10-24T07:27:58Z candidate 9c924074651dd0ec817ba8dcdc365a7df24480b4

以下为审查员窗格最终回复原文（去掉边框字符）。

T-168 独立审查报告

• 审查对象：候选提交 9c9240746（基线 a808c1137）
• 审查范围：full.diff（覆盖 workbench/src/panes.
ts、workbench/app/renderer.tsx、workbench/app/style.
css、workbench/README.
md、workbench/tests/test_t168_readonly_size_e2e.py）、candidate/.
project-map/tickets/T-168-readonly-review-pane-overlap.
md、candidate/evidence/2026-10-23-batch24/T-168/ 及外置归档证据
• 审查员身份：Enchanted（a2a）独立只读审查员
•
审查原则：只读检查、写审分离、真实入口证据核对、最小根因层、无吞异常/
无兼容分支/无平行 API
──────
## 一、核心核对结论

### 1. 根因分析与改动深度（最小根因层 / 架构整洁）

• 根因核对：正确且成立。
• 回读 T-164
现场截图（17-reviewer-readonly-no-focus-error.png），切到审查员窗
格时出现严重的文字重叠、残行与黑块。
• 修前 renderer.tsx 的 resize() 无条件调用 fit.fit()，将 xterm
视口物理尺寸调整为容器 DOM 尺寸（如测试夹具中的 154
列或大屏下的更宽列数）；但只读窗格因 writable === false
不会向后台下发 PTY 尺寸重置。后台 node-pty 实际仍保持初始的
160×45。
• CLI（如 Claude Code）在 PTY 内按 160
列计算相对光标重绘（例如光标上移 N 行 \x1b[NA、清屏
\x1b[J、重绘）；当行宽接近或跨越 160 列（如 159 列或 161
列）并在另一视口列数下渲染时，物理折行位置偏移，导致上移行数与逻
辑行不匹配，残存字符未被清除或上位行被误擦除，产生重叠与黑块。
• 改动深度与最小层：
• 改动严格落在拥有层：
1. 后台 panes.ts:1473：在 status() 中为在线活跃窗格透出真实
PTY 几何尺寸 size: { cols: pane.pty.cols, rows: pane.pty.rows
}。
2. 前端 renderer.tsx:234-237：若 !writable &&
ptySize，直接调用 term.resize(ptySize.cols, ptySize.rows) 使
xterm 与 PTY 自身尺寸强一致，不再调用 fit.fit()。
3. 前端样式 style.css:161-162：对 data-readonly="true"
的窗格设置 overflow: auto; display: flex; flex-direction:
column-reverse;
，实现视口较小时允许水平/垂直滚动，且默认对齐并展示最新的最后
一行。

• 坏味道排查：
• 无吞异常、无自动重试、无平行 API。
• 对于无在线 PTY 的场景（如历史已结束 attempt），ptySize 为 null
时自然沿用通用 fit.fit()，并在 RESULTS
中如实列为未覆盖项，未引入虚假 mock 或投机垫片。


### 2. 真实入口与独立 Oracle

• 真实入口测试：
• 测试 test_t168_readonly_size_e2e.py 驱动真实 Electron
客户端（通过 CDP 注入与读取）、真实 a2a 编排后台、真实 node-
pty、真实门禁派发与审查员拉起流程；本地供应商模型请求为 0。
• 测试通过受控 PTY
精确输出了审查员在回放段（Replay，打开窗格前产生）和实时段（Live
，打开窗格后产生）的相对光标重绘转义序列。
• 独立预期来源：
• 预期值直接来自终端 ANSI 标准语义（159 字符在 160 列占 1
行、在较窄下多出残行；161 字符在 160 列折 2
行、在较宽下误擦上一行），预期输出为连续的
_ABOVE、_NARROW_OK、_MID、_WIDE_OK 且残存字符数必须为 0。
• 预期来自规格与终端语义数学推导，绝非照抄被测实现输出。


### 3. 红态复现与变异体核验（Evidence-First Testing）

• 修前红态落点：
• 在基线 a808c1137 上执行 test_t168_readonly_size_e2e.py（证据
red-3、red-4），视口适配为 154 列而 PTY 为 160
列，回放段与实时段均断裂并留下残行（leftovers > 0、consecutive:
false），准确落入 replay_text_not_overlapping 与
live_text_not_overlapping 断言，red_reproduced=true。
• 早期因测试脚本夹具等待与 \r\n 格式问题导致的 red-1、red-2
失败记录已在 CHECKS.json 和 RESULTS.md 中完整保留，无抹除涂改。
• 已知坏实现（变异体）：
• 变异体 1（readonly-fits-
view）：模拟只读窗格继续强制适配容器宽度（if (false &&
ptySize)）。运行 t168-mutant-fits-view.json 精准在
replay_text_not_overlapping 和 live_text_not_overlapping
失败，保留了带 NNNN...
残行的截图（t168-mutant-fits-view-live.png）。
• 变异体 2（readonly-resizes-pty）：模拟只读窗格试图向后台下发
PTY resize 请求。运行 t168-mutant-resizes-pty.json
触发后台门禁拒绝，UI 弹出黄色错误横幅 Window is not available for
input，在文字重叠和无错误断言上双重失败（截图：t168-mutant-resize
s-pty-live.png）。
• 两个变异体均代表真实的缺陷/坏实现，且均被有效拒绝。


### 4. 关键专项核对（用户重点指示项）

1. 只读窗格是否因此改变了被查看程序的环境：
• 否，绝对没有改变。renderer.tsx:234-237 处理 !writable &&
ptySize 时直接 return，不调用 window.a2a.resize；PTY 的真实
cols/rows 始终为 160×45，子进程未收到 SIGWINCH。测试断言
reviewer_pty_size_unchanged 在 green 运行中稳定通过（pane.size ==
{cols: 160, rows: 45}）。
2. 可写窗格是否发生回归：
• 否。可写窗格因 writable === true，不进入 !writable 分支，继续由
fit.fit() 计算并在尺寸变化时下发 window.a2a.resize；data-readonly
为 false，样式保持原有伸缩布局。
•
包含可写窗格焦点、输入、分屏及布局的完整回归套件全部通过：t161（
可写主控/worker 焦点）、t139-t143（视图保留与性能）、t143-
focus、t139-layout、t139-selection、t091 全部
PASS（详见外置盘归档 exits.txt）。
3. T-161 只读焦点有无回归：
• 否。端到端测试显式断言
reviewer_readonly_no_focus_no_error（input: "false", errors: [],
focused: false）。回归套件中的 test_t161_readonly_role_e2e.
py（t161.json）共 18 项断言全部 PASS，审查员窗格与历史 attempt
窗格均未请求焦点，无任何焦点错误横幅。
4. 历史窗格未覆盖的说明是否如实：
• 如实。已结束 attempt 没有保存在线 PTY（this.panes.get(thread)
为空），panes.ts:1480-1495 返回的快照中不含 size 字段。前端收到后
ptySize 为 null，自然回退到 fit.fit() 容器适配。RESULTS.md
的“未覆盖”章节明确记录了该行为与边界，表述与代码完全一致。


### 5. 修改边界与文档文案

• 修改边界：本票按用户授权（user-decision.
md）由执行主控自修。改动仅触及 workbench/src/panes.
ts、workbench/app/renderer.tsx、workbench/app/style.
css、workbench/README.md、新增端到端测试与对应 evidence
记录。未越过任务卡和 ticket 边界，未修改门禁核心逻辑。
• 文档与文案：workbench/README.md#L10 准确补充说明：“可写窗格把 PTY
调到窗格大小；只读查看不改 PTY 尺寸，按 PTY
自身的行列显示，窗格较小时可滚动，打开时停在最新的行（T-
168）。”文案客观清晰，无营销口吻。
──────
## 二、审查发现列表

序号 │ 文件与行号                │ 严…  │ 发现与失败场景说明
──────┼───────────────────────────┼──────┼───────────────────────────
1    │ renderer.tsx:220-244      │  P3  │ 初次挂载时的短暂 fit 与
hidden
屏障组件首次挂载时，ptySi
ze 初始为
null，挂载瞬间触发的
ResizeObserver 会先走一次
fit.fit()。由于此时
restoring === true 且
hidden，直到首个快照返回、ter
m.resize(ptySize)
执行完毕且回放追平实时后才会
解除隐藏并绘制，因此用户界面
执行完毕且回放追平实时后才
会解除隐藏并绘制，因此用户
界面无可见闪烁或错位。但在
逻辑时序上存在一帧未拿到快
照前的
fit.fit()，属无害实现细节
。
2    │ panes.ts:1480-1495      │  P3   │ 历史 attempt
尺寸未持久化到事件库正如作
者在 RESULTS.md
中如实记录，历史已结束
重绘序列，在不同容器宽度下回
放历史 attempt
仍有错位风险。当前针对 T-
164（在线审查员）的修复有效，
建议后续可在事件库或 launch
记录中持久化最终 PTY 尺寸。
3    │ style.css:161-162    │  P3   │ 窄分屏下的水平滚动交互data-
readonly="true" 使用了
overflow: auto; flex-
direction: column-reverse;
width: max-
content;。在极端窄分屏（如窗
口被多次横向切分致单窗格宽度
远小于 160
列）下，内容不会自动软折行，
需要用户手动横向滚动查看右侧
内容。这是保证 TUI
相对光标重绘不崩塌的必要设计
取舍，行为符合预期。
──────
## 三、最终审查结论

T-168 的根因分析准确定位了视口与 PTY
尺寸不一致的物理根源；修法将只读窗格视口锁定在 PTY
实际尺寸，既不破坏被查看程序的环境，又避免了相对重绘序列错位；可写窗
格与 T-161
只读焦点均无回归；红态、绿态、两类典型变异体与完整回归套件均具备真实
入口证据；未覆盖边界如实记录。审查结论为通过。

T-168 REVIEW PASS
