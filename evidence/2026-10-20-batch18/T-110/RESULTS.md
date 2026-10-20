# T-110 / a1

状态：INCOMPLETE。应用内通知、设置和 Dock 接线已实现；本地合同及构建通过。真实入口首轮发现侧栏高亮被覆盖，已修复，等待主控用当前候选重跑；地图验收受稀疏检出影响。

范围只含 T-110。未修改 panes.ts、启动参数、模型与强度设置、门禁和全局 CLI 配置；未调用模型或 push。起点为 `e3102389eda8952ea92cae4b373e14eaff898314`，分支 `exec/t110`。任务 T-110，attempt a1；worker 启动记录 `launch-d008aad4e92d4bbc86a75109c7625d0f`，session `08655309-afa5-40e1-90b5-70da288741da`。提交尾注由已有钩子生成。本沙箱尝试 `git add --sparse` 被 worktree 的 `index.lock` 写权限拒绝，未申请升级；主控需运行下方提交脚本。

## 行为与验收

- PASS（本地合同）：只消费 T-108 已核实的 `waiting_user_answer`，sidebar 只增加该问题 ID。未知、权限等待、等待主控回答、运行与空闲不产生提醒。保留 T-108 的可信度判定，不读取终端文字推断。
- PASS（本地合同）：同一个问题在当前应用进程只提醒一次；按 ID 去重，换问题可产生新提醒。回答、取消、结束或未知导致待答列表移除。关闭再开启不重放已观察的问题。
- PASS（本地合同）：通知与 Dock 两个设置独立保存；Dock 用 `app.dock.setBadge`，后台显示待答数量，前台清空，多窗口不重复计数。
- PASS（代码检索）：生产目录没有 Electron／Web Notification 调用或通知授权请求。检索命令与逐条结果见 `notification-api-search*.json`；测试中的旧 Notification 边界仅用于捕捉违规调用。
- INCOMPLETE（真实入口）：首轮隐藏通知变异体被业务断言拒绝；正常候选实际渲染一条通知，失败在高亮颜色断言。已将待答 CSS 选择器加上行类，解决选中项目和 agent 基础样式覆盖；保留精确颜色断言。原件 `/private/tmp/t110-outside-01.json`，摘要 `outside-01-failure.json`。当前候选的点击聚焦、回答移除、去重、禁用及真实 Dock 尚待同一入口复验。
- INCOMPLETE（治理）：启动地图检查为 8 问题、0 stale，全部是稀疏检出缺失链接／文件；已发 inbox issue `20261020T124545Z-worker:s18-t110-issue-001`。由主控在完整 checkout 重跑，不改地图。

## 本地证据

- `node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs <新摘要.json>`：修前 `contract-red-02.json` 在缺少应用内通知的业务断言失败；修后 `contract-green-02.json` PASS。原有 IPC 身份、越权、只读、旧窗格、关闭与空布局拒绝检查均保留，22 个 handler／23 个 bridge 名称不变。
- `node workbench/tests/test_t108_questions.mjs <新摘要.json>`：`questions-green-01.json` PASS，包含 429 个 hook 异常案例和 14 个作答生命周期案例。
- `node workbench/tests/test_t107_sidebar.mjs <新摘要.json>`：`sidebar-green-01.json` PASS，真实 Git／SQLite 投影只读回归。
- `node workbench/app/build.mjs --slot <唯一槽名>`：三次构建 PASS；临时输出与缓存已清理。语法及 diff 检查见 `local-checks*.json`。运行环境 Node 26.5.0、Python 3.9。
- `npm ci --ignore-scripts`：安装于本 worktree，成功。安装器报告 3 个 high 依赖漏洞，已随上述 issue 上报；本票未升级依赖。

## 最小接线位置

`sidebar.ts` 119–128 行只增加已获准问题的 ID，168 行移除已失效的提问信号缺口文案。`renderer.tsx` 14–15 行 import、41／48 行类型、419–427 行状态接线、461 行失败清除、497 行切回终端、573–585 行设置区块与通知组件。设置区块的实现位于新组件；`style.css` 135 行修复待答高亮优先级。实际行号以最终提交为准。

## 主控复验

```sh
zsh evidence/2026-10-20-batch18/T-110/RUN-OUTSIDE-NO-MODEL.sh /private/tmp/t110-outside-02.json
```

脚本复制源码和本 worktree 的依赖到私有测试目录，只在该副本改 spawn-helper 执行位。使用 T-108 的 controller_start → 已安装 Claude → 本地假 API → 真实 Electron → 原 PTY 作答通路，不调用模型或供应商，不保存截图。依次运行隐藏通知的坏变异、正常闭环、禁用通知；断言通知 ID、DOM 新增次数、项目和会话实际高亮颜色、流程页切回并聚焦原窗格、回答后清除、真实 Dock 角标及开关。默认 Electron 位于内置盘，可用 `T110_ELECTRON_DIST` 指定。

原始运行及夹具仍在摘要所指的 `/private/tmp` 下，待主控按 T-088 归档外置盘；未删除失败现场。独立只读审查与完整 checkout 的地图复验仍由主控完成，不将本 worker 自查算作独立审查。

沙箱外提交（已有 hook 自动写尾注，脚本绑定本 worker 身份）：

```sh
zsh evidence/2026-10-20-batch18/T-110/RUN-OUTSIDE-COMMIT.sh
```

环境补充：内置盘曾报空间不足（116 MiB），只清理了已退出首轮私有副本的可再生依赖后约余 320 MiB；问题已上报 `20261020T125909Z-worker:s18-t110-issue-001`。原生 CLI 在隔离 home 内自行创建了 latest 日志链接和 URL Handler 的 claude 链接，测试脚本未用链接接源码、依赖或共享构建目录；归档时应记录链接本身，不复制其外部目标。

归档脚本（外置盘缺失即失败，保留本地原件、不计算校验值、不新建链接；须传入所有实际运行摘要）：

```sh
zsh evidence/2026-10-20-batch18/T-110/RUN-OUTSIDE-ARCHIVE.sh final-01 evidence/2026-10-20-batch18/T-110/final-01.archive.json /private/tmp/t110-outside-01.json /private/tmp/t110-outside-02.json
```
