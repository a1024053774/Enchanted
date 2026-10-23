# T-139 / T-143 同批验证（attempt a1）

状态：**INCOMPLETE**。T-139 已有候选实现与隔离红绿证据；真实 Electron 未取得，T-143 尚未修改生产路径。不能验收或集成。

## T-139

项目视图为每个任务显示一格，点击任务读取任务自己的窗格布局；点击 agent 选择单个 launch。
项目普通终端不再混入任务视图，侧栏保留普通终端与已批准主控终端各自的入口。
任务与单个 worker 之间切换时复用仍被选择的 PaneBinding，保留输入凭据与序号；历史或 ended agent 只读。
新建项目终端从任务视图转入项目终端视图。项目行菜单未改。

| 检查 | 结果与证据 |
| --- | --- |
| 实际 main.ts 的修前合同检查 | NO_GO，`selection-red-03.json`：任务选择含 `project-shell`，正中缺陷。`-01`、`-02` 为夹具字段不完整的探索失败，不算红态 |
| 相同入口的改后检查 | PASS，`layout-green-02.json`，10 项：原 8 项加单 agent 重命名/关闭保留兄弟窗格布局与名称 |
| Git/SQLite 侧栏投影回归 | PASS，`sidebar-projection-01.json`。受控状态信号，不代表真实 CLI/UI |
| 标准构建 | PASS，`build-check-02.json`，命令 `node workbench/app/build.mjs --slot t139-view-check-02`；构建目录已清理 |
| Python 与 zsh 脚本语法 | PASS，`PYTHONPYCACHEPREFIX=/private/tmp/a2a-t139-pycache python3 -m py_compile workbench/tests/test_t139_t143_views_perf_e2e.py`；`zsh -n evidence/2026-10-23-batch23/T-139-T-143/RUN-OUTSIDE-01.sh` |
| 联合真实 Electron 修前运行 | INCOMPLETE，`baseline-02.json`：真实后台和两个 CLI 已启动，但 Electron 未开放 CDP 端口，ECONNREFUSED；无截图、无性能基线。`baseline-01.json` 是测试使用了错误夹具字段的探索失败 |
| 两个真实 Electron 变异 | 未运行；联合 e2e 提供 `task-includes-project-terminal` 和 `duplicate-replay` |
| T-091 指定回归 | INCOMPLETE，`pane-ipc-01.json` 与 `pane-ipc-baseline-01.json`：当前和起点 ebbae7bd0 都因既有 IPC handler 枚举过旧而失败，详见 `t091-issue.md`；未改受保护 oracle |
| T-107、T-133/T-107 真实回归 | 未运行；已列入 RUN-OUTSIDE-01 |

隔离合同复现命令：

```sh
node --experimental-vm-modules workbench/tests/test_t139_selection.mjs <新的summary路径> ebbae7bd0
node --experimental-vm-modules workbench/tests/test_t139_selection.mjs <新的summary路径>
node workbench/tests/test_t107_sidebar.mjs <新的summary路径>
```

联合 e2e 的期望来自任务卡与两张 ticket；只在测试副本注入 xterm 观察引用，不改终端输入/输出实现。
同一真实运行覆盖两个任务的真实 Claude CLI（`claude-haiku-5-5`，本地脚本化模型接口）、角色申请批准的主控终端、视图截图、
5000 行真实 PTY 输出、三次滚动帧间隔采样、八次交替切换、偏移/完整编号/隐藏输出核对、焦点输入、布局名与 ended 拒绝输入。
这些断言尚未在真实 Electron 上验证，脚本可能仍有夹具问题。

独立检查提醒单 agent 编辑的保存范围未覆盖。补充两名 agent、纵向分屏、分别命名的夹具后，`layout-red-01.json`
在 `agent_rename_keeps_sibling_layout` 准确失败：任务树被缩成 worker 一格，兄弟名称消失。现已在原保存函数中合并保存集，
单 agent 重命名只改其名称，关闭只移除其叶子；明确重开当前 agent 时登记其打开状态。`layout-green-02.json` 通过两项对应检查。
`layout-green-01.json` 是补丁位置错误导致的探索失败，已保留，不算通过。
第一次只读独立检查见 `REVIEW-01.md`：INCOMPLETE；审查期间只提交了证据，但 HEAD 改变使其按冻结规则停止。

## T-143

必须先量后改。当前无有效数字，因此没有提交性能收益结论，也没有关闭读屏、改轮询或增加缓存。

| 逐项试验 | 前后数字 | 当前处置 |
| --- | --- | --- |
| screenReaderMode 默认关闭 | 未取得 | RUN-OUTSIDE-01 在基线副本只改这一项，待数据决定是否保留；若保留还需手动开启入口 |
| WebGL 渲染 | 未取得 | 缺 `@xterm/addon-webgl`；已上报，不自行安装，详见 `webgl-issue.md` |
| 缩短轮询（100 → 16 ms） | 未取得 | RUN-OUTSIDE-01 在基线副本只改这一项，待数据决定是否保留 |
| 切换保留终端或限制回放 | 未取得 | 等有效基线后继续试验；本次只复用 T-139 所需的仍在选择中的输入绑定，不宣称切换性能改善 |

下一步由执行主控在沙箱外运行：

```sh
zsh evidence/2026-10-23-batch23/T-139-T-143/RUN-OUTSIDE-01.sh
```

脚本为每次运行新建目录；先确认修前真实业务红态和数字，再运行单项试验、T-139 候选、两个变异与指定回归。
回传新目录后，worker 才能按数字继续 T-143，并将生产性能改动放入第二组提交，最终再跑同一联合 e2e。
T-091 oracle 处置与 WebGL 依赖仍需主控处理。两条问题已通过 `scripts/inbox` 上报，未更改地图、ticket 或 oracle。

临时夹具原始现场仍在 `/private/tmp/t139-w2dud_w4`、`/private/tmp/t139-ybsr62oh`，以及
`regression-baseline-source.txt` 指向的修前源码副本。大块内容未入 Git，归档由主控按公共约定处理；未清除失败现场。
