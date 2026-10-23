# T-143 CDP 工具修复独立只读审查

状态：**INCOMPLETE**。
冻结候选：3598eac5d17bfb8ce9ce543505ceade7a0ddfd10。
来源：新鲜只读会话 `/root/t143_serialization_review`；候选和工作区在审查期间保持不变。

本次只审查相对 39a11fd6038413302568471b9f1254deecb8b9b6 的联合 e2e、RUN-OUTSIDE-03.sh 与 CHECK-CDP-SERIALIZATION.mjs。
限定范围未发现已复现的可达缺陷。

- 独立运行 CHECK-CDP-SERIALIZATION.mjs，退出 0。旧表达式循环对象序列化失败；实际修复表达式返回 undefined，同时保留同一对象引用。证据 serialization-review-cdp-01.json。
- 经 Python AST 提取实际滚动表达式并替换 mount，通过 node --check；JSON.stringify 返回字符串，Python json.loads 恢复指标对象。未执行模拟采样。
- Python 编译、zsh -n RUN-OUTSIDE-03.sh、node --check CHECK-CDP-SERIALIZATION.mjs 均通过。
- 使用保留的真实失败摘要，在临时目录执行 RUN-OUTSIDE-03.sh 第 12–29 行。退出 1，PREFLIGHT.json 为 INCOMPLETE，未到达后续退出 77 的继续执行哨兵。证据 serialization-review-preflight-01.json，原目录 /private/tmp/t143-review-preflight-08biiz2n/。
- measurement_version 保持 2，harness_version 为 3。项目地图 0 problems、0 stale docs。

独立隔离检查命令：

```sh
node evidence/2026-10-23-batch23/T-139-T-143/CHECK-CDP-SERIALIZATION.mjs /private/tmp/t143-review-3598eac5d-serialization-20261023.json
```

局限：Node V8 inspector 不能证明真实 Electron 行为。serialization-selftest-01.json 因沙箱 CDP 端口 ECONNREFUSED、metrics 为空；
该次运行发生在修正尚未提交时，其记录的 code_version 仍为 39a11fd6038413302568471b9f1254deecb8b9b6，不是冻结候选的真实通过证据。
冻结候选尚无一次真实 Electron 非空指标，未启动全部批次，不得宣称性能或整体通过。
