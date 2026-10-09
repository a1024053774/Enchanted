# T-061 恢复结果（2026-10-09，ready_rev 2）

**PASS：ready_rev 2 的解析修复、红绿、116 个工具逐项对照、规定检查与一次独立审查完成。** ticket 保持 open，待主控关闭。本报告是本轮恢复记录；[上一轮 BLOCKED 记录](RESULTS.md)及其原始失败证据保留。

## 候选与交付范围

- task：T-061，ready_rev 2；worker：s11-t061b；恢复派发为主控 #4，依据 `brief-T-061-resume.md`。起点为 `a2a-t061` 分支的红态测试快照 `1ec64d866c6a37985ddfada5f22c39f9fcb15e54`，工作树干净。
- fork 候选：`aff04b5f05fefc1113cdad876b18917f387dc975`；worktree：`/Users/luckye/Documents/Code/synara-t045`；生产父修订：`2330534b2cf906b9d8f0a0b643adb370683d7fe0`。
- 生产改动只有原生提示的工具名字符范围 `[a-z_]` → `[a-z0-9_]`。完整提示匹配、显式字段优先、目录成员、身份与授权条件保持原实现；没有工具级特例、额外入口或重试。
- 这是 Herdr 期本地交付，不是工作台受管 run。brief 明确要求提交、RESULTS 和终端 DONE 行，不走门禁 submit；没有新建或接管 attempt/session/fence。主控验收、集成与关闭尚未执行。
- 六项绿态检查的运行版本与完整 diff 已逐字绑定到固定候选，见 [candidate-binding-02.json](candidate-binding-02.json)。a2a 交付提交以本报告所在提交及终端 DONE 行为准。

## 证据

| 验收信号 | 结果 | 原始证据 |
| --- | --- | --- |
| 同一 manager 入口，缺字段的三个数字名字，各覆盖 full-access 和显式授权 | 红态 6 个预期业务失败、57 个通过；修复后同一信号 63/63 通过 | [红态](permission-red-02.log)、[绿态](permission-green-02.log)，各有 `.command.json` |
| 身份与授权反例 | 三个名字逐条覆盖未授权、无 lease、撤销、非活跃、无 turn、过期 turn、错误 thread/server/kind、停止、Plan、目录外普通/数字名字；非完整提示、近似名字、显式字段优先也通过 | `permission-green-02.log`；`wrong-kind` 沿原合同 cancel，其余反例保持 pending |
| 同一目录探针，116 个名字、显式字段与缺字段两种帧 | 116 个显式字段结果不变；缺字段仅三个目标名字由 pending 转为单次 accept，其余 113 个逐项一致 | [前后对照表](catalog-comparison-02.md)、[结构化结果](catalog-comparison-02.json)、`catalog-baseline.json`、`catalog-green-02.json` |
| 相关既有套件 | 3 个测试文件，295 通过、2 跳过，退出 0 | [related-suite-02.log](related-suite-02.log) |
| fmt:check | 退出 0，匹配文件格式通过 | `fmt-check-02.log` |
| lint | 退出 0，0 errors；输出 870 warnings；同步文件系统预算检查通过 | `lint-02.log` |
| typecheck | 退出 0，8/8 package 成功；输出已有建议诊断 | `typecheck-02.log` |
| project-map status | 开始及完成前均为 Problems 0、Stale living docs 0 | `map-status-resume-02.log`、`map-status-final-02.log` |
| fresh-context 只读独立审查 | PASS；固定目标为上述 fork 候选，只做一次，无候选缺陷 | [中文审查记录](acceptance-review-resume.md) |

预期来自 ticket ready_rev 2 与已有许可合同：批准为一次 `accept`，`content`/`_meta` 为 null，pending 为 0，不持久化。目录只提供输入名字，不提供批准答案。所有反例都经过真实 manager 的许可判定；只控制其原生 I/O 与上下文，没有替换该生产判定。

`catalog-compare-02` 曾因本机 Python 3.9.6 不支持 `zip(strict=True)` 而退出 1。这是证据脚本环境错误，不是产品红态；原脚本和失败日志保留。`compare-catalog-resume-03.py` 在已明确验证名字列表完全相同、长度均为 116 后做逐项核对，退出 0。没有覆盖异常结果。

## 重放与版本

fork 根目录中执行；已有输出不覆盖，目录探针的输出使用新路径：

```sh
A2A_SYNARA_SLOT=t061 ./a2a/scripts/bun run --cwd apps/server test src/a2a/raise-permission.test.ts --reporter=verbose
A2A_SYNARA_SLOT=t061 ./a2a/scripts/bun /Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch11/T-061/native-catalog-probe.ts /Users/luckye/Documents/Code/synara-t045 /Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch11/T-061/catalog-green-replay.json
A2A_SYNARA_SLOT=t061 ./a2a/scripts/bun run --cwd apps/server test src/codexAppServerManager.test.ts src/agentGateway/computerToolPermission.test.ts src/a2a/raise-permission.test.ts --reporter=verbose
A2A_SYNARA_SLOT=t061 ./a2a/scripts/bun run fmt:check
A2A_SYNARA_SLOT=t061 ./a2a/scripts/bun run lint
A2A_SYNARA_SLOT=t061 ./a2a/scripts/bun run typecheck
```

完整 argv、cwd、时间、退出码与当时 fork diff 见各 `.command.json`；本轮由 `run-check-resume.py` 追加创建。红态第二轮收据保留了测试增量；在旧解析器上应用该测试增量即可复现包含 `synara_e2e_review` 的 6 个失败。已提交的 `1ec64d866c6a37985ddfada5f22c39f9fcb15e54` 可直接复现上一轮四个失败，第三个名字的父修订 pending 另在目录基线中保留。

本机 Codex CLI 0.162.0、Bun 1.4.2、Node v24.13.1（wrapper 核对）、Python 3.9.6；Vitest 4.1.10。未调用真实模型，供应商实际模型/tier 未核对；Herdr 版本本轮未单独核对。skill 为本地 `project-map`、`evidence-first-testing`、`document-writing`、`behavioral-acceptance-review` 文件，无独立发布版本号。

## 文件清单与局限

fork 改动限于：

- 上游原文件 `apps/server/src/codexAppServerManager.ts`：字符范围修复。
- fork 测试 `apps/server/src/a2a/raise-permission.test.ts`：保留上一轮红态测试，补第三个目录名字的两种授权正例与 13 类反例。

没有修改目录或生产授权条件，没有新的异常处理、fallback、兼容分支或平行 API，故不另做 design-integrity-review。本次为受控帧的解析与许可逻辑证据，不宣称真实 CLI 已经发生缺字段故障或正式工作台通过。两个跳过项是 `CODEX_BINARY_PATH` 未设置时默认跳过的真实 Codex resume/rollback 用例，符合本票不需真实模型调用的范围；没有运行全仓测试、桌面 build、UI、平台/迁移检查。

本轮新问题上报 0；上一轮的 submit 身份问题由恢复 brief 明确 Herdr 期交付方式，验收口径冲突由 ready_rev 2 明确三个既有数字名字同样修复。原收件箱条目与旧报告不改写，处置由主控负责。没有停止或重启任何服务，没有访问正式工作台数据，没有改用户配置，没有 push；其他 worker 的 dirty files 保留。
