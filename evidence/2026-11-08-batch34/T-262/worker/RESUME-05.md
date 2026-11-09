# T-262 新 attempt 恢复与测试交接

INCOMPLETE：旧候选已经恢复，表单选择驱动已修正。尚未取得本次候选完整绿态、四个变异结果和独立审查，代码未提交、未 submit。

**Works**：旧 base 与本次 base 的三个目标文件无差异，恢复前本 worktree 干净。三个文件及 14 份 worker 精简证据与旧 worktree、备用检查点逐字节一致，见 `restore-05.json`。修订后的 select 驱动通过语法检查，真实运行待主控执行。
**No regression**：`static-checks-05.json` 证明本次只改测试 docstring 和 `Fixture.choose`，测试其余 AST、全部业务期望、四个变异、details 的 Enter 检查及入口、清理不变。两个产品文件与检查点一致；本次未重复构建，未运行完整回归或真实 Electron。
**Risk / undo**：原生沙箱已知拒绝产品和清理路径里的 ps，worker 不重试、不绕过。主控需运行 `controller-runs-05.command` 并回传结果，随后安排独立审查与原生选择器键盘观察。若要撤回本轮驱动修订，可从只读检查点取回测试文件；不要丢弃本次及旧失败证据。

## 身份与范围

- task：`a2a+T-262-1`
- attempt：`64d48cf7-0cfc-4078-8a13-6f0067297990`
- session：`f08fffc6-d09d-4a7c-8253-e5ddf60fca04`；fence：2；spec_rev：2
- 本次 base：`3647a07bdacb514cdc303965be8c52b84d9356b2`
- 旧 base：`f80d5cdbf0e1b62de864300eff7bb4497f8c4c70`
- 旧工作区只读；外层 cwd 始终为本 attempt worktree。额外可写目录为 []，无额外目录改动。

小目标：恢复既有候选，修正真实 select 测试驱动，交出准确可执行的父版 smoke、完整候选和四个变异命令。本轮不重新实现产品，不操作 T-249 的 Enchanted Test 窗口、正式应用或其他状态目录。

Ubiquitous language 沿用用户输入、门禁回执、任务、会话。Tracer bullet 仍为混合任务/会话场景中的双区排序与任务筛选。Deep modules 沿用已恢复的页内统一记录索引，未添加过滤路径或包装层。

## 已有红态与本次驱动修正

主仓库 `controller/red-outside-03.json` 与 `red-outside-04.json` 都记录父版排序业务失败。04 记录了真实 keydown/keyup，但没有 input/change，select 值仍为空；该选择失败属于测试驱动 INCOMPLETE，不能当产品筛选 FAIL。

本次 `choose` 核对真实选项及启用状态，设置真实 select 的 value，派发冒泡 input/change，再等待 React 提交和读取结果。没有修改 React 状态、产品记录、window.a2a 或 UI 行数据。监听器在 finally 移除；新报告字段 `form_selections` 记录事件、目标值和 `native_keyboard=false`，不声称原生键盘操作通过。

details 继续使用原有 CDP Enter 展开、收起；没有修改键码或业务断言。原生 select 的键盘体验由主控另做 Computer Use 验收。旧键盘探索说明、历史启动阻断与旧身份文件均原样保留；`RESTART-HANDOFF-04.md` 和旧命令不再代表当前操作要求。

## 入口与清理核对

以下为代码核对，未冒充本次运行结果：

- `renderer.tsx` 按项目 key 挂载 RecordsPage，IPC 通过当前窗口的独立 state 请求 `user_input_records` / `relay_receipts`，再由后台读取 SQLite。输入的 thread 映射已有 launch；回执保留 launch 与完整 result。
- 默认无参数走完整场景；`--smoke` 只截短到双区排序、任务筛选。`--revision` 仅替换隔离复制品中的两个产品文件；四个 mutant 均唯一匹配，只改隔离复制品。
- Electron 通过现有 `cdp_launch.cjs` 启动，独立 userData、HOME、TMPDIR、状态库及 CDP 端口；后台与窗口不借用现有 App。依赖从既有 node_modules 读取，不安装。hc 缓存路径只读，安装与构建目标在本次夹具内。
- 真实读取代理只对本次后台的完整响应做延迟或断连，不制造响应记录；业务期望仍来自固定原始场景和新增随机哨兵。
- `stop` 先关闭自有 Electron，再停止后台、代理和私有 core；仅复用 `scripted_claude` 的纯清理函数，不实例化其 Claude 夹具。任何清理异常进入 INCOMPLETE 并保留现场，不继续删除夹具。
- 摘要和 diagnostics 使用独占创建；清理前先保存精简日志、阶段和退出码。只有私有 core/进程检查成功，才记录目录、时间、文件数、字节数并删除自有夹具和构建缓存。

## 本次检查与待补证据

可复现的静态命令：

```sh
python3 evidence/2026-11-08-batch34/T-262/worker/check-resume-05.py
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
```

静态检查通过；它依赖仍保留的只读检查点，结果不证明 UI 行为。地图检查为 Problems 0、Stale living docs 1，退出码 1；范围外的 `workbench/README.md` 因恢复两个覆盖文件被标 stale，合并到本次单条 issue 交主控处理，worker 不修改 README 或地图。

完整场景包括双区筛选和倒序、单一来源会话、同名主控、原文与人工介入、完整回执、窄窗、details 键盘、刷新哨兵、跨项目迟到响应、错误及恢复、空项目。父版及四个变异应 FAIL / 非零；INCOMPLETE 不计变异检出。候选要求 PASS 且清理状态完整。当前这些运行结果全部待补。

旧 T-133/T-179 脚本依赖 Claude，按卡未运行；其相关页面行为由新无模型场景覆盖，但尚无本次绿态。旧标准构建结果只作为历史证据保留，不作为新 base 的行为结论。design-integrity-review 自查与主控负责的 behavioral-acceptance-review / 独立审查留待真实结果及稳定候选具备后完成。

下一步由主控在本 worktree 作为外层 cwd，逐条执行 `controller-runs-05.command`。worker 本轮没有启动后台、应用、模型或 ps，没有执行全套测试或构建；保持未交付直到回传证据。

本次单条 blocking issue 请求 `3ef58c0f-04d7-4749-a745-edd9b010f9bd` 已返回 `queued=true, delivered=false`，只表示请求文件已排队，不表示主控已受理。原始回显见 `issue-queued-05.txt`；请求文件位于本 attempt 的请求目录，不进 Git。等待本回合结束后的 Stop hook 转交。
