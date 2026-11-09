# T-249-1 第五次派发：候选恢复与机械复验

**PASS（候选恢复与本卡机械条件）**：原样接回候选，保留旧红态，三条机械检查全部通过，代码已用当前身份提交。

**INCOMPLETE（交付接收及整票验收）**：本报告写入时尚未执行最终 submit；提交报告后显式请求一次，由 Stop hook 转交。排队不等于门禁接收。独立审查、真实窗口、新包、terra 验收、敏感证据批准与集成均待主控完成。

## 身份与恢复范围

- task：`a2a+T-249-1`；attempt：`b33751df-0d57-4223-834d-4d467b199e22`；session：`dcfd69d9-6557-4901-bd83-24bb348f0693`；fence：`4`；spec_rev：`5`。
- 当前基线：`b7cce248c5ed85dd9342ade10886287365273863`。
- 按卡运行 `git diff --binary 8683c4edba5ff635fea7e2918af059e4cd5ba07c 9f96a9121ba6ed8d77a514a0a78c9341ceaacb86 | git apply`，随后独立执行 `git add --sparse` 与 `git commit`。恢复提交为 `6e6af856f91b617ac7e8827f363947678ab17efb`；最终交付提交还包含本目录证据，其完整号以 submit 请求为准。
- 57 个导入文件均在卡内，逐文件 Git diff 与旧候选无差异。两条 P2 修复和 no-panel 必跑编排仍在，没有重新实现或扩大产品范围。全部新增工作仅为本目录的本轮证据和复验脚本。
- 提交钩子自动记录 `codex-cli 0.167.0`、`gpt-6-astra`、`xhigh` 和当前 attempt/session；没有手写尾注。环境为 Node `v26.5.0`、Git `2.52.0`、完成条件 Python `3.9.6`，详见 [run-context.json](run-context.json)。这些是版本及启动记录信息，不宣称已验证供应商实际 tier。
- 未改 `acceptance/**`、根目录 `REVIEW.md`、门禁、依赖清单或锁文件。没有 T-250、T-255、T-256、T-257、T-258 修改，没有新依赖。

## 本轮运行与证据

实际运行封装：`/usr/bin/python3 evidence/2026-11-07-batch33/T-249/attempt-fence4/run_checks.py`。封装按下表原始 argv 执行，并将三个互不共享的临时目录放在 `A2A_REQUEST_DIR=/private/tmp/a2a-requests-0vSJrb` 下。stdout、stderr、命令、工作目录、TMPDIR 与退出码均保存到对应文本。

| 原始命令 | 本轮结果 | 证据 |
| --- | --- | --- |
| `/usr/bin/python3 acceptance/T-249/check_git_graph.py` | PASS，exit 0 | [acceptance.txt](acceptance.txt) |
| `/opt/homebrew/Cellar/node/26.5.0/bin/node --test workbench/tests/test_t249_git_host.mjs` | 22/22，exit 0 | [host.txt](host.txt) |
| `/usr/bin/python3 workbench/tests/test_t249_outside_safety.py` | 5/5，exit 0 | [outside-safety.txt](outside-safety.txt) |

无界面验收核对 all/current 两种范围的顺序、父提交、完整引用、HEAD、泳道、merge 连线、未提交文件数，以及创建／删除分支和拒绝以 `-` 开头的名字。宿主检查补足单文件字面路径、无 HEAD 详情、受管写保护、读取不改元数据和 HEAD 虚线终点。脚本检查只证明编排分类与清理逻辑，不替代真实窗口。

夹具没有放进受管 worktree。三个测试均自行移除夹具；本轮再保存临时目录体量和状态后移除空临时根，见本目录三个 `*-cleanup.json`。没有构建、缓存、临时依赖或待清理进程。没有修改额外可写目录（派发为 `[]`）；请求目录只用于本轮允许的临时测试和门禁请求，请求文件不进入 Git。

源码和文档的 `git diff --check b7cce248c5ed85dd9342ade10886287365273863 HEAD -- workbench/app/ workbench/tests/ workbench/README.md` 退出 0。导入时 git apply 报告的 20 处行尾空白来自原有工具输出记录，保留原始证据，没有改写以消除警告。

## 旧证据保留与自查

旧 `attempt-fence2/`、`attempt-fence3/`、`headless-redgreen/` 和此前 RESULTS 原样保留。尤其保留 `attempt-fence3/acceptance-final.txt` 的误放夹具失败，以及解释其来源的 `acceptance-fixture-location.json`；本轮没有重演该错误，也没有把旧文件名里的 final 解释为通过。

两处 P2 的旧红态见 [host-red.txt](../attempt-fence3/host-red.txt) 和 [unborn-diff-red.txt](../attempt-fence3/unborn-diff-red.txt)，旧编排红态见 [outside-safety-red.txt](../attempt-fence3/outside-safety-red.txt)。本轮核对它们与当前修复的对应关系并实际重跑绿态，未重复无关测试。

按 design-integrity-review 做恢复范围实现者自查，按 behavioral-acceptance-review 说明独立 oracle、已知坏实现和层次限制，详见 [本轮自查](REVIEW.md)。这不是门禁独立审查，也不将模型不符的旧审查 01 结论用作通过依据。

没有运行全仓测试：本轮只恢复已有候选，产品源码及开发测试与来源一致；完成条件已按当前基线重跑。旧标准构建通过仅是历史证据，本轮没有构建。真实窗口、no-panel/parents/order 窗口反例、Esc 与焦点限制、watch 时序、拖宽和菜单行为均未验证。

开工 `project_map.py status` 退出 0，Problems 0、Stale 0。恢复敏感脚本后收尾退出 1，Problems 0、Stale 1，仅 `REVIEW.md`，见 [project-map-status.txt](project-map-status.txt)。按卡由主控核对 Verified，worker 不修改；T-257 的 Resolution 没有再报错，没有重开旧问题。

## 主控后续操作

门禁独立审查通过后，在本交付候选 worktree 的沙箱外使用全新 slot：

```sh
bash workbench/app/RUN-OUTSIDE-T249.sh t249-fence4-review-20261108
```

脚本沿用旧候选代码，输出目录仍是 `attempt-fence3/outside-<新时间戳>/`，本轮未改这个路径；运行结果须按实际候选与 attempt 记录归属，不能误称为上轮运行。脚本包含真实窗口绿态、no-panel、parents、order 三个指定业务断言红态，以及 `npm run package:mac -- --variant test --slot <slot>` 打包。启动失败不能算红态。

主控还需核对正式 Enchanted 的 PID／启动时间和用户 hc core 前后不变，再让 `gpt-6.1-terra` 用 Computer Use 与常规测试验收新打出的 Enchanted Test。不能用正式旧包宣称新面板已通过。用户读完整敏感脚本证据并批准后，再经唯一门禁集成；本 worker 不集成、不 push。

本轮证据提交后按任务卡显式 submit 一次，不重复请求、不向终端补 Enter。若 CLI 返回 queued 或 delivered=false，只报告已排队，门禁接收状态由 Stop hook 转交后核对。

**Works**：原样恢复 57 个卡内文件，两处详情修复与 no-panel 编排保留；三条机械条件在本 attempt 全部通过。

**No regression**：宿主 22/22、脚本 5/5、冻结验收和源码／文档差异检查通过；全仓、构建与窗口没有重跑。

**Risk / undo**：交付接收、整票独立验收及敏感脚本批准未完成。主控可经门禁拒收或回收本 attempt；原候选及旧红态保留，本轮未操作 main 或其他任务引用、正式应用或后台。
