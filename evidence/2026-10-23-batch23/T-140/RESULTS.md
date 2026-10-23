# T-140-1 / a1 交付记录

状态：**INCOMPLETE**。worker：b23-t140；分支：`exec/t140`；起点：`ebbae7bd09cee3a8220b948029f9033dc2906c90`。
这是待执行主控复跑、独立审查的候选，不是已验收结论。代码版本以本文件所在交付提交为准。

最新进展：执行主控已运行 RUN-OUTSIDE-01。两家 worker 的添加授权、两家 reviewer/monitor 以及 T-131/T-137/T-127 回归在
`bffd3ca125a4605580b1d52d754b93e471ea40e5` 上通过；移除场景被测试驱动的同回合连续点击阻断，旧 shell 变异也不成立。
本轮只修复测试驱动与反事实判定，没有修改产品代码或放宽断言；当前候选待 `RUN-OUTSIDE-02.sh`。
根因、现场数据和新命令见 [ROOT-CAUSE-02.md](ROOT-CAUSE-02.md)。
修订的固定候选 `3e8f2a5e6b036fb5d1bda455c91ce551b021f61a` 已经新的只读上下文审查：未发现确定的新设置失败，
结论为 INCOMPLETE，等待原生复跑，见 [ACCEPTANCE-REVIEW-02.md](ACCEPTANCE-REVIEW-02.md)。本次后续提交只保存该审查记录。

## 改动

- 项目行右键菜单增加“编辑项目”，显示主目录，支持目录选择器添加、列表移除与保存；沿用现有设置对话框样式。
- 后台只接受操作员保存设置，目录解析为真实绝对路径并去重。`project_settings_saved` 追加到现有事件表；读回取最近保存的目录列表，删除/重开项目不继承旧授权。
- worker、reviewer、monitor 在启动时读取该项目的额外目录。Claude 同时得到 `--add-dir`、文件工具写权限和沙箱 `filesystem.allowWrite`；Codex 得到 `--add-dir`。monitor 有额外目录时使用 workspace-write，工作目录仍是自己的观察目录，主项目不成为额外写根。恢复同一 monitor 会话保留原启动权限。
- 完整启动记录保存 `extra_directories` 与实际 argv；角色提示带本会话目录列表。reviewer 的原生门禁仍逐项核对参数、沙箱与身份，允许的额外路径须与该次启动记录一致。
- 界面、角色卡和 README 写明额外目录改动不进门禁审查与集成，worker 须列出改过的额外目录。用户项目终端启动路径未改。

## 验收证据

| 验收项 | 结果 | 证据与限制 |
| --- | --- | --- |
| 追加事件、读回、移除、跨项目隔离、重启读回 | PASS（存储契约） | `store-red.log` → `store-green.log`；真实 SQLite，未替代原生权限验收 |
| Electron renderer/main/preload 构建 | PASS | `build-01.log`、`build-02.log`；只证明能构建，不证明界面交互或视觉效果 |
| 现有侧栏投影回归 | PASS | `sidebar-01.json`；真实 Git/SQLite、受控状态输入，无 Electron/模型证明 |
| 测试驱动识别 reviewer 的独立副本路径 | PASS（驱动契约） | `driver-red-01.json` → `driver-green-01.json`；两家 reviewer、worker、monitor 的脚本路由，未替代原生运行 |
| 两家真实 worker：X 可写、Y 不可写 | INCOMPLETE（当前候选） | RUN-OUTSIDE-01 在 bffd3ca12 的此项已通过；新驱动待 RUN-OUTSIDE-02 |
| 真实 reviewer 门禁与两家 monitor 的额外目录 | INCOMPLETE（当前候选） | RUN-OUTSIDE-01 在 bffd3ca12 的此项已通过；新驱动待 RUN-OUTSIDE-02 |
| CDP 操作编辑对话框移除 X，之后两家新 worker 写 X 失败 | INCOMPLETE | 同一 e2e 已编写，未运行 |
| 修前 e2e 红态 `--revision ebbae7bd0` | INCOMPLETE（当前驱动） | RUN-OUTSIDE-01 在“Edit Project menu”拒绝修前版本；新驱动待复跑 |
| 两个变异 | INCOMPLETE | 改为 `claude-shell-deny-extra` 与 `removed-directory-retained`；旧 shell 变异未测到 shell 失败，旧移除变异与普通绿态同因失败，不作为敏感性证明 |
| T-131、T-137、T-127 原生回归 | INCOMPLETE（当前交付） | RUN-OUTSIDE-01 三项通过；RUN-OUTSIDE-02 再跑以绑定新交付 |
| Python 语法、zsh 语法、diff 空白检查 | PASS | `py_compile`、`zsh -n`、`git diff --check` 均退出 0 |

存储契约的预期红态在实现前取得：旧实现返回 `undefined`，要求是 `['/fixture/X']`，断言在第 14 行失败。
当时 HEAD 为任务起点。修复后相同命令通过，事件历史仍保留两次设置。

本地命令（均在本 worktree 根目录）：

```zsh
node workbench/tests/test_t140_project_events.ts > evidence/2026-10-23-batch23/T-140/store-red.log 2>&1
# 上一条在实现前运行，退出 1；实现后改用新的 store-green.log，退出 0。
node workbench/tests/test_t140_project_events.ts > evidence/2026-10-23-batch23/T-140/store-green.log 2>&1
node workbench/app/build.mjs --slot t140-check-01 > evidence/2026-10-23-batch23/T-140/build-01.log 2>&1
node workbench/app/build.mjs --slot t140-check-02 > evidence/2026-10-23-batch23/T-140/build-02.log 2>&1
node workbench/tests/test_t107_sidebar.mjs evidence/2026-10-23-batch23/T-140/sidebar-01.json
PYTHONPYCACHEPREFIX=/tmp/t140-pycache python3 -m py_compile workbench/tests/test_t140_extra_dirs_e2e.py
zsh -n evidence/2026-10-23-batch23/T-140/RUN-OUTSIDE-01.sh
git diff --check
```

上述固定证据路径不能覆盖，复跑应另取新路径/slot。单独构建的临时缓存与输出已清理，保留日志及 `build-cleanup-*.json`。
首次 `py_compile` 未设置缓存目录，被沙箱拒绝写用户 Python 缓存；改用 `/tmp/t140-pycache` 后通过。
首次侧栏回归命令漏传报告路径，被脚本拒绝；按其接口传入新路径后通过。两者不算产品红态。

## 沙箱外复跑

运行：`zsh evidence/2026-10-23-batch23/T-140/RUN-OUTSIDE-01.sh`。
以上是首轮历史命令；本轮请运行 `zsh evidence/2026-10-23-batch23/T-140/RUN-OUTSIDE-02.sh`，原脚本与旧证据不覆盖。
脚本每次创建新的 `outside-<时间>` 目录，保存每条命令、退出码、JSON 摘要、日志与截图，最后给出 `run.json` 路径。
红态、变异必须在对应行为断言失败才算通过反事实检查，环境失败不算红态。

本地原生运行命令：

```zsh
PYTHONDONTWRITEBYTECODE=1 python3 workbench/tests/test_t140_extra_dirs_e2e.py --summary evidence/2026-10-23-batch23/T-140/native-sandbox-01.json
```

实际在创建 `/Users/Shared/t140-extra-*` 时被沙箱拒绝，退出 1，0 个模型请求；见 `native-sandbox-01.json`。
按 COMMON.md 未申请越权。X/Y 用测试自建的 `/Users/Shared` 隔离目录，避免 Codex 原有临时目录写权限污染 Y 负例。
真实 Codex CLI 使用 `/tmp` 下隔离 CODEX_HOME 与本地脚本化 Responses API，不复制 auth.json，不调用供应商模型；只设置夹具 provider 与 `git add`/`git commit` 两条规则，结束后删除整个测试 CODEX_HOME。
Claude 使用真实 CLI、`claude-haiku-5-5` 与本地脚本化 Messages API。后台通过现有 detached 启动入口运行；Electron 独立进程组，从内置盘临时构建启动。
初次添加通过真实后台操作员入口；移除通过 CDP 点击真实对话框。原生目录选择器的人工交互尚未验证，不能据此声称已通过。

原始 fixtures、SQLite、traces 与外部 X/Y 夹具留给执行主控按 T-088 归档；本次没有把大块原始目录提交进仓库。

## 已上报与待处理

- 收件箱：`20261023T101123Z-worker:b23-t140-issue-001`，正文见 `ISSUE-temporary-write-roots.md`。
  Codex 普通 worker 原有 `/tmp` / `$TMPDIR` 写权限仍在：若额外目录本来就在默认可写位置，移除登记不能撤销默认授权。
  该事实目前来自源码，尚无原生复现；请执行主控与 T-141 协调。未擅自收紧临时目录或修改 T-141。
  收件箱文件由规定的 `scripts/inbox send` 生成，留在本 worktree 的 `.project-map/inbox/`；未纳入交付提交，以免改动任务卡禁止路径。
- 未修改 oracle_paths、地图、ticket、术语表或其他任务的实现。独立审查和原生验收尚未完成。
- session 开始与本地检查后 `project_map.py status`：0 Problems、0 Stale living docs。交付前再保存一次结果。

## 固定候选的只读审查与修复

behavioral-acceptance-review skill 要求的新只读上下文审查了固定候选 `f41503eabd50c4c30f963ae6b5b8d8d45055838a`。
结论是 **FAIL**：新 e2e 把 reviewer 的随机副本目录当作 worker 目录来识别任务，原生绿态跑到首个 reviewer 就会失败。
完整审查保存在 `ACCEPTANCE-REVIEW-01.md`。该 FAIL 保留，不升级为 PASS。

后续只修复测试驱动：reviewer 从门禁提示的绑定 `task` 字段识别任务；worker 继续按自己的 worktree 识别。
新增驱动契约先在坏候选取得 `unknown working directory` 红态，再在当前脚本取得绿态：

```zsh
PYTHONDONTWRITEBYTECODE=1 python3 workbench/tests/test_t140_scripted_plan.py --revision f41503eab --summary evidence/2026-10-23-batch23/T-140/driver-red-01.json
PYTHONDONTWRITEBYTECODE=1 python3 workbench/tests/test_t140_scripted_plan.py --summary evidence/2026-10-23-batch23/T-140/driver-green-01.json
```

这两条也已加入 RUN-OUTSIDE。修复后的原生候选仍需执行主控运行和独立审查，整体验收仍为 INCOMPLETE。
