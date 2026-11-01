# 第三轮迁移与 hc 复跑只读验收

状态：PASS，仅限第三轮授权的迁移与 hc 复跑子范围。

候选：`9c0e262125edb75ed841609472e32c952adc2bbd` 加 [round3-candidate.patch](round3-candidate.patch)。本次为新的只读行为验收上下文，不是 agy 独立审查；没有修改文件、分支或外部状态。

## 证据

- 审查前后重新生成受控文件与两个未跟踪测试的完整差异，均逐字等于冻结 patch；project-map 为 0 problems、0 stale living docs。
- 对照迁移前现场，`shellInput`、`terminalTurn`、`dispatch`、`wakeThread`、`drain`、daemon 的 `terminal_hook` 块及终端资源均未变；两个未跟踪测试也未变。
- 项目终端经 `hc.run`、`attachShell` 创建与重接，写入经 hc attach DATA 通道；没有接入 `terminal.send`，没有恢复 node-pty 的 shell 路径。
- 两条路由与处理人场景分别通过 3、3、5 项；原 T-216、T-124、T-132、T-171 分别通过 15、26、6、11 项。
- 独立读取保留现场 SQLite、私有 hc 的 `terminals.json` 和 Claude 原生 JSONL，核对 hc terminal label、shell launch/pid、`shell_native_session`、获批角色的 native session、dispatch、`turn_start_signal.prompt_id` 和原生 root-user 消息行能关联。原生完整记录重新逐行计数：online A=1/B=0，offline A=1，processor A=1。
- T-212 指定的真实 Electron、尺寸不匹配场景 7 项通过，包括 Electron/hc 历史逐行一致、进程存活及用户 core 前后不变。
- 各次运行的 `.hc.json` 或 `.hc-recovered.json` 记录独立的 `enchanted-*` session、私有 socket 与 `stopped:true`；补采只读原现场，最初采集失败记录仍保留。

## 发现

本轮迁移子范围内未发现已证实的可达违约。证据支持原候选迁到新基线后，Claude 项目主控仍能在私有 hc 托管的项目终端中通过所列场景。

## 反例

[round3-duplicate-01.json](round3-duplicate-01.json) 中，完整原生 transcript 有两条独立 root-user 提交，队列登记仍为 1。`cli_actual_submission_count_is_one` 因实际计数失败，退出 1。原始摘要的 INCOMPLETE 保留，结论是“预期拒绝成功”，不能把它描述成业务正例 PASS。

## 限制

- 延期 P1 仍在：`terminalCli.ts` 只为 Claude/Codex 提供角色申请的 native session，`controllerThreads` 要求该 session 与 `nativeReport` 一致；hc shell 的 OSC 处理只更新 `cliTurn`。承载切换没有解除 agy/opencode 的静态收件阻断。
- Claude 使用真实原生交互 CLI，模型端是本地脚本化接口，供应商调用为 0；没有证明模型自主判断或供应商稳定性。
- 审查者没有重跑长测试，也没有调用 agy/opencode。本审查不替代 agy 审查，不构成 T-216 全票或发布 PASS。
