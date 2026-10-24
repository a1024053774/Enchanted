# T-161-1 / a1：修前调查

状态：PLAN / INCOMPLETE。基线 `3c56f743f`，唯一写入者 b24-t161。

目标是消除只读查看的输入错误，并让批准确认后的主控窗格头同时显示载体和角色。非目标是更改门禁权限、终端协议、角色申请或 T-159 的分屏行为。

验收以真实隔离 Electron 中的审查员、历史 worker、可写 worker 和已确认主控为准，不使用模型。测试先由真实门禁启动受控 PTY worker，形成候选并启动 reviewer，再撤销另一 worker 的 attempt；输出含真实 PTY 焦点模式序列。相同脚本在修前版本须暴露 F02/F07，修后重跑，并用变异确认观察器能拒绝坏实现。可写 worker 的超限输入经真实 IPC 拒绝，须仍有错误横幅。

源码调查：`renderer.tsx` 的 `createFocusSafeWriter` 回调无条件调用 `observeFocus`；只读窗格不获 `window_open` 输入凭据，`main.ts` 的 `sendWindowCommand` 因无 identity 拒绝，错误由 `failInput` 展示。焦点模式处理仍须执行，以免 xterm 发回自动输入；需要阻止的是只读视图发送输入通道观察。

角色标识：`sidebar_snapshot` 已投影确认角色；原始 launch 保持 `shell`，窗格头仅按原始 role 渲染。计划把现有侧栏的确认角色传给窗格，在“普通终端”后追加角色；不把原始 shell 改成 controller。

`renderer.tsx` 由 T-157 占用。计划修改输入焦点条件、焦点观察条件、窗格角色属性与头部标签，已通知主控；等待合并通知与 rebase 后才写产品代码。`main.ts`、`preload.ts` 目前没有必需改动。

项目地图起始检查：Problems 0，Stale living docs 0。真实 Electron 不在当前沙箱运行，执行脚本为 `RUN-OUTSIDE-01.sh`；红态尚未取得，产品修复尚未开始。
