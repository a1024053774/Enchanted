STATUS: FAIL
TARGET: 1db51d21d19e462e54360cb6d53f0c04026bf18b（针对性对照 116985ec9f14b80cb26c1fd4a4451a409293e768）
EVIDENCE:
- 这是上轮 P1 的唯一限定复核，只核对正常登录 exec-only 标记、未知 shell 默认拒绝和相关 fake／legacy／argv／version／session／history／runtime identity／worker 合同，未重开其他范围的广泛审查，也未以实现者新增测试或结果为 oracle。旧报告 `/private/tmp/t093-r20-independent-K6vIJW/REVIEW.zh-CN.md` 保留不变。
- 新 nonce、新 SQLite、新原生 JSONL，通过真实 `Panes.recover()` 和 `OrchestrationStore`；所有外部执行边界仍为 supplied 替身。19 场完成，候选 18 场 PASS、1 场 FAIL。输入、逐次边界记录和结果分别在 `/private/tmp/t093-shell-recheck-joPlVg/candidate-e3de1651/{inputs.json,boundaries.jsonl,result.json}`。
- 局部 PASS：actual `claudeLaunch()` 使用相同 task／session／launch 身份生成 normal／fake 成对记录，单独保留 normal 的 exec shell 形态后，候选返回 `normal_login_restore_requires_protected_start`，零版本／PTY／进程调用，保留中文重启提示。normal 记录删其他标记却保留 exec 的案例也按实际残留标记判为 normal；去掉 exec、改成未知 shell 的变体才预期 `restore_record_unrecognized`，没有沿用上轮错误分类标签。
- 局部 PASS：未知 shell 缺失、非数组、额外参数、未知 option、空命令、空格开头 exec 均在版本／PTY／进程边界前以 `restore_record_unrecognized` 拒绝。显式 fake ideation、缺 authentication 与 executable_path 的 legacy fake executor 均恢复一次，完整 argv 仅替换 session selector，保留 nonce、引号及中文；运行时 canonical identity 与固定 leader 更换拒绝保持，原 launch 与已有事件历史原文未改。缺 argv、版本不符、native session 缺失、保存 argv 改动、规范身份改动各自失败；worker 不恢复且 attempt 原文不变。所有场景零 prompt write、零 auth prepare／auth 文件访问。
- 重放：`node /private/tmp/t093-shell-recheck-joPlVg/probe.mjs candidate`，退出 1；将末参数换成 `base` 对照 116985ec9，退出 1。命令与结果位置在同目录 `commands.json`；base 源码快照为 `panes-base.ts`。每次重跑重新生成 nonce 与隔离输入，不覆盖既有结果。
- 收尾 HEAD 仍为 TARGET，受控 diff 为空；原有未跟踪文件保留。地图 status 退出 0，Problems 0、Stale living docs 0；完整输出在同目录 `freeze-final.json`。
FINDINGS:
- [P1] `workbench/src/panes.ts:49` — fake shell 准入只检查单引号开头与 `; exec /bin/zsh -f -i` 后缀，未核对命令是否对应记录的完整 argv。限定新输入 `unknown-shell-command-sentinel-with-fake-envelope` 的其余字段来自实际 fake launcher，但 shell_argv[3] 换为 `'/private/tmp/unrecognized-<nonce>' 'different-input'; exec /bin/zsh -f -i`；这是未知命令，却仍标成 `restored` 并各调用 1 次 supplied 版本、PTY、process snapshot。预期应为 `restore_record_unrecognized` 且零边界调用。原 exec-only 缺口已修，但“未知 shell 默认拒绝”的同类准入缺口仍在。最小修正是核对已知 fake 启动命令与原 argv 的完整一致关系；保留 legacy 正例与原 argv/version/session 诊断，不扩大成 shell 解释器或平行恢复路径。
COUNTEREXAMPLE:
- 116985ec9 经同一限定脚本完成 19 场，仅 10 场 PASS；actual 成对输入的 exec-only 案例被标为 `restored`，各调用 1 次 supplied version／PTY／process，触发“必须未恢复”和“零边界”业务断言。新候选在该原问题上取得明确绿态。对照原件在 `/private/tmp/t093-shell-recheck-joPlVg/base-d7fd3c63/{inputs.json,boundaries.jsonl,result.json}`；不是因崩溃或缺依赖判红。
LIMITATIONS:
- 仅 L0／L1。未执行真实 CLI、daemon、PTY、OS／PID／ps／libproc 查询、auth／Keychain、网络／socket、服务或模型；没有读 auth，也未改工作树、源码、Git 或旧夹具。替身不能证明真实外部边界。
- 本限定范围仍为 NO_GO；新候选 T-096 native7 与门禁重跑仍待授权主控完成。review03 的其他范围维持原边界，本次没有新增通过结论，也不以旧证据代替新候选验证。本轮按限定要求在报告此问题后停止，不再继续扩展检查。
RULE:
- 保留实际 launcher 生成的 normal／fake 成对输入，以未知 nonce 改变 shell 命令内容但保留外壳前后缀，要求在 CLI／PTY／auth 之前拒绝；同时保留显式 fake、legacy fake 和 worker attempt 反退化断言。这是可执行的 profile 准入反例，不需要另加提示词记忆规则。
