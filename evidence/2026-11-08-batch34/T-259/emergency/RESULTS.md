# T-259 隔离修复候选

当前交付状态：INCOMPLETE。隔离测试通过，尚待独立审查、用户批准安装及正式现场经门禁恢复；没有修改正式数据库、安装应用或重启正式后台。

## 授权与范围

用户本轮批准：“允许一次隔离修复例外（推荐）”。对应问题明确限定：在隔离工作区修复 T-259、准备独立审查，展示候选和证据后再批准安装，随后恢复原门禁继续 T-258 和两个面板；不手改正式数据库、不跳过最终审查。本记录不扩大为其他票的绕门禁授权。

工作区 `/private/tmp/a2a-t259-repair-20261108`；分支 `codex/t259-preparing-reclaim`；父版本 `1013b542377325cc1e37f89bdbf37ceb70b7e0ef`。运行环境为本机 macOS arm64、Node 26.5.0。候选完整版本由包含本报告的提交标识；独立审查与打包记录另绑定完整版本。

目标是恢复原 attempt 的安全回收：真实窗格创建后、初始身份保存前读取失败，留下 runtime_identity=null 的 preparing attempt。只有确认已停止、从未发送或登记任务输入、没有原生会话，且创建、dispatch、shell 与领导进程记录一致时才放行。仍经唯一 reclaim 入口、操作锁及原有停止/归档/清理；确认归档后才释放路径。脏工作区和原失败记录保留。

本票不改变 panes、schema、公开接口、权限、凭据、全局配置或冻结验收。没有调用模型。编译的等待程序只代替 CLI 进程，真实生产 A2AGates、Panes、PTY、SQLite、Git、daemon 与 Unix socket 仍参与。注入点仅是窗格真实创建后的第一次身份读取异常。原现场 JSON 解析异常的具体来源仍未知，本候选不声称修复该瞬时异常或让仍存活的准备会话直接可回收。

## 行为证据

| 证据 | 结论与边界 |
| --- | --- |
| `e2e-parent-03.json` | FAIL，父版本通过真实 CLI/socket 派发、后台正常停止与重启后，仍无法回收已停止准备会话；业务断言 stopped_unsent_preparation_reclaimed 与 old_path_released_after_reclaim 失败，驱动错误为 0。 |
| `e2e-green-03.json` | PASS，9 项：创建后失败、运行中拒收、正常后台停止、重启确认停止、回收、释放旧路径、重复回收、同任务新 attempt、未发送任务输入。 |
| `green-03.json` | PASS，37 个场景、230 项检查；覆盖身份字段、不同 shell/leader、缺失/重复记录、输入发送及未知状态、操作锁、停止/归档失败、重启、重复回收及脏文件保留。 |
| `parent-red-02.json` | FAIL，父版本在相同直接 gate/PTY 场景不能完成回收及后续派发，驱动错误为 0。 |
| `mutant-session-01.json` | FAIL，删掉 session 核对后，外来 session 被误回收；业务检查命中。 |
| `mutant-input-01.json` | FAIL，忽略输入事件后，已有输入意图的会话被误回收；业务检查命中。 |
| `mutant-release-01.json` | FAIL，提前释放路径后，归档失败仍丢失占用；业务检查命中。 |

预期来自 T-259 验收中“原 attempt、未发送、确认停止归档后释放”的条件。新增测试不能作为独立 oracle 自证；父版和三个不同破坏方向的变异验证它们确实能拒绝坏实现。正式场景部署复验仍待执行。

## 无回归与历史失败

`regression-t253-01.json`：原生身份绑定检查通过。`regression-t170-fast-01.json` 与 `regression-t170-hang-01.json`：已有真实 daemon/PTY 启动退出回收、仍存活拒收场景通过。未把全部历史测试或真实模型交付流程宣称为通过；该候选没有修改 dispatch/submit 的正常分支。语法检查和 `git diff --check` 通过。

保留全部探索失败：`red-01.json` 是初次父版红态；`leader-red-01.json` 是首候选遗漏领导进程一致性的反例，修复后纳入 green-03。`e2e-*-01.json`、`e2e-*-02.json` 因测试 host 凭据初始化错误而 INCOMPLETE，不能当成产品红态。最终 03 组已修正驱动并重跑。

`green-01/02` 的业务检查通过，但早期清理遗漏两个本测试专用 hc core；`cleanup-correction-01.json` 记录遗漏，`cleanup-correction-result-01.json` 记录核对精确进程后结束。最终 green-03 及 e2e-03 均在保存状态摘要后清理测试目录和私有进程。用户已有 core 未操作。T-170 夹具清理见 `regression-fixture-cleanup.json`。旧失败证据未覆盖或删除。

## 重放

从候选根目录执行；每次使用新的输出文件名，避免覆盖已有失败。以下 `OUT` 应设为本机新的证据目录。

```sh
export ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/hc-cache
node workbench/tests/test_t259_preparing_reclaim.ts . "$OUT/green.json"
python3 workbench/tests/run_t259_checks.py --revision 1013b542377325cc1e37f89bdbf37ceb70b7e0ef --summary "$OUT/parent.json"
python3 workbench/tests/run_t259_checks.py --mutant skip-session --summary "$OUT/mutant-session.json"
python3 workbench/tests/run_t259_checks.py --mutant ignore-input --summary "$OUT/mutant-input.json"
python3 workbench/tests/run_t259_checks.py --mutant release-before-archive --summary "$OUT/mutant-release.json"
python3 workbench/tests/test_t259_preparing_reclaim_e2e.py --summary "$OUT/e2e-green.json"
python3 workbench/tests/test_t259_preparing_reclaim_e2e.py --revision 1013b542377325cc1e37f89bdbf37ceb70b7e0ef --summary "$OUT/e2e-parent.json"
python3 workbench/tests/test_t253_native_bind.py --summary "$OUT/t253.json"
python3 workbench/tests/test_t170_failed_launch_reclaim_e2e.py --claude /usr/bin/false --scenario fast --summary "$OUT/t170-fast.json"
python3 workbench/tests/test_t170_failed_launch_reclaim_e2e.py --claude /usr/bin/false --scenario hang --summary "$OUT/t170-hang.json"
```

父版及变异预期退出 1；候选与回归预期退出 0。T-170 的 `/usr/bin/false` 仅填入未使用的 Claude 配置，不启动 Claude。T-259 驱动自动清理自身夹具；旧 T-170 驱动须在读取摘要、确认服务与私有 core 已结束后另记录目录大小并清理。

Works：隔离后台入口验证了原 attempt 的安全回收与重新派发，并以父版、变异判红。

No regression：T-253、T-170 两种真实生命周期回归通过；尚未完成正式安装、模型交付及主线两个面板验收。

Risk / undo：仍活着、缺证据或有输入的准备会话继续拒收；原 JSON 异常可能再次出现。安装前可直接弃用隔离候选；安装后按保留的旧应用回退，已追加的恢复记录不删，不手动回滚正式数据库。
