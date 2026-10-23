# T-146-4 交付记录

状态：**INCOMPLETE**。主控已在 `outside-DBc5ZoMx/` 完成候选 `f76805f76bb9020662cb21dffc584686e5c79c50` 的真实 Electron／CLI 验证，产品检查符合预期；旧脚本因错误字符串末尾空格误拒绝 UI 变异证据。本次判据修复的本地重放 PASS；新组合脚本 `RUN-OUTSIDE-02.sh` 尚未沙箱外执行，正式验收与独立审查仍由主控完成。

任务：T-146-4；attempt：a4；worker：b23-t146d；分支：`exec/t146-a4`；起点：`6af6e3028cbca2d1868e32eda85eeb932b91ef17`。任务范围与验收文件见 `card.md`，规格依据见其中引用的 T-146 与用户裁定 B。候选版本由交付提交绑定；沙箱外脚本另保存实际 HEAD 与相关源码差异。

## 改动与边界

根因：`sidebar.ts` 将所有曾确认生效的角色都作为主控保留，并直接把角色申请的 ended 当作会话 ended。`a2a release` 只结束角色，终端仍运行，因此原 T-133/T-107 等不到主控条目消失。

修复仍在同一投影入口：取终端的 pane lifecycle；角色不再 approved 且 pane 没有 ended 时，跳过主控条目，让既有普通终端投影显示真实生命周期。pane 已 ended 时仍保留最近生效的主控身份与“已结束”状态，不恢复命令权限。没有修改门禁、角色权限或终端观测器。

流程页原本消费侧栏投影，自动得到修复；没有修改 `flow.ts` 或 `FlowPage.tsx`。Reflect 按角色申请保留历史角色，已交回的历史角色仍显示“已结束”；现有逻辑已符合该语义，无须修改。也未修改 `panes.ts` 或任何 oracle_paths。

Ubiquitous language 沿用“角色申请”“普通终端”“Agent 会话”。Deep modules 的现有投影接口不变。Tracer bullet 沿用受保护的真实 T-133/T-107 入口与 T-146 入口，已取得主控沙箱外运行证据。

## 已有真实入口红态

主控提供的合并回归与单独重跑，均在交回成功之后失败“超时：身份已放弃”。`existing-e2e-red-01.json` 保存原路径、fixture、命令、前置检查和角色交回回执摘录，原件保留在主 checkout 的 `merge-1/run-20261023T134713Z/`。这是已有失败证据，不是本 worker 新运行的 e2e。

本 attempt 在修改行为前运行新增投影反例，`projection-red-01.json` 实际保存了交回后仍残留的主控条目；失败为 `Released live terminal must not remain a controller`，不是启动或依赖错误。

## 本地验证

环境：macOS；Node v26.5.0；未调用供应商模型；pane lifecycle 由夹具提供，SQLite 与三处投影使用真实代码。这些检查不证明实际 CLI、Electron 或进程观测边界。

| 检查 | 结果与证据 |
| --- | --- |
| 修前交回运行中终端的角色 | 预期红态，`projection-red-01.json` |
| 修后同一信号 | PASS，`projection-green-01.json`：恢复普通终端、未知生命周期不冒称结束、新角色替换、关闭后保留身份与历史、无权限和只读查询 |
| 已知坏起点反事实 | 预期红态，`baseline-counterfactual-01.json`：隔离导出起点源码，新测试在同一目标断言失败 |
| 已结束主控回退普通终端变异 | 被既有 ended_projection 拒绝，`closed-controller-mutant-01.json`；隔离副本将 `held` 条件改回仅 approved |
| 既有 T-146 ended_projection | PASS，`ended-projection-01.json` |
| 既有 T-111 flow | PASS，`t111-01.json` |
| 既有 T-107 sidebar 投影 | PASS，`t107-projection-01.json` |
| 初次交付的脚本语法、编码与差异检查 | `final-checks-01.json`、`final-checks-02.json`、`cdp-syntax-01.json`；当时新增可见性驱动只完成静态检查，后续真实运行见下节 |
| 项目地图 | session 开始及交付检查均为 Problems 0、Stale living docs 0；未修改地图、术语表或 ticket |

重放命令（输出必须使用新路径）：

```zsh
node workbench/tests/test_t146_released_projection.mjs /private/tmp/NEW-release.json
node workbench/tests/test_t146_ended_projection.mjs /private/tmp/NEW-ended.json
node workbench/tests/test_t111_flow.mjs /private/tmp/NEW-flow.json
node workbench/tests/test_t107_sidebar.mjs /private/tmp/NEW-sidebar.json
zsh evidence/2026-10-23-batch23/T-146-a4/RUN-OUTSIDE-02.sh
```

反事实重放：将起点的 `workbench/src` 用 `git archive` 导出到新的 `/private/tmp` 目录，在其 `workbench/node_modules` 接上本 worktree 已有依赖，然后给新增投影测试传第二个参数 `<隔离源码根目录>`。变异重放：复制候选 `workbench/src`，只把 `const held = current.filter(row => row.confirmed_at);` 改成 `const held = current.filter(row => row.state === 'approved');`，给既有 ended_projection 测试传该源码根目录。原始隔离目录保留，路径见 JSON 的 argv 与 fixture；归档由主控按 T-088 处理。

## 沙箱外交接

`RUN-OUTSIDE-01.sh` 按顺序运行：起点 T-133/T-107 红态（同时作为“交回后仍保留主控”的已知坏实现）、候选同测试绿态、普通终端 UI 错标 ended 的变异、T-146 绿态、T-146 主控回退普通终端变异、两项投影检查、T-111、T-107、T-139/T-143、T-137。每次生成新的 outside 目录，保留失败、日志和截图。红态要求交回成功且到达目标断言；关闭终端变异沿用已有业务字段判据，不接受任意失败作为反例。

T-133/T-107 红绿通过新增 `test_t146_release_visibility_e2e.py` 驱动原有受保护场景，原测试文件及其全部断言不变。驱动在“放弃身份的回合结束”之后、原场景继续输入之前，保存并核对同一 launch：后台为运行中的普通终端；侧栏唯一条目位于普通终端区域且运行中；流程 API 和已加载的 DOM 均移除该主控；Reflect 历史角色可见且已结束。另有 `--mutant stale-terminal-ui`，只在隔离源码中把普通终端 UI 状态写成 ended，后台不改；脚本要求实际看到 API running／DOM ended 的业务违约才接收反例。原测试摘要另存 `*-oracle.json`，补充观察存根摘要的 `release_visibility`，均不覆盖已有文件。主控已运行该驱动与 UI 变异，结果见下一节。

## RUN-OUTSIDE-01 实跑与判据修订

运行来源：执行主控在沙箱外运行 `RUN-OUTSIDE-01.sh`；目录 `outside-DBc5ZoMx/`，候选版本由其中 `candidate.txt` 绑定。worker 在本轮只读核对结果、隔离变异源码与日志，并重放判据，没有重启 Electron 或原 fixtures。核对摘要为 `outside-summary-01.json`。

| 检查 | 实际结果 |
| --- | --- |
| T-133/T-107 起点红态 | 预期拒绝：交回成功之后“超时：身份已放弃”；新脚本判据重放通过 |
| T-133/T-107 候选绿态与可见性补充 | PASS；`t133-t107-green.json` 的四项 `release_visibility.checks` 全部完成，含侧栏普通终端、流程移除和 Reflect 历史状态 |
| T-146 绿态 | PASS |
| ended_projection、released_projection、T-111、T-107、T-139/T-143、T-137 | 全部 PASS |
| 主控关闭后降为普通终端变异 | 预期拒绝；原 `red_verdict.py` 业务字段判定通过，本轮再次重放通过 |
| stale-terminal-ui 变异 | 按预期被 DOM 断言拒绝：API 为运行中的普通终端，实际 DOM 为可见的已结束普通终端；旧脚本的字符串等值判定误报失败 |

旧判定失败原因：`scripted_claude.py` 的 `Electron.until` 使用 `f'超时：{label} {last or ""}'`，本次 `last` 为空时错误末尾仍有一个空格。`RUN-OUTSIDE-01.sh` 第 66 行按无空格字面量匹配，因此误拒绝有效反例。`verdict-red-01.json` 保留了对这份真实摘要重放旧判据的失败；没有修改旧脚本、原摘要或日志来掩盖它。

`RUN-OUTSIDE-02.sh` 保留相同测试、断言和超时，只在两个预期红态的错误字符串比较前加 `.strip()`，输出改为新的 `outside-02-XXXXXXXX/` 目录。所有角色、launch、API、DOM、前置检查与非零退出要求均保留。对原始真实摘要重放后，两项红态判据均通过；另用四个合成错误输入核对仍拒绝：错误检查名、进程成功、API 已结束、UI 实际运行中。详见 `verdict-green-01.json`；这些合成输入只证明判据，不作为产品运行证据。本轮没有修改生产代码、测试文件、测试断言或超时。

单独重放新 UI 判据（旧判据红态将 `02` 换为 `01`；保留既有原文件）：

```zsh
python3 - <<'PY'
import subprocess, sys
from pathlib import Path
root = Path('evidence/2026-10-23-batch23/T-146-a4')
script = (root / 'RUN-OUTSIDE-02.sh').read_text(encoding='utf-8')
marker = 'python3 - "$OUT/t146-mutant-ui.json" "$code" <<\'PY\'\n'
verdict = script.split(marker, 1)[1].split('\nPY\n', 1)[0]
result = subprocess.run([sys.executable, '-', str(root / 'outside-DBc5ZoMx/t146-mutant-ui.json'), '1'], input=verdict, text=True)
raise SystemExit(result.returncode)
PY
```

### `t146-mutant-ui-oracle.json` 的来源

它是变异进程内部调用原 T-133/T-107 测试产生的摘要，不是另一次未变异候选运行。驱动先在 `ObservedFixture.__init__` 把 UI 变异注入隔离源码，再在内存中把原测试的 `Fixture`／`Electron` 替换为该观测驱动。调用 `oracle.main()` 前，驱动重建 `sys.argv`，仅传内层摘要路径、可选 Claude 路径和 revision，不传外层的 `--mutant`，所以内层摘要的 `argv` 没有该参数，原测试自己的 `mutant` 为 null；`visibility_mutant` 是外层驱动写入的字段，内层文件根本没有这个字段（用 `.get()` 读取会得到 None）。

证据核对：内外摘要都绑定 `/private/tmp/t133t-9tg9wxxc`，原测试检查列表与错误完全相同；外层 `t146-mutant-ui.json` 明确标有 `visibility_mutant: stale-terminal-ui`。该 fixture 的 `source/workbench/app/renderer.tsx` 实际包含 `setOrdinaryTerminals(value.terminals.map(row => ({...row, state: 'ended', state_label: '已结束'})));`，日志堆栈也从 `oracle.main()` 进入外层 `check_release_visibility()` 后在目标 DOM 检查失败。未变异候选另有 `t133-t107-green-oracle.json` 和 `t133-t107-green.json`，两者均为 PASS。两类运行未混用。

## 冻结候选的辅助审查

按 behavioral-acceptance-review 技能对 `a2ec0db9d7f0025c414cc4988e411c1b41c98ddf` 做了一次新上下文只读审查，原文见 `acceptance-review-01.md`，结论 INCOMPLETE。审查独立复跑两项投影为 PASS，但指出交回角色后的 DOM 行为尚无专门断言（P2）。后续补充上述可见性驱动和 UI 变异，现已有主控实跑证据，不冒称原审查者已复验。生产修复没有变更。该辅助审查不替代主控的正式独立审查与门禁。

待核对：`RUN-OUTSIDE-02.sh` 新组合脚本的沙箱外结果，以及正式独立审查。已取得的真实运行证据均来自主控；worker 未运行 Electron、申请沙箱越权、改全局配置、push、集成或接管其他 attempt。交付提交后由主控复跑、正式审查和门禁集成。
