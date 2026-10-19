# T-106 / a1：简化表单候选

2026-10-19。**INCOMPLETE**：表单、现有门禁调用与局部检查完成；真实 Electron 验收和独立审查尚未取得本候选结果。提交交接脚本已准备，须主控在沙箱外运行。没有启动主控、agent CLI 或模型，真实模型根回合 0，假 API 请求 0；没有截图，没有 push。

本轮按主控 #40 和 main `b0e12a88c` 的用户裁定“B 简化表单,不用主控 (Recommended)”执行，取代早先主控补卡方案。早先阻塞报告及探针保留在历史中，不拿它们替本候选背书。

## 绑定与范围

- task `T-106`、attempt `a1`、分支 `exec/t106`，本轮起点/已知坏版本 `f88f6f6927d4b836fc502898b6309e5e21e14b4c`。
- session `46c7c0a5-076f-48e7-adc0-4aea62a637a9`、launch `launch-d83c474a34f148c19f8e35e9bd60ff71`；派发环境未提供 fence/spec_rev，不推断其值。ticket 的 ready_rev 仍为 1，执行要求取其裁定节与本轮派发。
- 目标：一张表单填写项目号、选择仓库、填写任务，并经既有 operator 门禁命令注册。非目标：独立项目表、模型补卡、派 worker、修改门禁格式规则、git init 或自动创建提交。
- **Tracer bullet**：先贯通表单选择仓库 → 模板 → 校验 → 保存 → 注册 → 列表刷新；再补格式拒收、取消、窗口权限及原 IPC 合同回归。
- **Deep modules**：门禁核心仍拥有校验与写库；界面只维护窗口内草稿、原生目录选择和显式确认，不新增门禁 API 或存储。
- **Ubiquitous language**：沿用项目、任务、任务卡和门禁。项目号就是列表名称，项目随首个任务隐含出现，不伪装成可独立保存的空项目。

## 实现与逐项验收

| 验收项 | 当前状态与证据 |
| --- | --- |
| 空库表单创建项目与首个任务，列表显示 | 已实现。“新建项目与任务”在空库可用，已有项目下有“新建任务”。真实 Electron 待主控运行脚本；不宣称 PASS。 |
| 目录由主进程原生对话框选择，renderer 不能传路径 | 主进程保存仓库；三个新 handler 都核对 sender/mainFrame。局部实际 main 模块的路径注入、未知窗口、iframe、跨窗口草稿反例 PASS。真实原生目录选择待验证。 |
| 只调用原命令、operator 身份、同库语义 | main 取 `card_template`，确认后依次调用 `card_validate`、`card_save`（expected_version 0）、`create`。局部路由及完整 card/元数据转交 PASS；真实库与 CLI 对照待验证。没有改 daemon、gates、锁或校验规则。 |
| 确认前任务不存在、取消无残余 | 确认前不调用 save/create；取消清除窗口草稿。局部无写入与取消检查 PASS；真实库计数待验证。门禁命令的操作锁及追加式审计记录仍沿用原合同。 |
| 缺字段、完成条件不是命令时可见拒收原因 | UI 显示阶段、门禁错误码及 details。局部门禁拒收转交 PASS；真实格式校验待 Electron 脚本验证。JSON 语法错误直接显示为未提交。 |
| 其余任务卡字段有默认值、可见可改 | JSON 字段区展示编号、来源、非目标、路径、验收文件、红态命令、类型、复杂度、执行器、起点与写入者。默认允许整个仓库、禁止 `.git/`、验收文件 `tests/`、复杂度 M、Codex/gpt-6.1-sol/xhigh；README 与表单都要求按仓库实际情况修改路径。 |
| 已知坏实现对照红态 | 实现前的实际 main 入口因缺少创建 IPC 退出 1，见 `form-ipc-red-02.json`。真实 Electron 的基线对照脚本已写，尚未运行。 |
| IPC 名称集合和原拒绝检查 | PASS：17 个显式 handler、18 个桥接名称；旧 key、iframe、跨窗口、历史 worker、凭据/序号、关闭/恢复、已知坏版本和原有变异断言全部保留并通过。 |
| 模型、全局配置与截图 | 模型根回合 0、假 API 请求 0。没有读取正常登录凭据，没有写用户全局 CLI 配置，没有截图。 |
| project-map | INCOMPLETE：稀疏 checkout 起止均有 8 个既有缺文件诊断，stale living docs 0。没有改地图或其他 ticket。 |

确认不是跨两个命令的事务：任务卡保存后若 create 失败或响应未知，已保存记录会保留。表单明确提示，禁用再次提交，按钮改为“关闭表单（保留已保存记录）”；不把它叫取消，也不自动重试或删库。任务卡格式拒收发生在保存前，可修改或取消。此处沿用已有门禁语义，没有另发明回滚或补偿路径。

## 已执行的检查

```sh
node --experimental-vm-modules workbench/tests/test_t106_creation.mjs evidence/2026-10-19-batch17/T-106/form-ipc-final-01.json
node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs evidence/2026-10-19-batch17/T-106/pane-ipc-final-01.json
node --experimental-vm-modules workbench/tests/test_t105_panes.mjs
```

以上均 PASS。前两项执行实际 main/preload 模块，但 Electron/transport 边界由测试提供；不是 GUI 或实际后台的证据。新局部测试覆盖保存失败不继续 create、并发确认互斥、临时 card 文件清理及部分注册结果可见。测试中的输入与期待值取自派发合同及独立 sentinel。

在 `/private/tmp/t106-buildcheck-*` 中复制本候选 app/src 和本机现有依赖副本，运行标准命令 `node app/build.mjs --slot candidate-final-01`：PASS，见 `form-build-final-01.json`。构建成功后临时源码、依赖与输出均已清理；未改共享 checkout 的依赖或输出。Vite 仍有大于 500 kB 的 chunk 提示。本轮未打包或安装应用。下述 Electron 脚本可重建同一 UI。

driver 的 `node --check`、两个 shell 的 `bash -n`、新 runner/嵌入 Python 的 3.9 语法检查、UTF-8 回读与 `git diff --check` 均已执行。尚未用外部的实际 Python 3.9 运行脚本。

失败证据未覆盖：`form-setup-failure-01.json` 是夹具继承 worker Git hook、摘要目录未展开导致的设置错误；`form-ipc-green-01.json` 是测试误用 assert.rejects 接同步 throw；`form-ipc-green-02.json` 是测试夹具 `/var` 与 `/private/var` 路径未规范化。均已修正测试设置，不将这些错误当作产品红态。项目号的 HTML pattern 还经 Node RegExp 的 `v` 语法检查，避免浏览器把未转义的短横线当作无效 pattern。

## 主控运行

先提交冻结候选，再运行真实验收：

```sh
cd /Users/luckye/Documents/Code/a2a-wt-t106
bash evidence/2026-10-19-batch17/T-106/RUN-OUTSIDE-02-COMMIT.sh
bash evidence/2026-10-19-batch17/T-106/RUN-OUTSIDE-01-ELECTRON.sh 01
```

提交脚本核对分支、起点、暂存路径及没有未暂存产品改动，带回本 worker 的非秘密启动身份，仍由现有 hook 自动添加尾注。本 worker不申请升级；共享 Git 元数据的写入按已知沙箱边界交主控执行。

Electron 脚本在内置盘临时目录复制当前候选与固定基线，`npm ci --ignore-scripts`，只改测试副本 helper 的执行位；默认使用主 checkout 的内置盘 Electron 43.4.1，可用 `T106_ELECTRON_DIST` 指定同版本内置盘 dist。既不安装应用，也不操作用户正在运行的应用、Herdr 或用户数据。

脚本会两次输出 `NATIVE_DIALOG` 和临时仓库路径。主控须在对应测试 Electron 的原生目录对话框中选择该路径；每次等待 180 秒。没有伪造对话框结果，也没有通过 renderer 注入路径。目录选择之外的表单操作、真实门禁拒收及两份库的独立 CLI 对照由脚本执行，不保存截图。若未选目录、退出未知或验证失败，会写 INCOMPLETE 并保留现场路径。通过且所有自有进程退出已核对后，清理临时构建、依赖与夹具，只留 `form-electron-01.json` 文本摘要；换新编号可复跑，不覆盖旧结果。

真实验收比较 UI 所写任务记录与同一库 CLI status；再在独立库通过同一四条命令直接注册相同外部输入，逐字段比较任务及任务卡快照，只排除独立生成的 snapshot UUID。另检查缺字段、非 argv、不可执行命令、取消前后五个相关表的计数，以及完成条件没有在注册时被运行。

独立审查尚未完成。[behavioral-acceptance-review](/Users/luckye/.agents/skills/behavioral-acceptance-review/SKILL.md) 要求 “Review one frozen candidate snapshot in a fresh, read-only context.” 本 worker 的自检不满足独立性；请执行主控在候选冻结后另开只读审查。本报告不把候选或局部 PASS 上调为 T-106 验收 PASS。
