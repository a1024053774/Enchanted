# 正常登录恢复的明确拒绝

**局部逻辑 PASS；整票 INCOMPLETE，新 OS 与 T-096 原生七场尚未运行。**
限定独立审查 [NORMAL-RESTORE-REVIEW-17.md](NORMAL-RESTORE-REVIEW-17.md) 对代码候选 91cd22d523af28ab9a13631d6919635be430ba34 给出 PASS；归档后的最终候选不再改产品或测试。该 PASS 仅覆盖 #125 的局部合同，不代替整票 OS／原生验收。

依据是主控 #125／#31 的明确裁定：“正常登录的主控记录不在恢复路径里续接。” recover 须在任何 CLI 命令前识别 `authentication="isolated normal login"`，保留为“未恢复”；假 API 恢复仍沿 T-096。完整重建 R/F/D/C 生命周期属于新范围，另票处理。本次不改门禁、app 或全局配置，不读真实 auth，不运行真实 CLI／OS 查询／网络或模型。

## 行为与已知限制

panes.ts 在原 worker／controller 身份检查之后、旧进程查询／argv／版本／session／PTY 之前拒绝正常登录记录。当前产品写出的正常登录持久标记就是上述 authentication 值；不增加别名或根据 env 猜测登录方式。即使调用者提供外层环境变量，也不续接该记录。

原 `pane_restore_failed` 事件及 status 路径返回 `normal_login_restore_requires_protected_start`，中文 details 为“正常登录会话不自动续接，请经正常登录入口重新启动。”窗格、位置、历史 launch record 保留，其他窗格继续恢复。现有界面显示“未恢复”及明确错误码；中文重启指引在状态接口 details 与 README，不声称改了界面映射。

正常登录自动续接是明确不支持的能力，用户须从正常登录入口重新启动。该限制不等于实现了受保护的 resume。假 API 主控仍核对完整 argv、版本、session 和规范运行身份，旧历史记录不补写；worker 不续接、attempt 不变。

## 红态、绿态与反例

- [normal-restore-red-17.json](normal-restore-red-17.json)：从 `git show 8771ba58d71a3fc025b09e32c45096b39858572e:workbench/src/panes.ts` 读取精确旧源，复制 [独立探针原文](normal-independent-review-16.mjs) 到新临时目录，仅把源读取位置改为该快照。原案例／oracle 不变；rc 2，正常登录 session 存在时 calls 精确为 cli-version、pty-spawn、given-process-snapshot，并记 pane_restored；历史不变。这是业务红态，不是环境错误。
- [normal-restore-green-17.json](normal-restore-green-17.json)：同一探针，仅更换输入源快照和输出版本标签。正常登录 session 存在／不存在两场均 calls=[]、starts=0，事件 pane_restore_failed，明确错误码；历史不变。fake-control 仍依次执行给定版本、PTY、process snapshot，记 pane_restored。rc 0。
- [t096-restore-red-17.json](t096-restore-red-17.json)：扩展的实际 recover／SQLite 合同在 8771ba58d 上命中“Normal-login restore must stop before version, identity and PTY boundaries”，rc 1；文件按旧测试格式为 INCOMPLETE，保留原字，不改写 PASS。
- [t096-restore-green-17.json](t096-restore-green-17.json)：合法缺 executable_path 的两个旧记录正例保留；三种身份模式各核对 19 个命名不变量，新增正常登录两个 session 条件、明确 status／重启提示／历史不变。删正常登录拒绝、缩短实际 argv、删身份一致性检查、固定 leader 及旧 worker 坏实现均被各自业务断言拒绝；不把多模式数量冒称独立端到端场次。
- [T-091 IPC](t091-ipc-regression-17.json) 19 项与 [T-096 daemon](t096-daemon-regression-17.json) 7 场局部回归通过，均使用给定边界，没有真实 Electron／daemon／CLI。

局部合同命令（输出须为不存在的新路径）：

```sh
git show 8771ba58d71a3fc025b09e32c45096b39858572e:workbench/src/panes.ts > /private/tmp/新的旧源快照.ts
node --experimental-vm-modules workbench/tests/test_t096_restore.mjs /private/tmp/新的红态.json /private/tmp/新的旧源快照.ts
node --experimental-vm-modules workbench/tests/test_t096_restore.mjs /private/tmp/新的绿态.json
```

第一项测试预期 rc 1，第二项 rc 0；旧源不能覆盖产品工作树。独立探针的原文、旧失败和新观察均保留，输入选择／精确 node 命令／临时路径记录在对应 red／green JSON 的 replay。临时 SQLite／整套夹具不入 Git。没有实际 auth 读取边界，也没有据此宣称 OS 权限已实测。

新候选的 OS 编译、443 无模型链与 T-096 七场仍须主控在沙箱外按 [请求 16](REVIEW-REQUEST-T093-16.md) 顺序执行，初始化继续逐屏批准。原生恢复回归失败即按主控要求交回 T-096，不放宽旧断言，不自动补 Enter。

独立摘要与探针原文分别保留为 normal-restore-independent-17.json／NORMAL-RESTORE-INDEPENDENT-17.mjs；不把约 30 KB／35 KB 的原始状态输出或 SQLite 夹具放入仓库。复跑须把探针复制到全新临时目录，并用 `git show 8771ba58d71a3fc025b09e32c45096b39858572e:workbench/src/panes.ts` 在该目录创建 `known-bad-panes.ts`，再执行 node --experimental-vm-modules probe.mjs。探针以给定边界读取当前产品和 paneRecovery，包含新随机输入和已知坏源对照；其中 candidate 字段固定为审查时版本。整套临时原件仍按审查报告里的路径保留，不覆盖。
