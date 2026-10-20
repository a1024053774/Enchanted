# T-111 / a1：系统流程页

状态：**INCOMPLETE**。功能候选与测试准备修复已提交至 `43717b803a6f3db84cf3420921fd277aa7d13c1a`，主控运行的 outside-02 三项报告均 PASS；独立审查 01 因 F1（计数验收漏检）判 NO_GO。本轮只补验收，不改产品；沙箱内候选与截断变异检查通过，真实 Electron 新断言及独立复审待运行，本轮修复尚未提交。

## 候选与范围

- worktree：`/Users/luckye/Documents/Code/a2a-wt-t111`，分支 `exec/t111`。
- 起点：`b1ecd6e9cba23c1bbddb331822b6500a1488e2e9`；规格：T-111 ready_rev 1；task T-111 / attempt a1。
- worker session：`10858660-9c4e-4904-9811-feb626a89c75`；launch：`launch-c9958cdeceed4ee2a1b96ada1da39586`；native thread：`01a1580e-96ab-73d2-b5a5-c7f825736cab`。提交实际模型／强度取钩子尾注，不把请求配置当实际取值。
- Tracer bullet：先建立缺失流程投影的合同红态，再贯通只读投影 → daemon → window IPC → 单票实现阶段 worker 胶囊，并构建；随后扩展多票、折回、折叠、空状态与窄窗。
- Deep modules：领域投影集中在新 `src/flow.ts`，界面集中在新 `app/FlowPage.tsx`；原有层只接线。Ubiquitous language 沿用任务、attempt、启动记录、门禁阶段和已有七种 agent 状态。
- 不改门禁状态机、侧栏数据实现、派发与原生采集，不操作用户的 CLI 全局配置。

## 验收逐项

| 要求 | 状态与证据 |
| --- | --- |
| 当前没有流程页的红态 | PASS（合同）：`contract-red.json`；已知坏起点由 `counterfactuals-final-02.json` 再次拒绝。真实 Electron 起点红态待运行。 |
| 单独“流程”标签，一票一横向泳道 | 已实现；构建通过，真实 Electron 待运行。 |
| 两票并行：实现 2 worker、审查 1 reviewer | PASS（领域合同）`contract-final-03.json`；真实 Electron 四票夹具待运行。 |
| 阶段、胶囊与记录对应 | 阶段只由当前 attempt 的事件推进；agent 只按核实的父关系、任务和当前 attempt 放置。monitor 在泳道上方，结束会话不列为当前参与者。合同及三个变异检查 PASS；真实 IPC 数据一致性待运行。 |
| 打回线与次数 | 只累计该票的 `delivery_rejected`；附属 verification/review 结果不重复计数；保留此前 attempt 的打回次数。合同 PASS；真实 Electron 待运行。 |
| 无父记录／缺失父项／过期 attempt 进未归属 | 已实现；无父和过期 attempt 的变异被合同拒绝；缺失父项由已有侧栏事实校验负责，真实 Electron 待运行。 |
| 超过 4 个折叠、展开；已集成票默认折叠 | 已实现；真实 Electron 待运行。 |
| 空状态、窄窗横向滚动 | 已实现；真实 Electron 待运行。 |
| F2／F3 零写入及能拦住写库 | 待运行：实际 daemon/socket／SQLite／collector 检查；`flow_snapshot` 被纳入 catalog 只读路径，不记录读取请求，不调用 scan。独立比较全部 SQLite 表、schema 和 trace 原值；再注入一次 `store.event` 写入变异并要求拒绝。 |
| IPC 原拒绝检查不削弱 | PASS：`ipc-final.json`；完整保留旧拒绝与反例，扩充为 21 个 handler／22 个 bridge 名称，flow 只发送读命令、不发输入凭据，拒绝 iframe 和未知 window。 |
| 地图 status 0 问题 | INCOMPLETE：开始与结束均有 8 个既存缺失链接／文件问题，属于稀疏 checkout 未包含的 findings 与 grilling 文件；没有修改地图。结束 stale living docs 为 0，见 `project-map-status-final.txt`。 |
| 独立审查 | 未进行；交执行主控新开只读 reviewer。worker 自查不充作独立 behavioral acceptance review。 |

## 与参考图对照

已读取用户参考图。结构对齐：横向空心节点与细连接线，节点之间用 `›››`，节点下放阶段名称与竖排圆角胶囊，左侧彩色点、右侧会话标识与角色；超过四个显示“还有 N 个 ↗”；机械检查／审查有返回实现阶段的折回线；横向滚动。

有意不同：沿用现有工作台深色主题；以系统实际五个门禁阶段取代参考图的设计工作阶段；按票上下排列泳道；额外标出票号、项目、当前阶段、状态文字与 attempt，monitor 置于泳道上方。启动记录没有独立展示名，使用记录号，不根据终端文字造名字。相同阶段多次打回合并为一条带次数的折回线。颜色只区分胶囊，运行状态同时用图标和文字表达。

以上是设计／源码结构对照，**尚非真实 Electron 渲染通过结论**。按执行主控转达的用户原话“证据截图什么的都不要了,我也不会看”，本轮没有保存截图；GUI 验证脚本也不生成截图。

## 文件与并行合并提示

`renderer.tsx` 只改这些接线位置（本候选行号）：

- 9–10：导入流程组件和只读快照类型。
- 43：声明 `window.a2a.flow()`。
- 398：本地页面选择状态。
- 571–576：添加“终端／流程”标签、挂载流程页并包装现有终端区；617：闭合包装。

没有修改 `sidebar.ts`；`renderer.tsx` 的侧栏、提问状态和原终端内部逻辑均未重写。T-108 合并时核对上述接线即可。

## 复现与未完成检查

沙箱内已运行：

```sh
node workbench/tests/test_t111_flow.mjs evidence/2026-10-20-batch18/T-111/contract-final-03.json
python3 workbench/tests/test_t111_counterfactuals.py --summary evidence/2026-10-20-batch18/T-111/counterfactuals-final-02.json
node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs evidence/2026-10-20-batch18/T-111/ipc-final.json
node workbench/app/build.mjs --slot t111-final-01
```

上述报告均使用新路径排他创建；重跑须改新文件名／slot。Node v26.5.0、npm 12.0.1，依赖在本 worktree 以 `npm ci --ignore-scripts --cache /private/tmp/a2a-t111-npm-cache` 安装，无跨目录依赖链接。构建在内置盘，只有现有包体积提示，没有构建错误；本次临时 cache/tmp 在交付前清理，dist 保留。Python 两个新脚本通过 3.9 语法检查，driver 通过 `node --check`；未宣称等同 Python 3.9 实跑。

首次反事实准备缺依赖，`counterfactuals-01.json` 与 `/private/tmp/t111-counterfactual-gn08909u` 保留；这是测试环境失败，不作业务红态。修正为私有普通依赖副本后，02、final 及 final-02 均 PASS。

收尾自查补充了缺失 attempt 的边界：任务和启动记录都没有 attempt 时，两个 undefined 不得视为绑定。`missing-binding-red.json` 保留该针对性红态；新增非空当前 attempt 前提后，同一合同在 `contract-final-03.json` 转绿。

执行主控应运行：

```sh
zsh /Users/luckye/Documents/Code/a2a-wt-t111/evidence/2026-10-20-batch18/T-111/RUN-OUTSIDE-01.sh
```

默认 Electron dist 为 `/Users/luckye/Documents/Code/a2a/workbench/node_modules/electron/dist`，可用 `T111_ELECTRON_DIST` 显式指定内置盘 43.4.1 dist。脚本清理 Git 路由变量、设 `LC_ALL=C`，以 Python 3.9 兼容语法运行，测试服务脱离调用者进程组。不调用 CLI 模型。GUI 起点来自上述 baseline 的普通归档副本，测试驱动读取真实 DOM／IPC，不替换产品响应。

脚本顺序：真实 daemon 的 flow 读取零写入 → 写库变异必须失败 → 起点 Electron 缺标签红态 → 新候选四泳道／折回／折叠／空态／900px 窄窗绿态 → 实际 IPC 所有表、schema、trace 原值比较。GUI 夹具中的状态保持已有规则判为未知，不凭“prepared”伪造运行中。

成功清理测试夹具与构建；失败保留进程归属、夹具及输出路径。保留的失败现场需执行主控按 T-088 归档后再处理，不能为取得通过而删除。没有更改用户提供的 ticket 验收勾选，也未进行门禁 submit。

## 提交交接

`git add --sparse` 在沙箱内被拒绝：`Unable to create '/Users/luckye/Documents/Code/a2a/.git/worktrees/a2a-wt-t111/index.lock': Operation not permitted`。没有暂存成功或部分提交；没有申请升级，也没有直接操作共享 Git 元数据。

由执行主控在沙箱外运行保留本 worker 原身份的脚本（尾注仍由原钩子自动追加）：

```sh
zsh /Users/luckye/Documents/Code/a2a-wt-t111/evidence/2026-10-20-batch18/T-111/RUN-OUTSIDE-COMMIT-01.sh
```

脚本核对分支、起点、空暂存区，使用明确文件清单和 `git add --sparse`。先提交当前 INCOMPLETE 候选以固定完整代码版本，再运行真实验证并交独立审查；本轮验证报告会绑定该提交。验证结果与本记录的状态更新可由主控后续提交。若候选变化或检查失败，不沿用本轮绿态。

## 第 21 轮反馈：测试副本 helper 执行位

执行主控已运行 COMMIT-01（rc 0），提交为 `862ca16709ec5936de8c769ce62dc4b0401dad22`。RUN-OUTSIDE-01 返回 rc 1、INCOMPLETE；失败报告保留在 `daemon-outside-01.json`，现场保留在 `/private/tmp/t107-daemon-read-JL2XUA`。错误是复制的 `runtime/node_modules/node-pty/prebuilds/darwin-arm64/spawn-helper` 为 0644，产品按原约定拒绝。它是测试准备失败，不是流程页业务红态。

修复范围：

- `test_t107_daemon_readonly.mjs`：依赖复制完成后，仅把该临时 runtime 中固定版本的 darwin-arm64 helper 设为 0755。零写入／native offset 的所有原断言不变。
- `run_t111_flow.py`：原先直接从 source 启动 daemon，同样会遇到 helper 0644；改为在该次测试根内普通复制 src 与依赖，只修改副本 helper 执行位，并从副本启动 daemon。Electron 仍验证原候选构建；无链接、无模型调用。
- 产品 `spawnHelper()` 继续核对执行位并拒绝失败；原 worktree 依赖未 chmod，仍为 0644。

局部准备检查 PASS，见 `helper-preparation-02.json`：从真实测试脚本执行副本 chmod 行，再由 node-pty 的实际 native loader 定位 helper，确认副本可执行且为 0755、原文件前后均为 0644。该检查不证明 socket、daemon 或 Electron。Node 语法、Python 3.9 语法、zsh 语法和 diff 检查 PASS。

新重跑命令（新报告名，保留 01）：

```sh
zsh /Users/luckye/Documents/Code/a2a-wt-t111/evidence/2026-10-20-batch18/T-111/RUN-OUTSIDE-02.sh
```

如需先固定此次测试准备修复的代码版本，可由执行主控运行 `RUN-OUTSIDE-COMMIT-02.sh`；脚本只暂存这两个测试文件与 T-111 的证据，仍由原钩子自动追加尾注。

## 第 23 轮反馈：F1 多次打回计数验收缺口

独立审查 `independent-review-01.md` 判 NO_GO：正确产品通过独立输入，但旧合同接受 `.slice(0, 1)` 截断打回事实的错误实现。本轮只修改四个测试文件，`workbench/src` 和 `workbench/app` 的 diff 为空；没有修改独立报告、审查脚本或产品代码。

已保留修复前信号 `count-oracle-red-03.json`：在反事实套件中新增截断变异后，旧合同仍返回 PASS，套件按预期报错。它是 F1 的重现，不把依赖或启动错误当作变异拒绝。

合同现在给同一张 T-B 票输入三条规范 `delivery_rejected`：旧 attempt `previous-b` 的机械检查打回一次，当前 attempt `b` 的独立审查打回两次（两次审查结果都伴随各自打回事实，中间有重新交付与机械检查通过事件）。独立预期写在测试里：总数 3，来源顺序 checks/review/review；去掉旧 attempt 后为 2 且均为 review；去掉 `review_result` 不改变打回记录；只剩 `review_result` 而没有 `delivery_rejected` 时为 0。当前 attempt 的阶段仍回到实现，不受旧 attempt 阶段干扰。

真实 Electron 夹具使用同一语义的三次打回，最终重新交付并检查通过，保持当前独立审查阶段。新增实际 DOM 与 IPC 断言：票头和折回图总数为“打回 3 次”；两条可见折回线分别显示“机械检查打回 1 次”和“审查打回 2 次”；data-return-count 为 1/2；实际 IPC 原始 returns 为三条，来源 checks/review/review。既有其他泳道、状态、折叠、空态、窄窗和零写入断言保留。

沙箱内结果：

- `count-contract-green-03.json`：候选 PASS。
- `count-oracle-green-03.json`：反事实套件 PASS，截断变异明确以 `Ticket rejection facts must accumulate across attempts`、`1 !== 3` 失败；其余已知坏版本与变异继续被拒。
- Node、Python 3.9 语法及 diff 检查 PASS。没有重建或修改产品。

由主控在沙箱外先固定修复提交，再运行新编号脚本：

```sh
zsh /Users/luckye/Documents/Code/a2a-wt-t111/evidence/2026-10-20-batch18/T-111/RUN-OUTSIDE-COMMIT-03.sh
zsh /Users/luckye/Documents/Code/a2a-wt-t111/evidence/2026-10-20-batch18/T-111/RUN-OUTSIDE-03.sh
```

真实 Electron 新断言尚未运行，不沿用 outside-02 的 PASS 替新验收背书。旧失败与主控／独立证据均原样保留。

审查脚本边界：`REVIEW-OUTSIDE-01.sh` 的 revision 固定为 `43717b803`，且预期旧合同及旧 Electron 接受截断变异，所以直接运行仍审旧版本并报告 NO_GO。这份独立脚本未由 worker 改动；要为新提交背书，需 reviewer 按新候选更新版本绑定和变异预期。主控可继续运行原脚本收集旧候选证据，但不能将其算作新候选独立通过。
