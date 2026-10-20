# T-108 第二轮审查修复（2026-10-20）

**本地回归 PASS；交付 INCOMPLETE，待主控提交及独立复审。** 起点 `a6c7c161ba101f4dc58870ace9dfa3ae4b1e8fe4`。本次模型／供应商调用均为 0；未读取真实凭据、未跑真实模型回合。

修复 F1-02 与 F2-02，沿用 question、answer、submission、turn 的 Ubiquitous language；Tracer bullet 采用实际 `Panes.signal → SQLite → questionState/agentState → answerQuestion`，进程身份和 PTY 由夹具提供。未改门禁、版本入口、全局配置、sidebar.ts 或 renderer.tsx；未把受控 PTY 合同当成新真实 CLI／Electron 验收。

## 改动

- 先单独核验工具事件的根来源与当前回合，取得 session／submission／turn 关联，再解析工具字段和响应。字段错误、非法响应 JSON 与处理失败都进入原有“保存事实后抛出”的处理；身份不符的诊断不带当前根关联，不撤销当前有效问题。
- `native_question_unverified` 携带上述关联和可定位的问题 ID。问题投影把对应 waiting／sending 问题降为 unknown；这同一投影供界面与作答入口使用。新的 answer_intent 不能把 unknown 再变成 sending，逐键写入也重新检查问题资格。异常在 answer 记录之前已存在时，不产生输入记录或按键；若异常发生于记录／写入期间，保留已有审计记录与已写按键，拒绝后续按键。
- 当前 Claude 根 Stop 的 stop_hook_active 必须为布尔值；缺失或类型错误时，保存同样的未知事实并拒绝。它不调用 transfer、不清 active／prompt、不置 idle，也不进入 stopInProgress。字段合法的旧 prompt、过期 Stop、stop_hook_active=true 保留未匹配处理；异 session 仍先拒绝。
- 问题面板沿用现有 disabled 判定，unknown 的标题与状态文案同步显示未知，避免已经撤销作答资格后仍显示等待回答。

## 红绿证据

先只修改正式测试，未修产品。`/private/tmp/t108-review02-red-02.json` 中，待答时缺工具名与非法 tool_response 都命中 `waiting_user_answer != unknown`，当前 Stop 缺 stop_hook_active 命中 `running != unknown`；另两个 Stop 状态／类型反例也失败。red-01 的运行中 Stop 场景先被旧的无关联诊断干扰，因此不作为该 Stop 缺字段的红态；原件保留。

随后将最终测试矩阵放到审查保留的 a6c7c161b 副本的新子目录；复制前用 `git show` 原文字节核对 panes.ts、questions.ts 未被改变，依赖使用审查目录中已有的普通文件。最终 8 场反例全部拒绝原候选，均命中业务断言。现场为 `/private/tmp/t108-review-02-6g6q0g48/worker-final-knownbad-9zivph58`，摘要 `/private/tmp/t108-review02-red-03.json`；没有修改审查先前的副本或失败证据。

修后同一正式入口 `/private/tmp/t108-review02-green-03.json` PASS：原 15 项及新增 8 场均通过。矩阵由 `test_t108_questions.mjs` 默认调用，不能只跑旧正常路径而漏掉新反例；README 记录了这类重复缺陷的机械检查入口。新增矩阵还核对旧 prompt、异 session、子 agent 不污染待答问题，完整无关工具仍忽略，以及异常后记录关联、作答拒绝、后续 PTY 零写入、无异常交付／完成事件。

本地检查均 PASS：Codex 原件回放、原 IPC 拒绝与变异检查、侧栏投影、实际 daemon 的 readonly／identity、原 Claude UPS／Stop 合同、标准 Vite 构建。构建位于内置盘临时目录且已清理。实际 daemon 两场 `cleanup_complete=true`，readonly 核对 SQLite 表与 trace 零写入。摘要保存在 [review02-fix-local.summary.json](review02-fix-local.summary.json)。

## 提交与复验

主控执行：

```sh
zsh evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-COMMIT-04.sh
```

脚本核对 HEAD、空索引，明确 `git add --sparse` 只暂存本次文件，由既有 hook 加尾注；不暂存 reviewer 报告或其脚本，不 submit、不 push。

提交后重跑以下命令。摘要必须使用新路径，不覆盖已有结果。

```sh
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node workbench/tests/test_t108_questions.mjs /private/tmp/t108-review02-recheck-01.json
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node workbench/tests/test_t108_hook_replay.mjs --samples evidence/2026-10-20-batch18/T-108/native-hook-samples.json --summary /private/tmp/t108-review02-codex-recheck-01.json
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs /private/tmp/t108-review02-ipc-recheck-01.json
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node workbench/tests/test_t107_sidebar.mjs /private/tmp/t108-review02-sidebar-recheck-01.json
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C T107_DEPENDENCIES=/Users/luckye/Documents/Code/a2a-wt-t108/workbench/node_modules node --experimental-vm-modules /private/tmp/t108-review-02-6g6q0g48/candidate/workbench/tests/review_t107_daemon_readonly.mjs /private/tmp/t108-review02-readonly-recheck-01.json /Users/luckye/Documents/Code/a2a-wt-t108 readonly
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C T107_DEPENDENCIES=/Users/luckye/Documents/Code/a2a-wt-t108/workbench/node_modules node --experimental-vm-modules /private/tmp/t108-review-02-6g6q0g48/candidate/workbench/tests/review_t107_daemon_readonly.mjs /private/tmp/t108-review02-identity-recheck-01.json /Users/luckye/Documents/Code/a2a-wt-t108 identity
```

后两条复用 reviewer 的普通复制依赖 harness，产品取当前 worktree，依赖取本 worktree，不链接主仓库。若需完整 Electron 无模型入口复验，沿用已有脚本并换新摘要：`zsh evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-NO-MODEL.sh /private/tmp/t108-native-e2e-04.json`。本修订未执行该 GUI 复验；不重跑真实模型。

原候选完整矩阵的反事实可重放：

```sh
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node /private/tmp/t108-review-02-6g6q0g48/worker-final-knownbad-9zivph58/workbench/tests/test_t108_questions.mjs /private/tmp/t108-review02-knownbad-repeat-01.json
```

该命令应退出 1；8 场均应为业务拒绝原候选。结束时项目地图检查仍为 rc=1、稀疏检出已有的 8 个缺失链接、0 stale living docs。修订提交尚未执行，不冒报 SHA 或整票验收通过。
