# T-078 cards host 启动失败诊断与续跑

根因诊断及最小复现／修复检查 **PASS**；完整 cards 和之后未运行的入口仍 **INCOMPLETE**。原 `post-rebase-2-outside-01` 不改、不重试。本轮不改产品源码或卡业务断言，不启动真实 Claude、Electron、后台服务或模型。

## 原始失败发生在夹具 bootstrap

主控 #170 的候选 `3d5225a9689bf04bf839967dc059e0a8e7adc300`：inbox-entry 8/8 PASS、cleanup 完整；随后第六条命令 cards 返回 15 tests、0 failures、15 errors，均在 setUp。前四条命令只是版本／源码前置核对，不是额外业务测试组。

从原 [fixtures.tar.gz](post-rebase-2-outside-01/cards/fixtures.tar.gz) 直接读取全部十五份 host.stderr／host.stdout，原字节另存 [diagnosis](post-rebase-2b-diagnosis/original-host-readback.json)。十五份 stderr 都是：

```text
Error: absolute_operator_credential_path_required
    at credentialPath (.../workbench/src/credentials.ts:9:41)
    at createOperatorCredential (.../workbench/src/credentials.ts:16:16)
    at .../workbench/tests/daemon_acceptance_host.ts:84:1
```

archive 中 readiness 文件为 0，原命令清单里 gate CLI 请求为 0。host 已成功加载 daemon／门禁／受控 runtime 的模块及配置，在 mkdir state 后、调用 serve 前创建 bootstrap 凭据时退出。尚未执行 card_save／create／claim；因此不是 oracle_paths 字段、T-080 卡拒收或 core 业务调用者接口触发的这十五个错误。完整运行时接口是否通过仍由续跑核对，不能从模块加载成功外推。

`credentials.ts` 要求 daemon 启动者明确提供绝对 `A2A_OPERATOR_CREDENTIAL`，不会自动选路径；这是现有安全边界。父夹具 `TaskCardsCLI.setUp` 清掉继承的 A2A 环境；`DaemonCards.setUp` 没有重新提供本夹具路径，却直接启动需要该字段的 daemon_acceptance_host。其它已使用的 `DaemonLifecycle.start_daemon` 在启动 host 前设置每代自己的 operator 路径。缺口在 cards 的生命周期 adapter，产品拒绝缺凭据符合契约。

## 最小信号与修改

[探针](../../../workbench/tests/test_t078_cards_host_bootstrap.py) 调用实际 `DaemonCards.setUp`，只在将启动 host 的 Popen 调用处截获并停止；Git 基线建库仍实际执行。取该调用真正传出的环境，执行 host 同用的生产 `createOperatorCredential`／`readOperatorCredential`，不进入 socket／PTY。两个新根另注入一个外来 A2A 路径／launch，期望清掉继承身份并选择各自的绝对私有路径；独立检查 state 与根绑定、mode 0600、两个路径不同。

迁移前 [red](post-rebase-2b-bootstrap-red/results.json) 2/2 INCOMPLETE、exit1：实际传出 credential_path=null，生产 API 给出与原 host 相同的缺绝对路径错误。迁移后 [green](post-rebase-2b-bootstrap-green/results.json) 同一信号 2/2 PASS、exit0。此探针证明环境接线与真实凭据 API，不声称 host ready、角色转交或 cards 全套通过。

修改仅三行：`DaemonCards.setUp` 建立本 fixture 根下的新 `operator.credential.json` 路径并传入 env；退出经原 CLI daemon_stop、pid 消失与 host.wait 完成后，移除这份自建测试凭据。没有从主控／worker／用户 HOME 复制凭据，没有在产品添加默认路径、fallback、重试或匿名放行。所有原卡、业务测试方法、门禁与 host 保持原样。

重放最小信号：

```sh
python3 -B workbench/tests/test_t078_cards_host_bootstrap.py --output evidence/2026-10-11-batch13/T-078/post-rebase-2b-bootstrap-NEW
```

## 主控冻结与续跑

先按原启动身份运行 [commit-post-rebase-2b.sh](commit-post-rebase-2b.sh)。固定父 HEAD 3d5225a9，提交夹具修复、探针、原失败／凭据红绿、续跑脚本与报告；钩子生成尾注。成功后生成新 `post-rebase-2b-source-freeze.json`，只交接，不启动。

当前 [同一阶段脚本](post-rebase-2-stage.py) 已改为从 cards 续跑，不保留自动选择／回退到旧阶段的分支。旧首次阶段脚本仍在提交 3d5225a9 的 Git 版本及原 argv 中可复核。新阶段先验证原 inbox-entry 8/8 与 cleanup、来源提交；比较该提交到新候选的 product／bin／scripts／acceptance／inbox 测试源码均未改变，才明确复用其 PASS 并记 rerun=false。前置不符合即停，不改成重跑或猜测通过。

沙箱外只运行一次：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/post-rebase-2-stage.py --output /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/post-rebase-2-outside-02
```

实际顺序为 cards15 → 空框 daemon/window/hook17 → Electron/PTY 确定性接收器 runtime12 → input-failures11 → worker-inbox14。cards 成功须原方法全部执行、0 failures/errors/skipped、无后台残留；后续原断言与 setup／cleanup 要求不变，前端仅新建一个构建后复用。模型与供应商 CLI 0。冻结 HEAD／源码／外盘及进程证据、异常停点、超时保留进程且不发信号、不重试、不删 slot 的规则保持。

新阶段及新独立 reviewer 未运行，单角色真实 Claude 入口红态 launch 包仍待这一阶段 PASS 后准备；09B／09C、真实 IME、真登录与整票仍 INCOMPLETE。不要把凭据局部绿态转换成卡业务或实际角色链路 PASS。
