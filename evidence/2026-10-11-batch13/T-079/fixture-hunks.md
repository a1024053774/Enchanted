# 旧夹具适配：逐 hunk 说明

批准来源为当前会话 `⟦主控 #5⟧`：“允许修改 acceptance/test_herdr_traceability_e2e.py，但只限两处：1. 让假 Herdr 支持 split --env 和 pane process-info；2. 让 managed_env 改从新的 env 来源读取。业务断言一条都不能改，用 git diff 逐 hunk 说明每处改动。”

夹具候选提交为 `d8446fc982aed0309e7d4892760cbe4e69b694eb`，父提交为 `8ab5177d09dcb25f57a50ad2166dc0006ea99ce3`。该提交不改 launcher。差异见 [fixture-approval-scope01/adaptation.diff](fixture-approval-scope01/adaptation.diff)。

`acceptance/test_herdr_traceability_e2e.py` 共 3 个 hunk，落在批准的两个位置：

1. `@@ -49,10 +49,12 @@`，`setUp` 内的假 Herdr：split 从真实 argv 的 `--env` 读取键值并保存为 JSON；将已不再被生产入口调用的 `pane run export` 夹具换成 `pane process-info`，返回明确的 shell 前台状态。`agent start` 的成功与失败分支保持原文。
2. `@@ -61,7 +63,7 @@`，仍在 `setUp`：将假 Herdr 的环境文件指向 `FAKE_ENV` / `fake-env.json`。只改新数据源的接线，没有改变 task、attempt、session 或任何预期值。
3. `@@ -93,10 +95,8 @@`，`managed_env`：删除对旧 export 命令的 shlex 拆分，读取新 JSON 环境。原生会话 nonce 的生成和返回环境保持原文。

新增测试文件 `acceptance/test_launcher_shell_ready_e2e.py` 只有 1 个 hunk：`@@ -36,12 +36,13 @@`。其 `setUp` 写入同一 JSON 数据源，以配合继承的 `managed_env`。split 的参数键值不变；为了继续验证起点版本，既有的旧 `pane run` 反事实夹具也写入同一 JSON 源。这里没有第二条生产路径，launcher 仍只用 split 环境。

源码逐方法比对见 [fixture-approval-scope01/scope.json](fixture-approval-scope01/scope.json)：旧文件只改 `setUp` 与 `managed_env`；新文件只改 `setUp`。全部 `test_*`、`assert_trailers`、`assert_wait_failure` 及其他业务辅助方法的原文均未改变。此检查只证明修改边界；后续沙箱外复跑取得旧套 7/7、新套 6/6 通过和起点反事实的预期红态，见 [tests 结果](tests-20261011T110739Z-8b3a1a/summary.json)。

重放（输出目录须不存在）：

```sh
python3 -B evidence/2026-10-11-batch13/T-079/inspect-fixture-scope.py /tmp/t079-fixture-scope-new
git diff 8ab5177d09dcb25f57a50ad2166dc0006ea99ce3 d8446fc982aed0309e7d4892760cbe4e69b694eb -- acceptance/test_herdr_traceability_e2e.py acceptance/test_launcher_shell_ready_e2e.py
```
