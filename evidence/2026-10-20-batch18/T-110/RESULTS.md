# T-110 / a1

状态：INCOMPLETE。第六轮三个红态成立，green 已恢复同一问题，但首个作答回执超时。已查明产品在 socket 连接前消耗窗口序号，修后改为连接成功才分配。本地修前红态、修后合同、IPC、T-108 和构建通过；e1c7b5c27 同场景对照、完整真实入口和独立复审仍待主控。原生回执成功断言未放宽。

范围只含 T-110。分支 `exec/t110`，本轮起点 `4a6d6bb9ecefc2bb16196b326ff032726d4d16fb`，初始实现起点 `e3102389eda8952ea92cae4b373e14eaff898314`。任务 T-110，attempt a1；worker launch `launch-d008aad4e92d4bbc86a75109c7625d0f`，session `08655309-afa5-40e1-90b5-70da288741da`。不修改 panes.ts、CLI 启动参数、模型设置、门禁或全局配置，不调用模型、不 push；尾注由已有钩子生成。

## 行为与验收

- PASS（合同及原候选真实正常入口）：信号只取 T-108 已核实的 `waiting_user_answer` 及问题 ID；未知、权限等待、等待主控回答、运行和空闲不提醒。项目／会话高亮、应用内通知、点击聚焦及原 PTY 作答共用现有入口。
- PASS（合同及原候选真实正常入口）：按问题 ID 去重；问题回答、取消、结束或未知时移除。通知和 Dock 设置独立保存，关闭再开启不补发已观察的问题。同一问题在本次应用进程只提醒一次。
- PASS（本地红／绿）：F1 的修前 `review01-disconnect-red.json` 在“断连后角标应清零”失败，实际 1、期望 0；修后 `review01-disconnect-green.json` PASS。传输异常与后台 `ok:false` 均使同一状态目录的中心失效，清除 active／waiting，保留 seen，重算 Dock；原始错误继续返回，失败不重试，也不伪造成功快照。
- INCOMPLETE（新真实入口）：第六轮三个旧坏候选均取得业务红态；green 的恢复／去重已过，作答回执失败。现场最后接纳 seq 14，恢复首条命令为 seq 17，后续共 10 条 invalid_window_sequence，没有 window_answer 到达 daemon。当前修复及 e1 对照方案见 `FOLLOWUP-ANSWER-RECEIPT.md`；第七轮仍须完整闭环，不能用已通过的前半段代替。
- PASS（检索）：生产 app／src／hooks 中没有 Electron／Web Notification、APNS 或通知授权请求调用，当前检索在 `review01-local-checks.json`；仅有 `app.dock.setBadge` 写应用角标标签。
- INCOMPLETE（治理）：稀疏检出使地图检查报 8 个缺失链接／文件、0 stale，已上报 `20261020T124545Z-worker:s18-t110-issue-001`。完整 checkout 的 status 与独立复审由主控完成，worker 不改地图，不把自查算作独立审查。

Dock 权限的准确边界：**当前固定版本 Electron 43.4.1 的 `setBadge` 不会主动请求权限，但不能证明在拒绝通知权限时角标一定可见。** 测试通过 `app.dock.getBadge()` 核对标签值，未验证所有权限状态下的视觉显示，也未修改或请求系统权限。继续使用 `app.dock.setBadge`，没有更换 API。来源核对见 `independent-review-01.md`。

## 当前证据

- `outside-06-summary.json`：第六轮三个红态、green 已通过的检查、无答复请求、序号缺口及旧 native 清理异常。`receipt-sequence-contract-01.json`：实际 main／transport 的修前红态与修后绿态；`receipt-ipc-01.json`、`receipt-questions-01.json` 和 `receipt-local-checks.json` 均 PASS。真实 socket／Electron／CLI 仍待沙箱外执行；e1 与 4a 的 main／transport 无差异不等于已实跑 e1 的回执。
- `review01-disconnect-red.json`／`review01-disconnect-green.json`：实际 main/preload 模块、受控传输边界的业务红／绿。修后还核对异常原对象传出、拒绝原因保留、单次读取、焦点变化不复活旧计数、恢复不重发同一问题、另一窗口共享去重结果。原 22 个 handler／23 个 bridge 名称及全部窗格身份、越权、历史、只读、关闭和空布局拒绝检查保留。
- `reconnect-view-red-02.json`／`reconnect-view-green.json`：当前刷新回调的业务红／绿；`reconnect-ipc-green.json`、`reconnect-snapshot-green.json`、`reconnect-questions-green.json` 均 PASS，后者包含 429 个 hook 失败案例及 14 个作答生命周期案例。`reconnect-local-checks.json` 记录当前构建及清理。`reconnect-view-red.json` 是最初探针未剥离 TS 语法的配置失败，不计入业务红态。
- `review01-local-checks.json`：构建、语法、diff 与系统通知 API 检索 PASS；本次临时构建和缓存已清理。`review01-structural-scan.json` 是定位器输出：主进程新增 catch 负责失效后重新抛错；另两个 marker 属于主控提供的旧审查脚本，不是本次新生产代码。扫描结果不冒充独立审查。
- `/private/tmp/t110-outside-03.json`：主控运行的原候选正常和禁用场景 PASS，隐藏通知变异被拒；精简摘要 `outside-03-summary.json`。第一轮独立审查把该证据与 c5ac40c0b 绑定，但仍因 F1 判 NO_GO。
- 原实现的红态、首轮高亮缺陷和早期检查仍保留在 `contract-red-*.json`、`outside-01-failure.json`、`local-checks*.json` 等文件。用户／主控已清理部分旧 t108／t109／t111 临时目录以腾空间；旧摘要不能证明原始夹具仍在。当前合同重新创建夹具，新的原生运行集中在 `/private/tmp/t078-2-t110-*`。
- `npm ci --ignore-scripts` 安装于本 worktree，未借用依赖链接。原安装器报告的 3 个 high 依赖漏洞已随上述 issue 上报，本票不升级依赖。

## 接线位置

本轮生产代码只改 `main.ts` sendWindowCommand（123–143 行）与 `transport.ts` request 的签名／发送点（19–34 行），将序号分配移到 socket 连接成功之后。renderer、sidebar 和设置页本轮未改。上一轮 renderer 刷新顺序修复仍保留；F1 的通知失效与 Dock 重算仍保留，原“同一问题回来且不重复提醒”和首个作答最终回执断言均保留。

## 主控运行命令

扩展真实入口（新路径，不覆盖已有结果）：

```sh
zsh evidence/2026-10-20-batch18/T-110/RUN-OUTSIDE-RECEIPT-COMPARE.sh /private/tmp/t110-receipt-compare-01.json
zsh evidence/2026-10-20-batch18/T-110/RUN-OUTSIDE-NO-MODEL.sh /private/tmp/t110-outside-07.json
```

对照入口两版均执行额外一次可见恢复刷新及界面重载，以使 e1 到达原作答入口；完整入口保留原来的自动保留项目检查和手动窗格重连，新增 4a6d6bb9e 的作答红态，共六个运行。使用本地假 API、真实已安装 Claude、Electron 与原 PTY，不调用模型或供应商，不保存截图。spawn-helper 执行位只在私有依赖副本修改；Electron 从内置盘运行。最新判断、断言边界及证据见 `FOLLOWUP-ANSWER-RECEIPT.md`。

沙箱外提交脚本绑定本 worker 身份及既有钩子，检查分支与 4a6d6bb9e 起点，使用 `git add --sparse`。本沙箱的 worktree Git 元数据不可写，未申请升级：

```sh
zsh evidence/2026-10-20-batch18/T-110/RUN-OUTSIDE-COMMIT-05.sh
```

归档本轮夹具（外置盘缺失即失败；只核对文件数和字节数，不计算校验值，不删除本地原件）：

```sh
zsh evidence/2026-10-20-batch18/T-110/RUN-OUTSIDE-ARCHIVE.sh reconnect-01 evidence/2026-10-20-batch18/T-110/reconnect-01.archive.json /private/tmp/t110-outside-04.json /private/tmp/t110-outside-05.json /private/tmp/t110-outside-06.json
```

原生 CLI 在隔离 home 自行产生的链接只记录为文字，不复制外部目标、不创建链接。新原生夹具归并在本轮私有根目录内后统一归档；失败现场保留。旧运行缺失的原件不伪造归档成功。

额外问题：旧 `REVIEW-OUTSIDE-01.sh` 的真实入口夹具路径预计不满足既有 `/private/tmp/t078-2-` 根校验（静态发现，未当作业务红态）；已上报 `20261020T133157Z-worker:s18-t110-issue-001`，未改独立审查原件。

第六轮 native 清理身份变化另已上报 `20261020T141307Z-worker:s18-t110-issue-001`；未放宽身份检查或处理不确定进程，见 `ISSUE-OUTSIDE06-CLEANUP.md`。

本轮快照证据：`snapshot-red-01.json` → `snapshot-green-01.json` 验证实际驱动表达式的 JSON 传输契约；真实错误文本仍须出现，断连后无通知、无角标和恢复去重的断言均未放宽。第四轮范围与修复原因见 `FOLLOWUP-SNAPSHOT.md`、`outside-04-summary.json`。
